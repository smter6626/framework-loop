"""F1 Reviewer-verdict correction and explicit final-result tests."""

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import test_evidence_summary as p63_tests
import test_run_mutation_loop as legacy


M = legacy.MODULE
SimulatedCrash = legacy.SimulatedCrash


class VerdictCorrectionTests(unittest.TestCase):
    make_legacy_fixture = legacy.MutationLoopTests.make_fixture

    def runtime_fixture(self, root, *, run_id="f1-correction"):
        args, target, _, paths = self.make_legacy_fixture(root, run_id=run_id)
        args.enable_runtime_transition = True
        machine = {
            "schema_version": 1,
            "workload_id": args.workload_id,
            "transition_mode": "reviewer_accept_once",
            "active_step": {"id": "S1", "status": "ACTIVE"},
            "last_transition_id": None,
        }
        args.workload_static.write_text(
            "# F1 fixture\nHuman authorizes one orchestrator transition.\n",
            encoding="utf-8",
        )
        args.workload_runtime.write_bytes(
            b"# F1 Runtime\n"
            + M.RUNTIME_STATE_BEGIN
            + b"\n"
            + json.dumps(machine).encode("utf-8")
            + b"\n"
            + M.RUNTIME_STATE_END
            + b"\n"
        )
        target, governance = M.validate_preflight(args)
        return args, target, governance, paths

    def evidence_fixture(self, root, *, run_id, runtime_transition=True):
        helper = p63_tests.EvidenceSummaryTests(
            methodName="test_default_raw_root_is_ignored_and_explicit_root_remains_supported"
        )
        return helper.fixture(
            root, run_id=run_id, runtime_transition=runtime_transition
        )

    def run_loop(self, args, *, environment=None, observer=None):
        target, governance = M.validate_preflight(args)
        output = io.StringIO()
        with patch.dict(os.environ, environment or {}, clear=False), redirect_stdout(output):
            result = M.orchestrate(
                args=args,
                target_initial=target,
                governance_initial=governance,
                checkpoint_observer=observer,
            )
        self.output = output.getvalue()
        return result

    def checkpoint(self, args):
        return M.CheckpointStore(M.checkpoint_path_for_args(args)).load()

    def correction_override(self, root, attempt, value):
        path = root / f"correction-{attempt}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return {f"P6_TEST_CORRECTION_OVERRIDE_{attempt}": str(path)}

    def parsed_final_result(self, output):
        lines = output.splitlines()
        index = len(lines) - 1 - lines[::-1].index("FINAL_RESULT")
        block = lines[index:]
        self.assertEqual(len(block), 1 + len(M.FINAL_RESULT_FIELDS))
        parsed = {}
        for expected, line in zip(M.FINAL_RESULT_FIELDS, block[1:]):
            key, encoded = line.split("=", 1)
            self.assertEqual(key, expected)
            parsed[key] = json.loads(encoded)
        return parsed

    def test_public_result_centrally_escapes_controls_and_bounds_reason(self):
        reasons = (
            "first line\nerror_code=FORGED\nrun_root=/forged",
            "first line\rerror_code=FORGED",
            "first line\r\nlogical_outcome=RUNTIME_TRANSITION_COMMITTED",
            "Unicode 正常，控制字符：\x00\x1b\u2028tail",
            "超长" + ("界" * (M.MAX_PUBLIC_REASON_CHARS + 200)),
        )
        for reason in reasons:
            with self.subTest(reason=reason[:20]):
                raw = {
                    "run_id": "run\nerror_code=FORGED",
                    "logical_outcome": "FAILED_CLOSED\rPUSHED",
                    "exit_code": 1,
                    "runtime_transition": "NOT_APPLIED\x00",
                    "evidence_publication": "FAILED\u2029FORGED",
                    "reason": reason,
                    "error_code": "KNOWN_ERROR\nrun_root=/forged",
                    "run_root": "/real\r\nlogical_outcome=FORGED",
                }
                public = M.public_final_result(raw)
                self.assertEqual(tuple(public), M.FINAL_RESULT_FIELDS)
                self.assertLessEqual(
                    len(public["reason"]), M.MAX_PUBLIC_REASON_CHARS
                )
                for name, value in public.items():
                    if isinstance(value, str):
                        self.assertFalse(any(
                            character in value
                            for character in ("\n", "\r", "\x00", "\x1b", "\u2028", "\u2029")
                        ))
                output = io.StringIO()
                with redirect_stdout(output):
                    M.emit_final_result(raw)
                terminal = self.parsed_final_result(output.getvalue())
                self.assertEqual(terminal, public)
                self.assertEqual(
                    [line.split("=", 1)[0] for line in output.getvalue().splitlines()[1:]],
                    list(M.FINAL_RESULT_FIELDS),
                )
        truncated = M.bounded_public_reason(
            "x" * (M.MAX_PUBLIC_REASON_CHARS + 1), "KNOWN_ERROR"
        )
        self.assertEqual(len(truncated), M.MAX_PUBLIC_REASON_CHARS)
        self.assertTrue(truncated.endswith(M.PUBLIC_REASON_TRUNCATION_MARKER))

    def test_progress_output_is_single_line_for_untrusted_controls(self):
        output = io.StringIO()
        with redirect_stdout(output):
            M.emit_progress(
                "SECRET\nerror_code=FORGED\rrun_root=/forged\x1b[2J"
            )
        self.assertEqual(len(output.getvalue().splitlines()), 1)
        self.assertIn("\\u000a", output.getvalue())
        self.assertIn("\\u000d", output.getvalue())
        self.assertIn("\\u001b", output.getvalue())

    def test_duplicate_json_key_never_echoes_untrusted_key(self):
        key = "SECRET_MARKER\nerror_code=FORGED\nrun_root=/forged"
        payload = json.dumps({key: 1})[:-1] + "," + json.dumps(key) + ":2}"
        with self.assertRaises(M.InvariantViolation) as caught:
            M.strict_json(payload.encode("utf-8"))
        self.assertEqual(str(caught.exception), "invalid JSON: duplicate JSON key")
        self.assertNotIn("SECRET_MARKER", str(caught.exception))
        self.assertNotIn("FORGED", str(caught.exception))

    def test_original_reviewer_prompt_has_exact_noncommit_locator_rules(self):
        prompt = M.reviewer_review_prompt(Path("/tmp/target"), "fixture").decode()
        self.assertIn("Every `file`, `artifact`, or `test` locator", prompt)
        self.assertIn("absolute path to an existing", prompt)
        self.assertIn("shell command, Git-status description, or prose is not a locator", prompt)
        self.assertIn("do not invent `test`/`artifact` evidence", prompt)
        self.assertIn("Independently inspect every ACCEPT evidence entry", prompt)

    def test_corrected_accept_resumes_same_thread_without_executor_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, target, _, _ = self.runtime_fixture(root)
            calls = root / "calls.log"
            before_runtime = args.workload_runtime.read_bytes()
            environment = {
                "P5_TEST_CALL_LOG": str(calls),
                "P5_TEST_SCENARIO": "executor-commit",
                "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                "P6_TEST_VERDICT": "ACCEPT",
            }
            code, run_root = self.run_loop(args, environment=environment)

            self.assertEqual(code, 0)
            call_lines = calls.read_text(encoding="utf-8").splitlines()
            self.assertEqual(call_lines.count("executor"), 1)
            self.assertEqual(call_lines.count("reviewer-correction-1"), 1)
            self.assertNotIn("reviewer-correction-2", call_lines)
            target_after = M.capture_target_state(
                args.target_repo, args.target_branch, require_clean=True
            )
            self.assertNotEqual(target_after.head, target.head)
            runtime = args.workload_runtime.read_bytes()
            self.assertNotEqual(runtime, before_runtime)
            self.assertEqual(runtime.count(b"1PCLOOP_RUNTIME_TRANSITION_RECORD"), 1)

            checkpoint = self.checkpoint(args)
            correction = checkpoint["verdict_correction"]
            self.assertEqual(correction["attempts_started"], 1)
            self.assertEqual(correction["attempts_completed"], 1)
            self.assertEqual(correction["resolution"]["verdict"], "ACCEPT")
            original = correction["original_verdict_reference"]
            corrected = correction["attempts"][0]["turn_reference"]
            self.assertNotEqual(original["final_path"], corrected["final_path"])
            self.assertNotEqual(original["final_sha256"], corrected["final_sha256"])

            manifest = json.loads((run_root / "manifest.json").read_text())
            self.assertEqual(len(manifest["turns"]), 4)
            first_thread = manifest["turns"][0]["created_thread_id"]
            correction_process = manifest["turns"][-1]
            self.assertEqual(correction_process["session_mode"], M.RESUME)
            self.assertEqual(correction_process["resume_target_thread_id"], first_thread)
            self.assertEqual(correction_process["observed_resume_thread_id"], first_thread)
            self.assertTrue(correction_process["resume_relationship_verified"])
            correction_prompt = (
                run_root / correction_process["prompt_path"]
            ).read_text(encoding="utf-8")
            self.assertIn("EVIDENCE_LOCATOR_NOT_ABSOLUTE", correction_prompt)
            self.assertIn('"attempt": 1', correction_prompt)
            self.assertIn('"maximum_attempts": 2', correction_prompt)
            self.assertIn(str(run_root.resolve()), correction_prompt)
            self.assertIn(original["final_sha256"], correction_prompt)
            self.assertIn("full commit object ID", correction_prompt)
            self.assertIn("commands, Git status, and prose are invalid", correction_prompt)
            self.assertNotIn("Reviewer opaque review", correction_prompt)
            self.assertNotIn("Executor opaque receipt", correction_prompt)
            self.assertEqual(
                manifest["final_result"],
                {
                    "error_code": "RUNTIME_TRANSITION_COMMITTED",
                    "evidence_publication": "NOT_ENABLED",
                    "exit_code": 0,
                    "logical_outcome": M.RUNTIME_TRANSITION_COMMITTED,
                    "reason": "one_reviewer_accept_transition_completed",
                    "run_id": args.run_id,
                    "run_root": str(run_root.resolve()),
                    "runtime_transition": "APPLIED",
                },
            )
            terminal = self.parsed_final_result(self.output)
            self.assertEqual(terminal["logical_outcome"], M.RUNTIME_TRANSITION_COMMITTED)
            self.assertEqual(terminal["runtime_transition"], "APPLIED")

    def test_corrected_accept_records_four_summaries_and_one_publication_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, framework, remote, _, baseline, _ = self.evidence_fixture(
                root, run_id="f1-published"
            )
            calls = root / "calls.log"
            code, run_root = self.run_loop(args, environment={
                "P5_TEST_CALL_LOG": str(calls),
                "P5_TEST_SCENARIO": "executor-commit",
                "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                "P6_TEST_VERDICT": "ACCEPT",
            })
            self.assertEqual(code, 0)
            checkpoint = self.checkpoint(args)
            self.assertEqual(checkpoint["state"], M.FRAMEWORK_EVIDENCE_PUSHED)
            self.assertEqual(len(checkpoint["summary_progress"]), 4)
            summary = M.summary_path_for_args(args, args.run_id).read_bytes()
            self.assertEqual(summary.count(M.P63.SUMMARY_BEGIN.encode()), 4)
            self.assertEqual(
                subprocess.check_output(
                    ["git", "rev-list", "--count", f"{baseline}..HEAD"],
                    cwd=framework,
                    text=True,
                ).strip(),
                "1",
            )
            self.assertEqual(
                subprocess.check_output(
                    ["git", "rev-parse", "main"], cwd=remote, text=True
                ).strip(),
                checkpoint["framework_commit_id"],
            )
            self.assertEqual(calls.read_text().splitlines().count("executor"), 1)
            self.assertEqual(checkpoint["final_result"]["evidence_publication"], "PUSHED")
            self.assertEqual(checkpoint["final_result"]["logical_outcome"], M.RUNTIME_TRANSITION_COMMITTED)
            self.assertNotIn("Reviewer opaque", self.output)
            self.assertTrue((run_root / "manifest.json").is_file())

    def test_correction_may_change_accept_to_reject_or_human_gate(self):
        cases = {
            "REJECT": {
                "verdict": "REJECT",
                "next_instruction": "Perform one bounded repair.",
                "runtime_transition": None,
            },
            "HUMAN_GATE": {
                "verdict": "HUMAN_GATE",
                "next_instruction": None,
                "runtime_transition": None,
            },
        }
        for verdict, override in cases.items():
            with self.subTest(verdict=verdict), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _, _, _ = self.runtime_fixture(root, run_id=f"change-{verdict.lower()}")
                before = args.workload_runtime.read_bytes()
                calls = root / "calls.log"
                environment = {
                    "P5_TEST_CALL_LOG": str(calls),
                    "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                    "P6_TEST_VERDICT": "ACCEPT",
                    **self.correction_override(root, 1, override),
                }
                code, _ = self.run_loop(args, environment=environment)
                self.assertEqual(code, 0)
                self.assertEqual(args.workload_runtime.read_bytes(), before)
                checkpoint = self.checkpoint(args)
                self.assertEqual(checkpoint["logical_outcome"]["state"], M.HUMAN_GATE)
                self.assertEqual(
                    checkpoint["verdict_correction"]["resolution"]["verdict"], verdict
                )
                self.assertEqual(calls.read_text().splitlines().count("executor"), 1)
                self.assertFalse(checkpoint["runtime_transition_applied"])

    def test_two_correctable_failures_exhaust_once_and_publish_logical_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, framework, _, _, baseline, _ = self.evidence_fixture(
                root, run_id="f1-exhausted"
            )
            calls = root / "calls.log"
            before = args.workload_runtime.read_bytes()
            code, _ = self.run_loop(args, environment={
                "P5_TEST_CALL_LOG": str(calls),
                "P6_TEST_CORRECTION_BAD_LOCATOR": "1",
                "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                "P6_TEST_VERDICT": "ACCEPT",
            })
            self.assertEqual(code, 1)
            checkpoint = self.checkpoint(args)
            correction = checkpoint["verdict_correction"]
            self.assertEqual(correction["attempts_started"], 2)
            self.assertEqual(correction["attempts_completed"], 2)
            self.assertIsNone(correction["pending"])
            self.assertEqual(
                checkpoint["logical_outcome"]["error_code"],
                M.ControlErrorCode.VERDICT_CORRECTION_EXHAUSTED.value,
            )
            self.assertEqual(checkpoint["logical_outcome"]["state"], M.FAILED_CLOSED)
            self.assertEqual(checkpoint["state"], M.FRAMEWORK_EVIDENCE_PUSHED)
            self.assertFalse(checkpoint["runtime_transition_applied"])
            self.assertEqual(args.workload_runtime.read_bytes(), before)
            lines = calls.read_text().splitlines()
            self.assertEqual(lines.count("executor"), 1)
            self.assertEqual(lines.count("reviewer-correction-1"), 1)
            self.assertEqual(lines.count("reviewer-correction-2"), 1)
            self.assertEqual(len(checkpoint["summary_progress"]), 5)
            self.assertEqual(
                subprocess.check_output(
                    ["git", "rev-list", "--count", f"{baseline}..HEAD"],
                    cwd=framework,
                    text=True,
                ).strip(),
                "1",
            )
            final = checkpoint["final_result"]
            self.assertEqual(final["logical_outcome"], M.FAILED_CLOSED)
            self.assertEqual(final["runtime_transition"], "NOT_APPLIED")
            self.assertEqual(final["evidence_publication"], "PUSHED")
            self.assertEqual(final["exit_code"], 1)

    def test_schema_invalid_correction_is_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, _, _, _ = self.runtime_fixture(root, run_id="schema-invalid")
            calls = root / "calls.log"
            before = args.workload_runtime.read_bytes()
            secret = "SECRET_DUPLICATE_KEY"
            key = secret + "\nerror_code=FORGED\nrun_root=/forged"
            raw = "{" + json.dumps(key) + ":1," + json.dumps(key) + ":2}"
            code, run_root = self.run_loop(args, environment={
                "P5_TEST_CALL_LOG": str(calls),
                "P6_TEST_CORRECTION_RAW_1": raw,
                "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                "P6_TEST_VERDICT": "ACCEPT",
            })
            self.assertEqual(code, 1)
            checkpoint = self.checkpoint(args)
            self.assertEqual(checkpoint["verdict_correction"]["attempts_started"], 1)
            self.assertEqual(checkpoint["verdict_correction"]["attempts_completed"], 0)
            self.assertEqual(
                checkpoint["logical_outcome"]["error_code"],
                M.ControlErrorCode.VERDICT_CORRECTION_PROCESS_FAILED.value,
            )
            self.assertEqual(calls.read_text().splitlines().count("reviewer-correction-1"), 1)
            self.assertNotIn("reviewer-correction-2", calls.read_text())
            self.assertEqual(args.workload_runtime.read_bytes(), before)
            process = json.loads((
                run_root
                / "cycle-01/reviewer-verdict-correction-01/process.json"
            ).read_text())
            self.assertIn("duplicate JSON key", process["failure"])
            self.assertNotIn(secret, process["failure"])
            self.assertNotIn(secret, self.output)
            self.assertNotIn("error_code=FORGED", self.output)

    def test_correction_timeout_is_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, _, _, _ = self.runtime_fixture(root, run_id="correction-timeout")
            calls = root / "calls.log"
            original = M.stream_subprocess

            def deterministic_timeout(**kwargs):
                if "reviewer-verdict-correction" in kwargs["progress_label"]:
                    kwargs["events_path"].write_bytes(b"")
                    kwargs["stderr_path"].write_bytes(b"")
                    return None, b"", b"", "timeout after 10 seconds"
                return original(**kwargs)

            with patch.object(M, "stream_subprocess", side_effect=deterministic_timeout):
                code, _ = self.run_loop(args, environment={
                    "P5_TEST_CALL_LOG": str(calls),
                    "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                    "P6_TEST_VERDICT": "ACCEPT",
                })
            self.assertEqual(code, 1)
            checkpoint = self.checkpoint(args)
            self.assertEqual(checkpoint["verdict_correction"]["attempts_started"], 1)
            self.assertEqual(checkpoint["verdict_correction"]["attempts_completed"], 0)
            self.assertEqual(
                checkpoint["logical_outcome"]["error_code"],
                M.ControlErrorCode.VERDICT_CORRECTION_PROCESS_FAILED.value,
            )
            self.assertNotIn("reviewer-correction-2", calls.read_text())

    def test_correction_process_authority_failures_are_default_deny(self):
        cases = {
            "profile": ("codex_home", "executor"),
            "role": ("role", "executor"),
            "thread": ("thread_id", "wrong-thread"),
            "resume": ("resume_relationship_verified", False),
            "read-only": ("reviewer_target_read_only_verified", False),
        }
        for name, (field, replacement) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _, _, _ = self.runtime_fixture(root, run_id=f"authority-{name}")
                calls = root / "calls.log"
                original = M.invoke_reviewer

                def corrupt(**kwargs):
                    turn = original(**kwargs)
                    if kwargs.get("review") and turn.turn_dir.name.startswith(
                        "reviewer-verdict-correction"
                    ):
                        value = (
                            str(args.executor_home.resolve())
                            if replacement == "executor" and field == "codex_home"
                            else replacement
                        )
                        turn.process[field] = value
                        M.P4.write_json(turn.turn_dir / "process.json", turn.process)
                    return turn

                with patch.object(M, "invoke_reviewer", side_effect=corrupt):
                    code, _ = self.run_loop(args, environment={
                        "P5_TEST_CALL_LOG": str(calls),
                        "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                        "P6_TEST_VERDICT": "ACCEPT",
                    })
                self.assertEqual(code, 1)
                checkpoint = self.checkpoint(args)
                self.assertEqual(checkpoint["verdict_correction"]["attempts_completed"], 1)
                self.assertEqual(calls.read_text().splitlines().count("executor"), 1)
                self.assertNotIn("reviewer-correction-2", calls.read_text())
                self.assertFalse(checkpoint["runtime_transition_applied"])

    def test_target_and_governance_drift_block_correction_before_launch(self):
        for mutation in ("target-head", "target-branch", "target-dirty", "governance", "runtime"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _, _, _ = self.runtime_fixture(root, run_id=f"drift-{mutation}")
                calls = root / "calls.log"
                mutated = False

                def observer(state, _checkpoint):
                    nonlocal mutated
                    if state != M.REVIEW_CORRECTION_PENDING or mutated:
                        return
                    mutated = True
                    if mutation == "target-head":
                        subprocess.run(
                            ["git", "commit", "--allow-empty", "-qm", "external drift"],
                            cwd=args.target_repo,
                            check=True,
                        )
                    elif mutation == "target-branch":
                        subprocess.run(
                            ["git", "switch", "-q", "-c", "external-drift"],
                            cwd=args.target_repo,
                            check=True,
                        )
                    elif mutation == "target-dirty":
                        (args.target_repo / "external-dirty.txt").write_text("dirty\n")
                    elif mutation == "runtime":
                        args.workload_runtime.write_text(
                            args.workload_runtime.read_text() + "external runtime drift\n"
                        )
                    else:
                        args.workload_static.write_text(
                            args.workload_static.read_text() + "external drift\n"
                        )

                code, _ = self.run_loop(args, observer=observer, environment={
                    "P5_TEST_CALL_LOG": str(calls),
                    "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                    "P6_TEST_VERDICT": "ACCEPT",
                })
                self.assertEqual(code, 1)
                self.assertNotIn("reviewer-correction-1", calls.read_text())
                self.assertFalse(self.checkpoint(args)["runtime_transition_applied"])

    def test_correction_checkpoint_corruption_fails_closed_without_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, _, _, _ = self.runtime_fixture(root, run_id="checkpoint-corrupt")
            calls = root / "calls.log"
            crashed = False

            def observer(state, _checkpoint):
                nonlocal crashed
                if state == M.REVIEW_CORRECTION_PENDING and not crashed:
                    crashed = True
                    raise SimulatedCrash()

            environment = {
                "P5_TEST_CALL_LOG": str(calls),
                "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                "P6_TEST_VERDICT": "ACCEPT",
            }
            with self.assertRaises(SimulatedCrash):
                self.run_loop(args, observer=observer, environment=environment)
            checkpoint_path = M.checkpoint_path_for_args(args)
            checkpoint = self.checkpoint(args)
            checkpoint["verdict_correction"]["attempts_started"] = 2
            M.atomic_write_json(checkpoint_path, checkpoint)
            calls_before = calls.read_bytes()
            args.resume = True
            code, _ = self.run_loop(args, environment=environment)
            self.assertEqual(code, 1)
            self.assertEqual(calls.read_bytes(), calls_before)
            self.assertEqual(
                self.checkpoint(args)["logical_outcome"]["error_code"],
                M.ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID.value,
            )

    def test_actual_evidence_byte_drift_blocks_correction_before_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, target, _, _ = self.runtime_fixture(root, run_id="evidence-drift")
            calls = root / "calls.log"
            artifact = args.runs_root / args.run_id / "test-output.log"
            commit_bytes = M.git_bytes(
                args.target_repo, ["cat-file", "commit", target.head]
            )
            override = root / "initial-evidence.json"
            override.write_text(json.dumps({
                "evidence": [
                    {
                        "kind": "commit",
                        "locator": target.head,
                        "sha256": M.P4.sha256_bytes(commit_bytes),
                    },
                    {
                        "kind": "test",
                        "locator": str(artifact.resolve()),
                        "sha256": "0" * 64,
                    },
                ]
            }))
            mutated = False

            def observer(state, _checkpoint):
                nonlocal mutated
                if state == M.PREFLIGHT_PASSED:
                    artifact.write_bytes(b"test PASS\n")
                elif state == M.REVIEW_CORRECTION_PENDING and not mutated:
                    mutated = True
                    artifact.write_bytes(b"externally changed\n")

            code, _ = self.run_loop(args, observer=observer, environment={
                "P5_TEST_CALL_LOG": str(calls),
                "P6_TEST_OVERRIDE": str(override),
                "P6_TEST_VERDICT": "ACCEPT",
            })
            self.assertEqual(code, 1)
            self.assertNotIn("reviewer-correction-1", calls.read_text())
            self.assertFalse(self.checkpoint(args)["runtime_transition_applied"])

    def test_framework_head_mutation_blocks_correction_and_finalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, framework, _, _, _, _ = self.evidence_fixture(
                root, run_id="framework-drift"
            )
            calls = root / "calls.log"
            mutated = False

            def observer(state, _checkpoint):
                nonlocal mutated
                if state == M.REVIEW_CORRECTION_PENDING and not mutated:
                    mutated = True
                    subprocess.run(
                        ["git", "commit", "--allow-empty", "-qm", "external framework drift"],
                        cwd=framework,
                        check=True,
                    )

            code, _ = self.run_loop(args, observer=observer, environment={
                "P5_TEST_CALL_LOG": str(calls),
                "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                "P6_TEST_VERDICT": "ACCEPT",
            })
            self.assertEqual(code, 1)
            self.assertNotIn("reviewer-correction-1", calls.read_text())
            checkpoint = self.checkpoint(args)
            self.assertFalse(checkpoint["runtime_transition_applied"])
            self.assertFalse(checkpoint["framework_evidence_committed"])
            self.assertEqual(checkpoint["final_result"]["evidence_publication"], "FAILED")

    def test_unknown_validation_failure_is_not_correction_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, _, _, _ = self.runtime_fixture(root, run_id="default-deny")
            calls = root / "calls.log"
            secret = "SECRET_INTERNAL_DIAGNOSTIC"
            diagnostic = (
                secret
                + "\nerror_code=FORGED\r\nrun_root=/forged\n"
                + ("x" * (M.MAX_PUBLIC_REASON_CHARS + 100))
            )
            with patch.object(
                M,
                "validate_accept_evidence",
                side_effect=M.InvariantViolation(diagnostic),
            ):
                code, run_root = self.run_loop(args, environment={
                    "P5_TEST_CALL_LOG": str(calls),
                    "P6_TEST_VERDICT": "ACCEPT",
                })
            self.assertEqual(code, 1)
            self.assertNotIn("reviewer-correction", calls.read_text())
            checkpoint = self.checkpoint(args)
            self.assertEqual(
                checkpoint["logical_outcome"]["error_code"],
                M.ControlErrorCode.UNCLASSIFIED_CONTROL_FAILURE.value,
            )
            self.assertEqual(
                checkpoint["logical_outcome"]["reason"],
                M.UNCLASSIFIED_PUBLIC_REASON,
            )
            self.assertIn(
                secret,
                checkpoint["logical_outcome"]["internal_diagnostic"]["reason"],
            )
            manifest = json.loads((run_root / "manifest.json").read_text())
            self.assertEqual(manifest["final_result"], checkpoint["final_result"])
            self.assertEqual(
                manifest["final_result"]["reason"], M.UNCLASSIFIED_PUBLIC_REASON
            )
            self.assertLessEqual(
                len(manifest["final_result"]["reason"]),
                M.MAX_PUBLIC_REASON_CHARS,
            )
            terminal = self.parsed_final_result(self.output)
            self.assertEqual(terminal, checkpoint["final_result"])
            self.assertNotIn(secret, self.output)
            self.assertNotIn("error_code=FORGED", self.output)
            self.assertNotIn("run_root=/forged", self.output)

    def test_correction_pending_and_completed_process_recover_without_duplicate_turns(self):
        for boundary in ("pending", "process-completed"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _, _, _ = self.runtime_fixture(root, run_id=f"recover-{boundary}")
                calls = root / "calls.log"
                crashed = False

                def observer(state, _checkpoint):
                    nonlocal crashed
                    if boundary == "pending" and state == M.REVIEW_CORRECTION_PENDING and not crashed:
                        crashed = True
                        raise SimulatedCrash()

                original = M.invoke_reviewer

                def complete_then_crash(**kwargs):
                    nonlocal crashed
                    turn = original(**kwargs)
                    if (
                        boundary == "process-completed"
                        and kwargs.get("review")
                        and turn.turn_dir.name.startswith("reviewer-verdict-correction")
                        and not crashed
                    ):
                        crashed = True
                        raise SimulatedCrash()
                    return turn

                environment = {
                    "P5_TEST_CALL_LOG": str(calls),
                    "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                    "P6_TEST_VERDICT": "ACCEPT",
                }
                with patch.object(M, "invoke_reviewer", side_effect=complete_then_crash):
                    with self.assertRaises(SimulatedCrash):
                        self.run_loop(args, observer=observer, environment=environment)
                args.resume = True
                code, _ = self.run_loop(args, environment=environment)
                self.assertEqual(code, 0)
                lines = calls.read_text().splitlines()
                self.assertEqual(lines.count("executor"), 1)
                self.assertEqual(lines.count("reviewer-correction-1"), 1)
                self.assertEqual(
                    args.workload_runtime.read_bytes().count(
                        b"1PCLOOP_RUNTIME_TRANSITION_RECORD"
                    ),
                    1,
                )

    def test_summary_written_and_corrected_accept_recover_idempotently(self):
        for boundary in ("summary-written", "corrected-review-completed"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, framework, _, _, baseline, _ = self.evidence_fixture(
                    root, run_id=f"recover-{boundary}"
                )
                calls = root / "calls.log"
                crashed = False

                def observer(state, checkpoint):
                    nonlocal crashed
                    correction = checkpoint.get("verdict_correction") or {}
                    if crashed:
                        return
                    if (
                        boundary == "summary-written"
                        and state == M.REVIEW_CORRECTION_RUNNING
                        and correction.get("attempts_started") == 1
                        and checkpoint.get("summary_pending") is None
                        and len(checkpoint.get("summary_progress", [])) == 4
                    ) or (
                        boundary == "corrected-review-completed"
                        and state == M.REVIEW_COMPLETED
                        and correction.get("attempts_completed") == 1
                    ):
                        crashed = True
                        raise SimulatedCrash()

                environment = {
                    "P5_TEST_CALL_LOG": str(calls),
                    "P5_TEST_SCENARIO": "executor-commit",
                    "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                    "P6_TEST_VERDICT": "ACCEPT",
                }
                with self.assertRaises(SimulatedCrash):
                    self.run_loop(args, observer=observer, environment=environment)
                args.resume = True
                code, _ = self.run_loop(args, environment=environment)
                self.assertEqual(code, 0)
                checkpoint = self.checkpoint(args)
                self.assertEqual(len(checkpoint["summary_progress"]), 4)
                self.assertEqual(calls.read_text().splitlines().count("executor"), 1)
                self.assertEqual(calls.read_text().splitlines().count("reviewer-correction-1"), 1)
                self.assertEqual(
                    args.workload_runtime.read_bytes().count(
                        b"1PCLOOP_RUNTIME_TRANSITION_RECORD"
                    ),
                    1,
                )
                self.assertEqual(
                    subprocess.check_output(
                        ["git", "rev-list", "--count", f"{baseline}..HEAD"],
                        cwd=framework,
                        text=True,
                    ).strip(),
                    "1",
                )

    def test_corrected_accept_runtime_transition_boundaries_are_idempotent(self):
        for boundary in ("pending", "postimage", "committed"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _, _, _ = self.runtime_fixture(
                    root, run_id=f"transition-{boundary}"
                )
                calls = root / "calls.log"
                crashed = False

                def observer(state, _checkpoint):
                    nonlocal crashed
                    expected = {
                        "pending": M.RUNTIME_TRANSITION_PENDING,
                        "postimage": "unused",
                        "committed": M.RUNTIME_TRANSITION_COMMITTED,
                    }[boundary]
                    if state == expected and not crashed:
                        crashed = True
                        raise SimulatedCrash()

                original = M.atomic_replace_runtime

                def replace_then_crash(*arguments):
                    nonlocal crashed
                    original(*arguments)
                    if boundary == "postimage" and not crashed:
                        crashed = True
                        raise SimulatedCrash()

                environment = {
                    "P5_TEST_CALL_LOG": str(calls),
                    "P5_TEST_SCENARIO": "executor-commit",
                    "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                    "P6_TEST_VERDICT": "ACCEPT",
                }
                with patch.object(M, "atomic_replace_runtime", side_effect=replace_then_crash):
                    with self.assertRaises(SimulatedCrash):
                        self.run_loop(args, observer=observer, environment=environment)
                calls_before = calls.read_bytes()
                args.resume = True
                with patch.object(M, "atomic_replace_runtime", wraps=original) as writer:
                    code, _ = self.run_loop(args, environment=environment)
                    self.assertEqual(
                        writer.call_count, 1 if boundary == "pending" else 0
                    )
                self.assertEqual(code, 0)
                self.assertEqual(calls.read_bytes(), calls_before)
                self.assertEqual(calls.read_text().splitlines().count("executor"), 1)
                self.assertEqual(calls.read_text().splitlines().count("reviewer-correction-1"), 1)
                self.assertEqual(
                    args.workload_runtime.read_bytes().count(
                        b"1PCLOOP_RUNTIME_TRANSITION_RECORD"
                    ),
                    1,
                )

    def test_publication_failure_keeps_logical_success_and_resume_only_pushes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, framework, remote, _, _, _ = self.evidence_fixture(
                root, run_id="publication-failure"
            )
            calls = root / "calls.log"
            hook = remote / "hooks/pre-receive"
            hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            hook.chmod(0o755)
            environment = {
                "P5_TEST_CALL_LOG": str(calls),
                "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                "P6_TEST_VERDICT": "ACCEPT",
            }
            code, _ = self.run_loop(args, environment=environment)
            self.assertEqual(code, 1)
            checkpoint = self.checkpoint(args)
            final = checkpoint["final_result"]
            self.assertEqual(final["logical_outcome"], M.RUNTIME_TRANSITION_COMMITTED)
            self.assertEqual(final["runtime_transition"], "APPLIED")
            self.assertEqual(final["evidence_publication"], "FAILED")
            self.assertEqual(final["exit_code"], 1)
            self.assertEqual(final["error_code"], "EVIDENCE_PUBLICATION_FAILED")
            calls_before = calls.read_bytes()
            hook.unlink()
            args.resume = True
            code, _ = self.run_loop(args, environment=environment)
            self.assertEqual(code, 0)
            self.assertEqual(calls.read_bytes(), calls_before)
            self.assertEqual(self.checkpoint(args)["final_result"]["evidence_publication"], "PUSHED")
            self.assertEqual(
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=framework, text=True
                ).strip(),
                self.checkpoint(args)["framework_commit_id"],
            )


if __name__ == "__main__":
    unittest.main()
