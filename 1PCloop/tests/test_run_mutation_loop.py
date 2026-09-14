import argparse
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_mutation_loop.py"
SPEC = importlib.util.spec_from_file_location("run_mutation_loop", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


FAKE_CODEX = r'''#!/usr/bin/env python3
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

args = sys.argv[1:]
prompt = sys.stdin.buffer.read()
output_path = Path(args[args.index("--output-last-message") + 1])
home = Path(os.environ["CODEX_HOME"])
scenario = os.environ.get("P5_TEST_SCENARIO", "no-op")
is_reviewer = home.name == "reviewer-home"
is_executor = home.name == "executor-home"
is_resume = "resume" in args
is_correction = "reviewer-verdict-correction" in str(output_path)
correction_attempt = None
if is_correction:
    correction_attempt = int(output_path.parent.name.rsplit("-", 1)[1])

call_log = os.environ.get("P5_TEST_CALL_LOG")
if call_log:
    label = (
        f"reviewer-correction-{correction_attempt}"
        if is_correction else "reviewer-resume" if is_reviewer and is_resume else (
        "reviewer-new" if is_reviewer else "executor"
        )
    )
    with Path(call_log).open("a", encoding="utf-8") as handle:
        handle.write(label + "\n")

if scenario == "slow":
    print(json.dumps({"type": "turn.started"}), flush=True)
    time.sleep(0.2)

if is_reviewer and scenario == "reviewer-dirty":
    (Path.cwd() / "reviewer-unexpected.txt").write_text("unexpected\n", encoding="utf-8")
if is_executor and scenario == "executor-dirty":
    (Path.cwd() / "executor-uncommitted.txt").write_text("dirty\n", encoding="utf-8")
if is_executor and scenario == "governance-change":
    governance_path = Path(os.environ["P5_TEST_GOVERNANCE_PATH"])
    governance_path.write_bytes(governance_path.read_bytes() + b"changed\n")
if is_executor and scenario == "executor-commit":
    changed_path = Path.cwd() / "executor-change.txt"
    with changed_path.open("a", encoding="utf-8") as handle:
        handle.write("changed\n")
    subprocess.run(["git", "add", "executor-change.txt"], check=True)
    subprocess.run(["git", "commit", "-qm", "executor fixture change"], check=True)

if is_executor:
    final = b"Executor opaque receipt: ACCEPT REJECT READY BLOCKED are just bytes.\n"
elif is_resume:
    final = b"Reviewer opaque review: ACCEPT REJECT READY BLOCKED are not parsed.\n"
else:
    final = b"Reviewer opaque bounded instruction: preserve these bytes exactly.\n"
schema_file = Path(args[args.index("--output-schema") + 1])
message_type = schema_file.name.removesuffix(".schema.json")
wrapper = dict(schema_version=1, message_type=message_type,
               evidence_summary=os.environ.get("P6_TEST_SUMMARY", "Fixture evidence summary"),
               peer_message=final.decode())
if message_type == "reviewer_verdict":
    start = prompt.index(b"--- BEGIN P5 DETERMINISTIC AUTHORITATIVE CONTEXT ---")
    envelope_text = prompt[start:].split(b"\n", 1)[1].decode()
    context, _ = json.JSONDecoder().raw_decode(envelope_text)
    target = context["target"]
    selected = os.environ.get("P6_TEST_VERDICT", "REJECT")
    commit = subprocess.check_output(["git", "cat-file", "commit", target["head"]])
    wrapper.update(
        verdict=selected, active_step_id="S1",
        reviewed_target={key: target[key] for key in ("repo", "branch", "head")},
        governance_hashes=context["current_hashes"],
        expected_runtime_sha256=context["current_hashes"]["workload_runtime_sha256"],
        evidence=[dict(kind="commit", locator=target["head"], sha256=hashlib.sha256(commit).hexdigest())],
        next_instruction="Inspect the bounded task again." if selected == "REJECT" else None,
        runtime_transition=dict(new_status="COMPLETED", next_active_step=None) if selected == "ACCEPT" else None,
    )
    overrides = os.environ.get("P6_TEST_OVERRIDE")
    if overrides:
        wrapper.update(json.loads(Path(overrides).read_text()))
    if not is_correction and os.environ.get("P6_TEST_INITIAL_BAD_LOCATOR"):
        wrapper["evidence"].append(dict(
            kind="test", locator="python -m unittest -v",
            sha256="0" * 64,
        ))
    if is_correction and os.environ.get("P6_TEST_CORRECTION_BAD_LOCATOR"):
        wrapper["evidence"].append(dict(
            kind="artifact", locator="git status reports clean",
            sha256="0" * 64,
        ))
    if is_correction:
        correction_override = os.environ.get(
            f"P6_TEST_CORRECTION_OVERRIDE_{correction_attempt}"
        )
        if correction_override:
            wrapper.update(json.loads(Path(correction_override).read_text()))
if message_type == os.environ.get("P6_TEST_INVALID_ROLE"):
    wrapper["verdict"] = "ACCEPT"
raw = os.environ.get("P6_TEST_RAW")
correction_raw = (
    os.environ.get(f"P6_TEST_CORRECTION_RAW_{correction_attempt}")
    if is_correction else None
)
if (correction_raw or raw) and message_type == "reviewer_verdict":
    output_path.write_bytes((correction_raw or raw).encode())
else:
    output_path.write_bytes((json.dumps(wrapper, ensure_ascii=False, indent=2) + "\n").encode())

if is_resume:
    thread_id = args[args.index("resume") + 1]
elif is_reviewer:
    thread_id = "reviewer-thread-id"
else:
    thread_id = "executor-thread-id"

print(json.dumps({"type": "thread.started", "thread_id": thread_id}))
print(json.dumps({
    "type": "turn.completed",
    "usage": {
        "input_tokens": 20,
        "cached_input_tokens": 5,
        "output_tokens": 4,
        "reasoning_output_tokens": 2
    }
}))
'''


class SimulatedCrash(BaseException):
    pass


class MutationLoopTests(unittest.TestCase):
    def make_fixture(self, root: Path, *, run_id: str = "p5-test"):
        target = root / "target"
        target.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "p5-test"], cwd=target, check=True)
        subprocess.run(
            ["git", "config", "user.name", "P5 Test"], cwd=target, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "p5@example.invalid"],
            cwd=target,
            check=True,
        )
        (target / "README.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=target, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=target, check=True)

        governance_root = root / "governance"
        governance_root.mkdir()
        governance_paths = {}
        for name in MODULE.DOCUMENT_ORDER:
            path = governance_root / f"{name}.md"
            path.write_text(f"# {name}\nfixture contract\n", encoding="utf-8")
            governance_paths[name] = path

        reviewer_home = root / "reviewer-home"
        executor_home = root / "executor-home"
        reviewer_home.mkdir()
        executor_home.mkdir()
        fake_codex = root / "codex"
        fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
        fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IXUSR)

        args = argparse.Namespace(
            codex_bin=str(fake_codex),
            executor_home=executor_home,
            framework_runtime=governance_paths[MODULE.FRAMEWORK_RUNTIME],
            framework_static=governance_paths[MODULE.FRAMEWORK_STATIC],
            max_cycles=1,
            reviewer_home=reviewer_home,
            resume=False,
            run_id=run_id,
            runs_root=root / "runs",
            state_root=root / ".local" / "state",
            target_branch="p5-test",
            target_repo=target,
            timeout_seconds=10,
            progress_interval_seconds=0.05,
            workload_id="fixture-workload",
            workload_runtime=governance_paths[MODULE.WORKLOAD_RUNTIME],
            workload_static=governance_paths[MODULE.WORKLOAD_STATIC],
        )
        target_initial, governance_initial = MODULE.validate_preflight(args)
        return args, target_initial, governance_initial, governance_paths

    def run_fixture(self, root: Path, *, scenario: str = "no-op"):
        args, target, governance, governance_paths = self.make_fixture(root)
        environment = {"P5_TEST_SCENARIO": scenario}
        if scenario == "governance-change":
            environment["P5_TEST_GOVERNANCE_PATH"] = str(
                governance_paths[MODULE.WORKLOAD_RUNTIME]
            )
        with patch.dict(os.environ, environment, clear=False):
            exit_code, run_root = MODULE.orchestrate(
                args=args,
                target_initial=target,
                governance_initial=governance,
            )
        manifest = json.loads((run_root / "manifest.json").read_text(encoding="utf-8"))
        return exit_code, run_root, manifest

    def test_all_session_commands_bypass_approvals_and_sandbox(self):
        for mode, resume_target in (
            (MODULE.NEW_PERSISTENT, None),
            (MODULE.RESUME, "reviewer-thread-id"),
            (MODULE.FRESH_EPHEMERAL, None),
        ):
            command = MODULE.build_codex_command(
                codex_bin="codex",
                workspace=Path("/tmp/target"),
                final_path=Path("/tmp/final.txt"),
                session_mode=mode,
                resume_target_thread_id=resume_target,
            )
            self.assertIn("--dangerously-bypass-approvals-and-sandbox", command)
            self.assertNotIn("--sandbox", command)
            self.assertNotIn("read-only", command)
            self.assertNotIn("workspace-write", command)
        self.assertIn("--ephemeral", MODULE.build_codex_command(
            codex_bin="codex",
            workspace=Path("/tmp/target"),
            final_path=Path("/tmp/final.txt"),
            session_mode=MODULE.FRESH_EPHEMERAL,
            resume_target_thread_id=None,
        ))

    def test_prompts_define_role_boundaries_without_a_filesystem_sandbox(self):
        target = Path("/tmp/target")
        reviewer_prompts = (
            MODULE.reviewer_initial_prompt(target, "p5-test"),
            MODULE.reviewer_review_prompt(target, "p5-test"),
            MODULE.reviewer_refresh_prompt(target, "p5-test"),
        )
        for prompt_bytes in reviewer_prompts:
            prompt = prompt_bytes.decode("utf-8")
            normalized = " ".join(prompt.split())
            self.assertIn("No Codex filesystem sandbox is active", normalized)
            self.assertIn("MUST NOT modify target code", normalized)
            self.assertIn("alter target Git state", normalized)
            self.assertIn("modify framework Static/Runtime", normalized)
            self.assertIn("modify workload Static/Runtime", normalized)
            self.assertIn("audited mechanically", normalized)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _, _, governance, _ = self.make_fixture(root)
            prompt = MODULE.executor_prompt(target, "p5-test", governance).decode(
                "utf-8"
            )
        normalized = " ".join(prompt.split())
        self.assertIn("No Codex filesystem sandbox is active", normalized)
        self.assertIn("Modify ONLY the target repository", normalized)
        self.assertIn("ordinary descendant Git commits", normalized)
        self.assertIn("MUST NOT modify framework Static/Runtime", normalized)
        self.assertIn("MUST NOT modify workload Static/Runtime", normalized)
        self.assertIn("MUST NOT modify unrelated files outside", normalized)
        for forbidden_operation in ("push", "merge", "reset", "clean", "stash"):
            self.assertIn(forbidden_operation, normalized)

    def test_no_op_routes_both_opaque_payloads_before_human_gate(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            exit_code, run_root, manifest = self.run_fixture(Path(temporary_directory))

            self.assertEqual(exit_code, 0)
            self.assertEqual(manifest["status"], "STOPPED_FOR_HUMAN_REVIEW")
            self.assertEqual(manifest["reason"], "target_head_unchanged")
            self.assertEqual(len(manifest["turns"]), 3)
            run_configuration = manifest["run_configuration"]
            self.assertEqual(run_configuration["reviewer_sandbox"], "none")
            self.assertEqual(run_configuration["executor_sandbox"], "none")
            self.assertTrue(
                run_configuration["approvals_and_sandbox_bypassed"]
            )
            roles = [turn["role"] for turn in manifest["turns"]]
            self.assertEqual(roles, ["reviewer", "executor", "reviewer"])
            cycle = manifest["cycles"][0]
            self.assertIsNotNone(cycle["reviewer_review"])
            self.assertEqual(
                manifest["reviewer_state"]["reviewer_thread_id"],
                "reviewer-thread-id",
            )
            self.assertEqual(
                manifest["reviewer_state"]["reviewer_known_target_head"],
                manifest["target"]["initial_target_head"],
            )

            for turn in manifest["turns"]:
                self.assertEqual(turn["sandbox"], "none")
                self.assertTrue(turn["approvals_and_sandbox_bypassed"])
                self.assertEqual(turn["approval_policy"], "bypassed")
                self.assertIn(
                    "--dangerously-bypass-approvals-and-sandbox", turn["command"]
                )
                self.assertNotIn("--sandbox", turn["command"])

            reviewer_thread = manifest["turns"][0]["created_thread_id"]
            resumed = manifest["turns"][2]
            self.assertEqual(resumed["resume_target_thread_id"], reviewer_thread)
            self.assertEqual(resumed["observed_resume_thread_id"], reviewer_thread)
            self.assertTrue(resumed["resume_relationship_verified"])

            for turn in manifest["turns"][1:]:
                transport = turn["transport"]
                payload = (run_root / transport["peer_payload_path"]).read_bytes()
                prompt = (run_root / turn["prompt_path"]).read_bytes()
                offset = transport["prompt_offset"]
                self.assertEqual(prompt[offset : offset + len(payload)], payload)
                self.assertEqual(hashlib.sha256(payload).hexdigest(), transport["sha256"])
                self.assertEqual(len(payload), transport["bytes"])
                self.assertTrue(transport["preserved_verbatim"])

    def test_target_and_governance_violations_still_fail_closed(self):
        cases = (
            ("reviewer-dirty", "Reviewer changed target repository state"),
            ("executor-dirty", "Executor left the target repository working tree dirty"),
            ("governance-change", "protected governance changed during Executor cycle"),
        )
        for scenario, expected_reason in cases:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                exit_code, _, manifest = self.run_fixture(root, scenario=scenario)
                self.assertEqual(exit_code, 1)
                self.assertEqual(manifest["status"], "FAILED_CLOSED")
                self.assertEqual(manifest["reason"], MODULE.UNCLASSIFIED_PUBLIC_REASON)
                self.assertIn(
                    expected_reason,
                    manifest["logical_outcome"]["internal_diagnostic"]["reason"],
                )

    def test_target_head_change_requires_same_thread_metadata_only_refresh(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            args, target_a, governance, _ = self.make_fixture(root)
            state = MODULE.ReviewerState(
                reviewer_thread_id="reviewer-thread-id",
                known_hashes=governance.hashes(),
                cycle_number=1,
                known_target_head=target_a.head,
            )
            (args.target_repo / "next.txt").write_text("next\n", encoding="utf-8")
            subprocess.run(["git", "add", "next.txt"], cwd=args.target_repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "advance fixture"],
                cwd=args.target_repo,
                check=True,
            )
            target_b = MODULE.capture_target_state(
                args.target_repo, args.target_branch, require_clean=True
            )
            freshness = MODULE.instruction_freshness_metadata(
                target=target_b, governance=governance, state=state
            )
            policy = MODULE.choose_freshness_policy(governance, state)

            self.assertTrue(freshness["refresh_required"])
            self.assertTrue(freshness["target_head_changed"])
            self.assertEqual(freshness["triggered_by"], ["target_head"])
            self.assertEqual(policy.session_mode, MODULE.RESUME)
            self.assertEqual(policy.resume_target_thread_id, "reviewer-thread-id")
            self.assertEqual(policy.injection_mode, "resume-unchanged")
            self.assertEqual(policy.injected_files, ())

    def test_checkpoint_atomically_overwrites_one_current_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            path = root / "state" / "checkpoint.json"
            store = MODULE.CheckpointStore(path)

            store.write(MODULE.PREFLIGHT_PASSED, {"run_id": "first"})
            store.write(MODULE.INSTRUCTION_READY, {"run_id": "second"})

            checkpoint = store.load()
            self.assertEqual(checkpoint["state"], MODULE.INSTRUCTION_READY)
            self.assertEqual(checkpoint["run_id"], "second")
            self.assertEqual([item.name for item in path.parent.iterdir()], [
                "checkpoint.json"
            ])

    def test_nonterminal_checkpoint_requires_explicit_resume(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            args, target, governance, _ = self.make_fixture(root)
            crashed = False

            def crash_at_instruction(
                state: str, _checkpoint: object
            ) -> None:
                nonlocal crashed
                if state == MODULE.INSTRUCTION_READY and not crashed:
                    crashed = True
                    raise SimulatedCrash()

            with self.assertRaises(SimulatedCrash):
                MODULE.orchestrate(
                    args=args,
                    target_initial=target,
                    governance_initial=governance,
                    checkpoint_observer=crash_at_instruction,
                )

            current_target, current_governance = MODULE.validate_preflight(args)
            with self.assertRaisesRegex(
                MODULE.InvariantViolation, "incomplete checkpoint exists"
            ):
                MODULE.orchestrate(
                    args=args,
                    target_initial=current_target,
                    governance_initial=current_governance,
                )

            args.resume = True
            exit_code, run_root = MODULE.orchestrate(
                args=args,
                target_initial=current_target,
                governance_initial=current_governance,
            )
            self.assertEqual(exit_code, 0)
            manifest = json.loads(
                (run_root / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["status"], "STOPPED_FOR_HUMAN_REVIEW")
            checkpoint = MODULE.CheckpointStore(
                MODULE.checkpoint_path_for_args(args)
            ).load()
            self.assertEqual(checkpoint["state"], MODULE.HUMAN_GATE)

    def test_restart_after_executor_commit_does_not_run_executor_twice(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            args, target, governance, _ = self.make_fixture(root)
            call_log = root / "calls.log"
            crashed = False

            def crash_after_commit(state: str, _checkpoint: object) -> None:
                nonlocal crashed
                if state == MODULE.EXECUTOR_COMMITTED and not crashed:
                    crashed = True
                    raise SimulatedCrash()

            with patch.dict(
                os.environ,
                {
                    "P5_TEST_SCENARIO": "executor-commit",
                    "P5_TEST_CALL_LOG": str(call_log),
                },
                clear=False,
            ):
                with self.assertRaises(SimulatedCrash):
                    MODULE.orchestrate(
                        args=args,
                        target_initial=target,
                        governance_initial=governance,
                        checkpoint_observer=crash_after_commit,
                    )
                head_after_crash = MODULE.git_text(args.target_repo, ["rev-parse", "HEAD"])
                self.assertNotEqual(head_after_crash, target.head)

                args.resume = True
                current_target, current_governance = MODULE.validate_preflight(args)
                exit_code, run_root = MODULE.orchestrate(
                    args=args,
                    target_initial=current_target,
                    governance_initial=current_governance,
                )

            self.assertEqual(exit_code, 0)
            calls = call_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(calls.count("executor"), 1)
            manifest = json.loads(
                (run_root / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                [turn["role"] for turn in manifest["turns"]],
                ["reviewer", "executor", "reviewer"],
            )
            self.assertEqual(manifest["reason"], "max_cycles_reached")

    def test_restart_before_executor_launch_runs_it_once(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            args, target, governance, _ = self.make_fixture(root)
            call_log = root / "calls.log"
            crashed = False

            def crash_before_executor(state: str, _checkpoint: object) -> None:
                nonlocal crashed
                if state == MODULE.EXECUTOR_RUNNING and not crashed:
                    crashed = True
                    raise SimulatedCrash()

            with patch.dict(
                os.environ, {"P5_TEST_CALL_LOG": str(call_log)}, clear=False
            ):
                with self.assertRaises(SimulatedCrash):
                    MODULE.orchestrate(
                        args=args,
                        target_initial=target,
                        governance_initial=governance,
                        checkpoint_observer=crash_before_executor,
                    )
                self.assertNotIn(
                    "executor", call_log.read_text(encoding="utf-8").splitlines()
                )

                args.resume = True
                current_target, current_governance = MODULE.validate_preflight(args)
                exit_code, _ = MODULE.orchestrate(
                    args=args,
                    target_initial=current_target,
                    governance_initial=current_governance,
                )

            self.assertEqual(exit_code, 0)
            calls = call_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(calls.count("executor"), 1)

    def test_restart_at_review_boundaries_does_not_duplicate_reviewer(self):
        for crash_state in (MODULE.REVIEW_PENDING, MODULE.REVIEW_COMPLETED):
            with self.subTest(crash_state=crash_state), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                args, target, governance, _ = self.make_fixture(root)
                call_log = root / "calls.log"
                crashed = False

                def crash_at_boundary(state: str, _checkpoint: object) -> None:
                    nonlocal crashed
                    if state == crash_state and not crashed:
                        crashed = True
                        raise SimulatedCrash()

                with patch.dict(
                    os.environ, {"P5_TEST_CALL_LOG": str(call_log)}, clear=False
                ):
                    with self.assertRaises(SimulatedCrash):
                        MODULE.orchestrate(
                            args=args,
                            target_initial=target,
                            governance_initial=governance,
                            checkpoint_observer=crash_at_boundary,
                        )
                    calls_before = call_log.read_text(encoding="utf-8").splitlines()
                    args.resume = True
                    current_target, current_governance = MODULE.validate_preflight(args)
                    exit_code, _ = MODULE.orchestrate(
                        args=args,
                        target_initial=current_target,
                        governance_initial=current_governance,
                    )

                self.assertEqual(exit_code, 0)
                calls_after = call_log.read_text(encoding="utf-8").splitlines()
                if crash_state == MODULE.REVIEW_PENDING:
                    self.assertEqual(len(calls_after), len(calls_before) + 1)
                else:
                    self.assertEqual(calls_after, calls_before)
                self.assertEqual(
                    sum(call.startswith("reviewer") for call in calls_after), 2
                )

    def test_ambiguous_commit_after_running_checkpoint_stops_for_human(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            args, target, governance, _ = self.make_fixture(root)
            crashed = False

            def crash_before_executor(state: str, _checkpoint: object) -> None:
                nonlocal crashed
                if state == MODULE.EXECUTOR_RUNNING and not crashed:
                    crashed = True
                    raise SimulatedCrash()

            with self.assertRaises(SimulatedCrash):
                MODULE.orchestrate(
                    args=args,
                    target_initial=target,
                    governance_initial=governance,
                    checkpoint_observer=crash_before_executor,
                )

            (args.target_repo / "ambiguous.txt").write_text(
                "external\n", encoding="utf-8"
            )
            subprocess.run(["git", "add", "ambiguous.txt"], cwd=args.target_repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "ambiguous concurrent commit"],
                cwd=args.target_repo,
                check=True,
            )

            args.resume = True
            current_target, current_governance = MODULE.validate_preflight(args)
            exit_code, run_root = MODULE.orchestrate(
                args=args,
                target_initial=current_target,
                governance_initial=current_governance,
            )
            manifest = json.loads(
                (run_root / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(manifest["status"], "STOPPED_FOR_HUMAN_REVIEW")
            self.assertEqual(
                manifest["reason"], "executor_outcome_ambiguous_after_restart"
            )

    def test_streaming_turn_emits_heartbeat_before_completion(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            args, target, governance, _ = self.make_fixture(root)
            output = io.StringIO()
            with patch.dict(
                os.environ, {"P5_TEST_SCENARIO": "slow"}, clear=False
            ), redirect_stdout(output):
                exit_code, _ = MODULE.orchestrate(
                    args=args,
                    target_initial=target,
                    governance_initial=governance,
                )

            self.assertEqual(exit_code, 0)
            progress = output.getvalue()
            self.assertIn("process_started", progress)
            self.assertIn("running elapsed=", progress)
            self.assertIn("process_finished", progress)
            self.assertIn("checkpoint state=HUMAN_GATE", progress)
            self.assertIn("target_head=", progress)


if __name__ == "__main__":
    unittest.main()
