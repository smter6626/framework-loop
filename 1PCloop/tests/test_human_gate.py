"""F5 pure Human Gate projection and operator integration tests."""

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_operator_cli as operator_tests


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import human_gate as GATE


OP = operator_tests.OP
CLI = operator_tests.CLI
PROJECTION_KEYS = (
    "gate_status",
    "reason_code",
    "allowed_actions",
    "recovery_mode",
)


class HumanGateTests(unittest.TestCase):
    def fixture(self, root: Path, *, run_id: str):
        return operator_tests.OperatorCliTests().fixture(root, run_id=run_id)

    def run_config(self, config, *, environment=None):
        selected = {"P6_TEST_VERDICT": "HUMAN_GATE"}
        selected.update(environment or {})
        with patch.dict(os.environ, selected, clear=False), contextlib.redirect_stdout(
            io.StringIO()
        ):
            return OP.run_mutation(config)

    @staticmethod
    def checkpoint(
        code: str,
        *,
        state: str = "FRAMEWORK_EVIDENCE_PUSHED",
        logical: str = "HUMAN_GATE",
        publication: str = "PUSHED",
    ):
        return {
            "state": state,
            "logical_outcome": {
                "state": logical,
                "error_code": code,
                "reason": "untrusted natural language",
            },
            "final_result": {
                "logical_outcome": logical,
                "runtime_transition": "NOT_APPLIED",
                "evidence_publication": publication,
                "error_code": "EVIDENCE_PUBLICATION_FAILED",
            },
        }

    def project(self, checkpoint, *, identity="VALID", evidence="AVAILABLE"):
        return GATE.project_human_gate(
            checkpoint,
            identity_status=identity,
            evidence_availability=evidence,
            artifact_locators={"checkpoint": "/public/checkpoint.json"},
        )

    def test_human_gate_reason_and_recovery_matrix(self):
        cases = (
            ("REVIEWER_HUMAN_GATE", "ACTIVE", "NEW_RUN_AFTER_REVIEW"),
            ("TARGET_HEAD_UNCHANGED", "ACTIVE", "NEW_RUN_AFTER_REVIEW"),
            ("MAX_CYCLES_REACHED", "ACTIVE", "NEW_RUN_AFTER_REVIEW"),
            (
                "EXECUTOR_OUTCOME_AMBIGUOUS_AFTER_RESTART",
                "ACTIVE",
                "NEW_RUN_AFTER_REVIEW",
            ),
        )
        for code, gate_status, recovery in cases:
            with self.subTest(code=code):
                result = self.project(self.checkpoint(code))
                self.assertEqual(result["gate_status"], gate_status)
                self.assertEqual(result["reason_code"], code)
                self.assertEqual(result["recovery_mode"], recovery)
                self.assertIn(
                    "START_NEW_RUN_AFTER_HUMAN_REVIEW", result["allowed_actions"]
                )
                self.assertNotIn("FINALIZE_EVIDENCE", result["allowed_actions"])

        interrupted = self.project(
            self.checkpoint(
                "UNKNOWN",
                state="RUNTIME_TRANSITION_PENDING",
                logical="UNDETERMINED",
                publication="NOT_STARTED",
            )
        )
        self.assertEqual(interrupted["gate_status"], "ACTIVE")
        self.assertEqual(interrupted["reason_code"], "RUNTIME_TRANSITION_INTERRUPTED")
        self.assertEqual(
            interrupted["recovery_mode"], "HUMAN_REMEDIATION_REQUIRED"
        )
        self.assertNotIn(
            "START_NEW_RUN_AFTER_HUMAN_REVIEW", interrupted["allowed_actions"]
        )

    def test_publication_boundaries_do_not_conflate_logical_success(self):
        pending = self.project(
            self.checkpoint(
                "REVIEWER_HUMAN_GATE",
                state="EVIDENCE_FINALIZATION_PENDING",
                publication="FAILED",
            )
        )
        self.assertEqual(pending["gate_status"], "ACTIVE")
        self.assertEqual(pending["recovery_mode"], "FINALIZATION_ONLY")
        self.assertIn("FINALIZE_EVIDENCE", pending["allowed_actions"])
        self.assertNotIn(
            "START_NEW_RUN_AFTER_HUMAN_REVIEW", pending["allowed_actions"]
        )

        logical_success = self.project(
            self.checkpoint(
                "UNKNOWN",
                state="FRAMEWORK_EVIDENCE_COMMITTED",
                logical="RUNTIME_TRANSITION_COMMITTED",
                publication="COMMITTED",
            )
        )
        self.assertEqual(logical_success["gate_status"], "NOT_APPLICABLE")
        self.assertEqual(logical_success["recovery_mode"], "FINALIZATION_ONLY")
        self.assertEqual(
            logical_success["logical_outcome"], "RUNTIME_TRANSITION_COMMITTED"
        )

        complete_non_gate = self.project(
            self.checkpoint(
                "UNKNOWN",
                logical="RUNTIME_TRANSITION_COMMITTED",
                publication="PUSHED",
            )
        )
        self.assertEqual(complete_non_gate["gate_status"], "NOT_APPLICABLE")
        self.assertEqual(complete_non_gate["recovery_mode"], "NO_ACTION")

    def test_absent_missing_conflicting_and_unknown_default_deny(self):
        absent = self.project(None, evidence="UNAVAILABLE")
        self.assertEqual(absent["gate_status"], "NOT_APPLICABLE")
        self.assertEqual(absent["reason_code"], "NO_CHECKPOINT")

        missing = self.project(
            self.checkpoint("REVIEWER_HUMAN_GATE"), evidence="UNAVAILABLE"
        )
        self.assertEqual(missing["gate_status"], "UNAVAILABLE")
        self.assertEqual(missing["reason_code"], "REQUIRED_EVIDENCE_UNAVAILABLE")
        self.assertNotIn("FINALIZE_EVIDENCE", missing["allowed_actions"])
        self.assertNotIn(
            "START_NEW_RUN_AFTER_HUMAN_REVIEW", missing["allowed_actions"]
        )

        conflict = self.project(
            self.checkpoint("REVIEWER_HUMAN_GATE"), identity="INVALID"
        )
        self.assertEqual(conflict["gate_status"], "INVALID")
        self.assertEqual(conflict["reason_code"], "IDENTITY_CONFLICT")

        unknown = self.project(self.checkpoint("UNRECOGNIZED_REASON"))
        self.assertEqual(unknown["reason_code"], "HUMAN_GATE_REASON_UNAVAILABLE")
        self.assertEqual(
            unknown["recovery_mode"], "HUMAN_REMEDIATION_REQUIRED"
        )
        self.assertNotIn(
            "START_NEW_RUN_AFTER_HUMAN_REVIEW", unknown["allowed_actions"]
        )
        self.assertTrue(
            set(unknown["allowed_actions"]).issubset(GATE.ALLOWED_ACTIONS)
        )

    def test_projection_ignores_private_payload_and_bounds_public_fields(self):
        secret = "SECRET-PEER-PAYLOAD\nerror_code=FORGED\x00"
        value = self.checkpoint("REVIEWER_HUMAN_GATE")
        value["peer_message"] = secret
        value["prompt"] = secret
        value["stderr"] = secret
        value["internal_diagnostic"] = secret
        value["logical_outcome"]["reason"] = secret
        result = GATE.project_human_gate(
            value,
            identity_status="VALID",
            evidence_availability="AVAILABLE",
            artifact_locators={
                "checkpoint": "/public/path\nforged",
                "peer_message": secret,
                "internal_diagnostic": secret,
            },
        )
        encoded = json.dumps(result)
        self.assertNotIn("SECRET", encoded)
        self.assertNotIn("peer_message", encoded)
        self.assertNotIn("internal_diagnostic", encoded)
        self.assertNotIn("\nforged", result["artifacts"]["checkpoint"])
        self.assertLessEqual(len(result["public_reason"]), 512)

    def test_operator_commands_share_projection_and_are_byte_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, _, _, framework, _, _, _, _ = self.fixture(
                root, run_id="gate-read-only"
            )
            config = OP.load_config(config_path)
            code, run_root = self.run_config(config)
            self.assertEqual(code, 0)
            checkpoint_path = OP.checkpoint_path(config)
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            protected = {
                path: path.read_bytes()
                for path in (
                    checkpoint_path,
                    run_root / "manifest.json",
                    run_root / OP.RUNNER.PROGRESS.EVENTS_FILENAME,
                    run_root / OP.RUNNER.PROGRESS.STATUS_FILENAME,
                    Path(config.resolved["evidence"]["summary_root"])
                    / f"{checkpoint['run_id']}.md",
                )
            }
            target = Path(config.resolved["target"]["repo"])
            git_before = {
                repo: subprocess.check_output(
                    ["git", "status", "--porcelain=v1", "--branch"], cwd=repo
                )
                for repo in (framework, target)
            }

            for _ in range(2):
                status = OP.status(config)
                inspect = OP.inspect_run(config)
                human = OP.human_gate_status(config)
                for key in PROJECTION_KEYS:
                    self.assertEqual(status["result"][key], human["result"][key])
                    self.assertEqual(inspect["result"][key], human["result"][key])
                self.assertEqual(inspect["overall_status"], "PASS")
                self.assertEqual(human["result"]["gate_status"], "ACTIVE")
                self.assertEqual(
                    human["result"]["recovery_mode"], "NEW_RUN_AFTER_REVIEW"
                )

            with contextlib.redirect_stdout(io.StringIO()) as output:
                cli_code = CLI.main(["--config", str(config_path), "human-gate"])
            self.assertEqual(cli_code, 0)
            self.assertEqual(len(output.getvalue().splitlines()), 1)
            parsed = json.loads(output.getvalue())
            self.assertEqual(parsed["command"], "human-gate")
            self.assertEqual(parsed["result"]["gate_status"], "ACTIVE")

            for path, content in protected.items():
                self.assertEqual(path.read_bytes(), content)
            for repo, before in git_before.items():
                self.assertEqual(
                    subprocess.check_output(
                        ["git", "status", "--porcelain=v1", "--branch"], cwd=repo
                    ),
                    before,
                )

    def test_missing_raw_and_identity_conflict_are_consistent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, *_ = self.fixture(root, run_id="gate-missing-raw")
            config = OP.load_config(config_path)
            _code, run_root = self.run_config(config)
            checkpoint_path = OP.checkpoint_path(config)
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            first_entry = OP.RUNNER.P63._entry_from_record(
                checkpoint["summary_progress"][0]
            )
            raw_locator = first_entry["raw_artifacts"][0]["locator"]
            Path(raw_locator).unlink()
            results = (
                OP.status(config),
                OP.inspect_run(config),
                OP.human_gate_status(config),
            )
            for result in results:
                self.assertEqual(result["result"]["gate_status"], "UNAVAILABLE")
                self.assertEqual(
                    result["result"]["reason_code"],
                    "REQUIRED_EVIDENCE_UNAVAILABLE",
                )

            checkpoint["configuration"]["operator_config_identity"][
                "raw_sha256"
            ] = "0" * 64
            checkpoint_path.write_text(
                json.dumps(checkpoint, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            results = (
                OP.status(config),
                OP.inspect_run(config),
                OP.human_gate_status(config),
            )
            for result in results:
                self.assertEqual(result["result"]["gate_status"], "INVALID")
                self.assertEqual(result["result"]["reason_code"], "IDENTITY_CONFLICT")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, *_ = self.fixture(root, run_id="gate-evidence-conflict")
            config = OP.load_config(config_path)
            _code, run_root = self.run_config(config)
            manifest_path = run_root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["run_id"] = "conflicting-run"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            results = (
                OP.status(config),
                OP.inspect_run(config),
                OP.human_gate_status(config),
            )
            for result in results:
                self.assertEqual(result["result"]["gate_status"], "INVALID")
                self.assertEqual(result["result"]["reason_code"], "IDENTITY_CONFLICT")

    def test_terminal_gate_resume_only_finalizes_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, _, _, _, remote, _, _, _ = self.fixture(
                root, run_id="gate-finalization"
            )
            config = OP.load_config(config_path)
            hook = remote / "hooks" / "pre-receive"
            hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            hook.chmod(0o755)
            calls = root / "calls.log"
            code, _run_root = self.run_config(
                config, environment={"P5_TEST_CALL_LOG": str(calls)}
            )
            self.assertEqual(code, 1)
            before = calls.read_bytes()
            pending = OP.human_gate_status(config)
            self.assertEqual(pending["result"]["gate_status"], "ACTIVE")
            self.assertEqual(
                pending["result"]["recovery_mode"], "FINALIZATION_ONLY"
            )

            hook.unlink()
            with patch.object(OP.RUNNER, "run_codex_turn") as agent_turn:
                with contextlib.redirect_stdout(io.StringIO()):
                    resumed_code, _ = OP.run_mutation(config, resume=True)
            self.assertEqual(resumed_code, 0)
            self.assertEqual(agent_turn.call_count, 0)
            self.assertEqual(calls.read_bytes(), before)
            completed = OP.human_gate_status(config)
            self.assertEqual(
                completed["result"]["recovery_mode"], "NEW_RUN_AFTER_REVIEW"
            )
            self.assertEqual(
                completed["result"]["evidence_publication"], "PUSHED"
            )


if __name__ == "__main__":
    unittest.main()
