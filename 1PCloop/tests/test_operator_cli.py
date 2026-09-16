"""F3 workload config and unified operator CLI tests."""

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

import test_evidence_summary as evidence


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

OP_SPEC = importlib.util.spec_from_file_location(
    "workload_operator", SCRIPTS / "workload_operator.py"
)
assert OP_SPEC is not None and OP_SPEC.loader is not None
OP = importlib.util.module_from_spec(OP_SPEC)
sys.modules[OP_SPEC.name] = OP
OP_SPEC.loader.exec_module(OP)

CLI_SPEC = importlib.util.spec_from_file_location("onepcloop", SCRIPTS / "onepcloop.py")
assert CLI_SPEC is not None and CLI_SPEC.loader is not None
CLI = importlib.util.module_from_spec(CLI_SPEC)
sys.modules[CLI_SPEC.name] = CLI
CLI_SPEC.loader.exec_module(CLI)


class Crash(BaseException):
    pass


class OperatorCliTests(unittest.TestCase):
    def fixture(self, root: Path, *, run_id: str = "operator-fixture"):
        helper = evidence.EvidenceSummaryTests()
        args, framework, remote, target_remote, baseline, target_remote_head = (
            helper.fixture(root, run_id=run_id)
        )
        config_dir = root / "configuration"
        config_dir.mkdir()
        config_path = config_dir / "workload.json"

        def relative(path):
            return os.path.relpath(str(Path(path)), str(config_dir))

        value = {
            "schema_version": 1,
            "workload_id": args.workload_id,
            "target": {
                "repo": relative(args.target_repo),
                "branch": args.target_branch,
            },
            "governance": {
                "workload_static": relative(args.workload_static),
                "workload_runtime": relative(args.workload_runtime),
                "framework_repo": relative(args.framework_repo),
                "framework_static": relative(args.framework_static),
                "framework_runtime": relative(args.framework_runtime),
            },
            "profiles": {
                "reviewer_home": relative(args.reviewer_home),
                "executor_home": relative(args.executor_home),
            },
            "execution": {
                "codex_bin": relative(args.codex_bin),
                "max_cycles": args.max_cycles,
                "timeout_seconds": args.timeout_seconds,
                "progress_interval_seconds": args.progress_interval_seconds,
                "enable_runtime_transition": args.enable_runtime_transition,
            },
            "evidence": {
                "runs_root": relative(args.runs_root),
                "state_root": relative(args.state_root),
                "summary_root": relative(args.summary_root),
            },
            "framework_git": {
                "branch": args.framework_branch,
                "remote": args.framework_remote,
                "push_ref": args.framework_push_ref,
            },
        }
        self.write_config(config_path, value)
        return config_path, value, args, framework, remote, target_remote, baseline, target_remote_head

    @staticmethod
    def write_config(path: Path, value):
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def read_json(path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def write_json(path: Path, value):
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def run_config(self, config, *, verdict="HUMAN_GATE"):
        with patch.dict(os.environ, {"P6_TEST_VERDICT": verdict}, clear=False), contextlib.redirect_stdout(io.StringIO()):
            return OP.run_mutation(config)

    def test_config_parse_canonical_identity_and_relative_paths_ignore_cwd(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, _, args, *_ = self.fixture(Path(temporary))
            first = OP.load_config(config_path)
            prior = Path.cwd()
            elsewhere = Path(temporary) / "elsewhere"
            elsewhere.mkdir()
            try:
                os.chdir(elsewhere)
                second = OP.load_config(config_path)
            finally:
                os.chdir(prior)
            self.assertEqual(first.identity(), second.identity())
            self.assertEqual(first.resolved["target"]["repo"], str(args.target_repo.resolve()))
            self.assertEqual(len(first.raw_sha256), 64)
            self.assertEqual(len(first.resolved_sha256), 64)

    def test_config_rejects_duplicate_unknown_missing_wrong_version_and_types(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, original, *_ = self.fixture(root)
            invalid_values = []
            unknown = json.loads(json.dumps(original)); unknown["extra"] = True; invalid_values.append(unknown)
            missing = json.loads(json.dumps(original)); del missing["target"]; invalid_values.append(missing)
            version = json.loads(json.dumps(original)); version["schema_version"] = 2; invalid_values.append(version)
            wrong = json.loads(json.dumps(original)); wrong["execution"]["max_cycles"] = True; invalid_values.append(wrong)
            home = json.loads(json.dumps(original)); home["profiles"]["executor_home"] = home["profiles"]["reviewer_home"]; invalid_values.append(home)
            secret = json.loads(json.dumps(original)); secret["token"] = "do-not-store"; invalid_values.append(secret)
            tilde = json.loads(json.dumps(original)); tilde["target"]["repo"] = "~/target"; invalid_values.append(tilde)
            for index, value in enumerate(invalid_values):
                with self.subTest(index=index):
                    self.write_config(config_path, value)
                    with self.assertRaises(OP.OperatorError):
                        OP.load_config(config_path)
            config_path.write_text('{"schema_version":1,"schema_version":1}\n', encoding="utf-8")
            with self.assertRaisesRegex(OP.OperatorError, "duplicate JSON key"):
                OP.load_config(config_path)

    def test_config_does_not_expand_environment_syntax(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, value, *_ = self.fixture(Path(temporary))
            value["target"]["repo"] = "$HOME/target"
            self.write_config(config_path, value)
            loaded = OP.load_config(config_path)
            self.assertIn("$HOME", loaded.resolved["target"]["repo"])

    def test_doctor_all_passes_without_creating_run_or_calling_agent(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, _, args, *_ = self.fixture(Path(temporary))
            call_log = Path(temporary) / "calls.log"
            config = OP.load_config(config_path)
            result = OP.doctor(config)
            self.assertEqual(result["overall_status"], "PASS")
            self.assertTrue(all(item["status"] == "PASS" for item in result["checks"]))
            self.assertFalse(args.runs_root.exists())
            self.assertFalse(args.state_root.exists())
            self.assertFalse(call_log.exists())

    def test_doctor_failure_matrix_is_bounded_and_machine_readable(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, value, *_ = self.fixture(Path(temporary))
            cases = (
                ("codex", lambda v: v["execution"].__setitem__("codex_bin", "missing-codex")),
                ("profiles", lambda v: v["profiles"].__setitem__("reviewer_home", "missing-profile")),
                ("framework_remote", lambda v: v["framework_git"].__setitem__("remote", "missing-remote")),
                ("storage_preflight", lambda v: v["evidence"].__setitem__("runs_root", "../framework/visible-runs")),
            )
            for expected, mutate in cases:
                with self.subTest(check=expected):
                    candidate = json.loads(json.dumps(value)); mutate(candidate)
                    self.write_config(config_path, candidate)
                    result = OP.doctor(OP.load_config(config_path))
                    by_name = {item["name"]: item for item in result["checks"]}
                    self.assertEqual(by_name[expected]["status"], "FAIL")
                    json.dumps(result)

    def test_doctor_dependency_git_and_target_failures_are_explicit(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, value, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            with patch.object(OP.RUNNER, "validate_json_schema", side_effect=OP.RUNNER.InvariantViolation("missing")):
                result = OP.doctor(config)
            self.assertEqual(
                {item["name"]: item for item in result["checks"]}["python_dependencies"]["status"],
                "FAIL",
            )

            real_run = OP.subprocess.run

            def no_git_version(command, *args, **kwargs):
                if list(command) == ["git", "--version"]:
                    return subprocess.CompletedProcess(command, 1, b"", b"")
                return real_run(command, *args, **kwargs)

            with patch.object(OP.subprocess, "run", side_effect=no_git_version):
                result = OP.doctor(config)
            self.assertEqual(
                {item["name"]: item for item in result["checks"]}["git"]["status"],
                "FAIL",
            )

            wrong_branch = json.loads(json.dumps(value))
            wrong_branch["target"]["branch"] = "missing-branch"
            self.write_config(config_path, wrong_branch)
            result = OP.doctor(OP.load_config(config_path))
            self.assertEqual(
                {item["name"]: item for item in result["checks"]}["target"]["status"],
                "FAIL",
            )

    def test_preflight_reuses_runner_without_evidence_side_effects(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, _, args, framework, *_ = self.fixture(Path(temporary))
            baseline = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=framework, text=True).strip()
            result = OP.preflight(OP.load_config(config_path))
            self.assertEqual(result["overall_status"], "PASS")
            self.assertEqual(result["result"]["operator_config_identity"], OP.load_config(config_path).identity())
            self.assertFalse(args.runs_root.exists())
            self.assertFalse(args.state_root.exists())
            self.assertEqual(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=framework, text=True).strip(), baseline)

    def test_config_compiles_to_legacy_runner_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, _, legacy, *_ = self.fixture(Path(temporary), run_id="legacy-equivalence")
            config = OP.load_config(config_path)
            args = OP.build_runner_args(config, run_id=legacy.run_id)
            for name in (
                "codex_bin", "target_branch", "max_cycles", "timeout_seconds",
                "progress_interval_seconds", "workload_id", "framework_branch",
                "framework_remote", "framework_push_ref", "enable_runtime_transition",
            ):
                if name == "codex_bin":
                    self.assertEqual(Path(getattr(args, name)), Path(getattr(legacy, name)).resolve())
                else:
                    self.assertEqual(getattr(args, name), getattr(legacy, name))
            for name in (
                "target_repo", "workload_static", "workload_runtime", "framework_repo",
                "framework_static", "framework_runtime", "reviewer_home", "executor_home",
                "runs_root", "state_root", "summary_root",
            ):
                self.assertEqual(getattr(args, name).resolve(), getattr(legacy, name).resolve())

    def test_run_binds_config_identity_to_checkpoint_and_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            _code, run_root = self.run_config(config)
            checkpoint = self.read_json(OP.checkpoint_path(config))
            manifest = self.read_json(run_root / "manifest.json")
            self.assertEqual(checkpoint["configuration"]["operator_config_identity"], config.identity())
            self.assertEqual(checkpoint["run_configuration"]["operator_config_identity"], config.identity())
            self.assertEqual(manifest["run_configuration"]["operator_config_identity"], config.identity())

    def test_resume_needs_only_config_and_does_not_replay_completed_turn(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            args = OP.build_runner_args(config, run_id="resume-config-only")
            target, governance = OP.RUNNER.validate_preflight(args)
            calls = Path(temporary) / "calls.log"
            crashed = False

            def observer(state, _checkpoint):
                nonlocal crashed
                if not crashed and state == OP.RUNNER.INSTRUCTION_READY:
                    crashed = True
                    raise Crash()

            with patch.dict(os.environ, {"P5_TEST_CALL_LOG": str(calls)}, clear=False), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(Crash):
                    OP.RUNNER.orchestrate(
                        args=args, target_initial=target, governance_initial=governance,
                        checkpoint_observer=observer,
                    )
                resumed = OP.resume_runner_args(config)
                target, governance = OP.RUNNER.validate_preflight(resumed)
                OP.RUNNER.orchestrate(args=resumed, target_initial=target, governance_initial=governance)
            labels = calls.read_text(encoding="utf-8").splitlines()
            self.assertEqual(labels.count("reviewer-new"), 1)
            self.assertEqual(resumed.run_id, "resume-config-only")

    def test_resume_rejects_config_drift_wrong_workload_and_legacy_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, value, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            args = OP.build_runner_args(config, run_id="resume-drift")
            target, governance = OP.RUNNER.validate_preflight(args)
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(Crash):
                    OP.RUNNER.orchestrate(
                        args=args, target_initial=target, governance_initial=governance,
                        checkpoint_observer=lambda state, _: (_ for _ in ()).throw(Crash()) if state == OP.RUNNER.PREFLIGHT_PASSED else None,
                    )
            config_path.write_bytes(config_path.read_bytes() + b" \n")
            with self.assertRaisesRegex(OP.OperatorError, "identity differs"):
                OP.resume_runner_args(OP.load_config(config_path))
            self.write_config(config_path, value)
            restored = OP.load_config(config_path)
            checkpoint = self.read_json(OP.checkpoint_path(restored))
            del checkpoint["configuration"]["operator_config_identity"]
            self.write_json(OP.checkpoint_path(restored), checkpoint)
            with self.assertRaisesRegex(OP.OperatorError, "legacy checkpoint"):
                OP.resume_runner_args(restored)
            wrong = json.loads(json.dumps(value)); wrong["workload_id"] = "other-workload"
            self.write_config(config_path, wrong)
            with self.assertRaisesRegex(OP.OperatorError, "checkpoint is unavailable"):
                OP.resume_runner_args(OP.load_config(config_path))

    def test_status_without_checkpoint_allows_new_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            result = OP.status(OP.load_config(config_path))
            self.assertEqual(result["result"]["safe_next_action"], "START_NEW_RUN_ALLOWED")
            self.assertEqual(result["result"]["observation_availability"], "UNAVAILABLE")

    def test_status_running_correction_human_failed_and_publication_states(self):
        templates = (
            (OP.RUNNER.REVIEW_CORRECTION_PENDING, None, "PENDING", "RESUME_ALLOWED"),
            (OP.RUNNER.HUMAN_GATE, OP.RUNNER.HUMAN_GATE, "NOT_ENABLED", "HUMAN_REVIEW_REQUIRED"),
            (OP.RUNNER.FAILED_CLOSED, OP.RUNNER.FAILED_CLOSED, "NOT_ENABLED", "TERMINAL_FAILURE"),
            (OP.RUNNER.RUNTIME_TRANSITION_COMMITTED, OP.RUNNER.RUNTIME_TRANSITION_COMMITTED, "FAILED", "RESUME_ALLOWED"),
            (OP.RUNNER.FRAMEWORK_EVIDENCE_PUSHED, OP.RUNNER.RUNTIME_TRANSITION_COMMITTED, "PUSHED", "TERMINAL_SUCCESS"),
        )
        for state, outcome, publication, action in templates:
            checkpoint = {
                "state": state,
                "logical_outcome": {"state": outcome} if outcome else None,
                "final_result": {"evidence_publication": publication},
            }
            with self.subTest(state=state, publication=publication):
                self.assertEqual(OP.safe_next_action(checkpoint), action)

    def test_status_projects_terminal_run_and_hides_internal_diagnostic(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            self.run_config(config)
            checkpoint = self.read_json(OP.checkpoint_path(config))
            checkpoint["internal_diagnostic"] = "SECRET-RAW-DIAGNOSTIC"
            self.write_json(OP.checkpoint_path(config), checkpoint)
            result = OP.status(config)
            encoded = json.dumps(result)
            self.assertNotIn("SECRET-RAW-DIAGNOSTIC", encoded)
            self.assertEqual(result["result"]["observation_availability"], "AVAILABLE")
            self.assertEqual(result["result"]["safe_next_action"], "HUMAN_REVIEW_REQUIRED")

    def test_status_integrates_correction_failed_closed_and_publication_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            self.run_config(config)
            path = OP.checkpoint_path(config)
            base = self.read_json(path)
            cases = (
                (OP.RUNNER.REVIEW_CORRECTION_PENDING, None, "PENDING", "RESUME_ALLOWED"),
                (OP.RUNNER.FAILED_CLOSED, OP.RUNNER.FAILED_CLOSED, "NOT_ENABLED", "TERMINAL_FAILURE"),
                (OP.RUNNER.EVIDENCE_FINALIZATION_PENDING, OP.RUNNER.RUNTIME_TRANSITION_COMMITTED, "FAILED", "RESUME_ALLOWED"),
            )
            for state, outcome, publication, expected in cases:
                with self.subTest(state=state):
                    checkpoint = json.loads(json.dumps(base))
                    checkpoint["state"] = state
                    checkpoint["logical_outcome"] = {"state": outcome} if outcome else None
                    checkpoint["final_result"]["logical_outcome"] = outcome or "UNDETERMINED"
                    checkpoint["final_result"]["evidence_publication"] = publication
                    self.write_json(path, checkpoint)
                    result = OP.status(config)
                    self.assertEqual(result["result"]["checkpoint_state"], state)
                    self.assertEqual(result["result"]["safe_next_action"], expected)

    def test_status_reports_observation_unavailable_without_losing_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            _code, run_root = self.run_config(config)
            (run_root / OP.RUNNER.PROGRESS.STATUS_FILENAME).unlink()
            result = OP.status(config)
            self.assertEqual(result["overall_status"], "PASS")
            self.assertEqual(result["result"]["observation_availability"], "UNAVAILABLE")
            self.assertEqual(result["result"]["checkpoint_state"], OP.RUNNER.FRAMEWORK_EVIDENCE_PUSHED)

    def test_inspect_complete_run_validates_all_identities(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            self.run_config(config)
            result = OP.inspect_run(config)
            self.assertEqual(result["overall_status"], "PASS", result)
            self.assertTrue(all(item["status"] == "PASS" for item in result["checks"]))

    def test_inspect_detects_rehashed_event_tamper(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            _code, run_root = self.run_config(config)
            path = run_root / OP.RUNNER.PROGRESS.EVENTS_FILENAME
            events = [json.loads(line) for line in path.read_text().splitlines()]
            event = events[-1]
            event["cycle"] = 999
            unsigned = dict(event); del unsigned["event_id"]
            event["event_id"] = OP.RUNNER.PROGRESS.event_identity(unsigned)
            path.write_text("".join(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n" for item in events), encoding="ascii")
            result = OP.inspect_run(config)
            check = {item["name"]: item for item in result["checks"]}["observation"]
            self.assertEqual(check["status"], "FAIL")
            self.assertEqual(result["overall_status"], "FAIL")

    def test_inspect_incomplete_tail_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            _code, run_root = self.run_config(config)
            path = run_root / OP.RUNNER.PROGRESS.EVENTS_FILENAME
            with path.open("ab") as handle:
                handle.write(b'{"partial":')
            before = path.read_bytes()
            result = OP.inspect_run(config)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(result["overall_status"], "UNAVAILABLE")

    def test_inspect_missing_raw_is_unavailable_not_success_or_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            _code, run_root = self.run_config(config)
            checkpoint = self.read_json(OP.checkpoint_path(config))
            entry = OP.RUNNER.P63._entry_from_record(checkpoint["summary_progress"][0])
            process = Path(next(
                item["locator"] for item in entry["raw_artifacts"]
                if item["name"] == "process.json"
            ))
            process.unlink()
            result = OP.inspect_run(config)
            checks = {item["name"]: item for item in result["checks"]}
            self.assertEqual(checks["summary"]["status"], "UNAVAILABLE")
            self.assertEqual(result["overall_status"], "UNAVAILABLE")

    def test_inspect_detects_summary_identity_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            self.run_config(config)
            checkpoint = self.read_json(OP.checkpoint_path(config))
            summary = Path(config.resolved["evidence"]["summary_root"]) / f"{checkpoint['run_id']}.md"
            summary.write_bytes(summary.read_bytes() + b"tamper\n")
            result = OP.inspect_run(config)
            checks = {item["name"]: item for item in result["checks"]}
            self.assertEqual(checks["summary"]["status"], "FAIL")
            self.assertEqual(result["overall_status"], "FAIL")

    def test_inspect_detects_manifest_and_framework_commit_identity_conflicts(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            _code, run_root = self.run_config(config)
            checkpoint_path = OP.checkpoint_path(config)
            checkpoint = self.read_json(checkpoint_path)
            manifest_path = run_root / "manifest.json"
            manifest = self.read_json(manifest_path)
            original_manifest = json.loads(json.dumps(manifest))
            manifest["run_configuration"]["operator_config_identity"]["raw_sha256"] = "0" * 64
            self.write_json(manifest_path, manifest)
            result = OP.inspect_run(config)
            self.assertEqual(
                {item["name"]: item for item in result["checks"]}["manifest"]["status"],
                "FAIL",
            )
            self.write_json(manifest_path, original_manifest)
            checkpoint["framework_commit_id"] = "0" * 40
            self.write_json(checkpoint_path, checkpoint)
            result = OP.inspect_run(config)
            self.assertEqual(
                {item["name"]: item for item in result["checks"]}["framework_commit"]["status"],
                "FAIL",
            )

    def test_machine_commands_emit_one_parseable_json_object(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, *_ = self.fixture(Path(temporary))
            for command in ("doctor", "preflight", "status", "inspect"):
                with self.subTest(command=command), contextlib.redirect_stdout(io.StringIO()) as output:
                    code = CLI.main(["--config", str(config_path), command])
                parsed = json.loads(output.getvalue())
                self.assertEqual(parsed["command"], command)
                self.assertIn(code, {0, 1})
                self.assertNotIn("PROGRESS", output.getvalue())

    def test_config_error_output_does_not_echo_secret_or_duplicate_key(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.json"
            path.write_text('{"SECRET\\nerror_code=FORGED":1,"SECRET\\nerror_code=FORGED":2}', encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code = CLI.main(["--config", str(path), "doctor"])
            self.assertEqual(code, 2)
            self.assertNotIn("SECRET", output.getvalue())
            self.assertNotIn("FORGED", output.getvalue())
            json.loads(output.getvalue())

    def test_legacy_configuration_has_explicit_null_operator_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, _, legacy, *_ = self.fixture(Path(temporary))
            self.assertFalse(hasattr(legacy, "operator_config_identity"))
            configuration = evidence.M.checkpoint_configuration(legacy)
            self.assertIsNone(configuration["operator_config_identity"])
            old_configuration = dict(configuration)
            del old_configuration["operator_config_identity"]
            self.assertTrue(
                evidence.M.checkpoint_configuration_matches(
                    old_configuration, configuration
                )
            )
            config_backed = dict(configuration)
            config_backed["operator_config_identity"] = {
                "schema_version": 1,
                "config_path": "/config.json",
                "raw_sha256": "0" * 64,
                "resolved_sha256": "1" * 64,
                "workload_id": "fixture-workload",
            }
            self.assertFalse(
                evidence.M.checkpoint_configuration_matches(
                    old_configuration, config_backed
                )
            )

    def test_read_only_commands_do_not_change_repository_or_artifact_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_path, _, _, framework, *_ = self.fixture(Path(temporary))
            config = OP.load_config(config_path)
            self.run_config(config)
            tracked_before = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=framework)
            artifacts = {
                path: path.read_bytes()
                for path in (
                    OP.checkpoint_path(config),
                    Path(OP.load_bound_checkpoint(config)["run_root"]) / "manifest.json",
                    Path(OP.load_bound_checkpoint(config)["run_root"]) / OP.RUNNER.PROGRESS.EVENTS_FILENAME,
                    Path(OP.load_bound_checkpoint(config)["run_root"]) / OP.RUNNER.PROGRESS.STATUS_FILENAME,
                )
            }
            OP.status(config); OP.inspect_run(config)
            self.assertEqual(subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=framework), tracked_before)
            for path, content in artifacts.items():
                self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
