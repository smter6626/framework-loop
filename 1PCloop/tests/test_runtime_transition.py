"""P6.2 control tests: fake Codex, real disposable Git, no live workload mutation."""
import copy
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import test_run_mutation_loop as legacy

M = legacy.MODULE
SimulatedCrash = legacy.SimulatedCrash


class RuntimeTransitionTests(unittest.TestCase):
    make_fixture = legacy.MutationLoopTests.make_fixture

    def fixture(self, root):
        args, _, _, paths = self.make_fixture(root, run_id="p62-test")
        args.enable_runtime_transition = True
        machine = {
            "schema_version": 1, "workload_id": args.workload_id,
            "transition_mode": "reviewer_accept_once",
            "active_step": {"id": "S1", "status": "ACTIVE"},
            "last_transition_id": None,
        }
        args.workload_static.write_text(
            "# Disposable contract\nOnly the deterministic orchestrator may complete S1, "
            "after CLI + Runtime capability authorization and independent Reviewer evidence.\n"
        )
        args.workload_runtime.write_bytes(
            b"# Disposable Runtime\nHistorical text stays byte-identical.\n"
            + M.RUNTIME_STATE_BEGIN + b"\n" + json.dumps(machine).encode()
            + b"\n" + M.RUNTIME_STATE_END + b"\nHistorical tail.\n"
        )
        return args, paths

    def run_loop(self, args, *, observer=None, environment=None):
        env = {"P6_TEST_VERDICT": "ACCEPT"}
        env.update(environment or {})
        target, governance = M.validate_preflight(args)
        with patch.dict(os.environ, env), redirect_stdout(io.StringIO()) as output:
            result = M.orchestrate(args=args, target_initial=target,
                                   governance_initial=governance,
                                   checkpoint_observer=observer)
        self.last_output = output.getvalue()
        return result

    def checkpoint(self, args):
        return M.CheckpointStore(M.checkpoint_path_for_args(args)).load()

    def overrides(self, root, value):
        path = root / "override.json"
        path.write_text(json.dumps(value))
        return {"P6_TEST_OVERRIDE": str(path)}

    def assert_failed_unchanged(self, args, before, **kwargs):
        code, _ = self.run_loop(args, **kwargs)
        self.assertEqual(code, 1)
        self.assertEqual(args.workload_runtime.read_bytes(), before)
        self.assertFalse(self.checkpoint(args)["runtime_transition_applied"])

    def test_valid_accept_preserves_history_and_applies_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, paths = self.fixture(root)
            before = {name: path.read_bytes() for name, path in paths.items()}
            code, run_root = self.run_loop(args)
            self.assertEqual(code, 0)
            checkpoint = self.checkpoint(args)
            self.assertEqual(checkpoint["state"], M.RUNTIME_TRANSITION_COMMITTED)
            self.assertTrue(checkpoint["runtime_transition_applied"])
            self.assertFalse(checkpoint["framework_evidence_committed"])
            self.assertFalse(checkpoint["framework_evidence_pushed"])
            runtime = args.workload_runtime.read_bytes()
            old, old_start, old_end = M.runtime_state(before[M.WORKLOAD_RUNTIME])
            new, new_start, new_end = M.runtime_state(runtime)
            self.assertEqual(runtime[:new_start], before[M.WORKLOAD_RUNTIME][:old_start])
            self.assertTrue(runtime[new_end:].startswith(before[M.WORKLOAD_RUNTIME][old_end:]))
            self.assertEqual(new["active_step"], {"id": "S1", "status": "COMPLETED"})
            self.assertEqual(new["transition_mode"], "disabled")
            self.assertEqual(new["last_transition_id"], checkpoint["runtime_transition"]["transition_id"])
            self.assertEqual(runtime.count(b"<!-- 1PCLOOP_RUNTIME_TRANSITION_RECORD -->"), 1)
            self.assertEqual(checkpoint["runtime_transition"]["record"]["old_state"], old)
            for name in M.DOCUMENT_ORDER[:-1]:
                self.assertEqual(paths[name].read_bytes(), before[name])
            manifest = json.loads((run_root / "manifest.json").read_bytes())
            self.assertEqual(len(manifest["turns"]), 3)
            self.assertTrue(M.capture_target_state(args.target_repo, args.target_branch, require_clean=True).clean)
            for turn in manifest["turns"]:
                self.assertIn("--output-schema", turn["command"])
                self.assertEqual(turn["output_schema_sha256"], M.P4.sha256_file(M.schema_path(turn["output_schema"])))
            for turn in manifest["turns"][1:]:
                transport = turn["transport"]
                payload = (run_root / transport["peer_payload_path"]).read_bytes()
                source = (run_root / transport["source_final_message"]).read_bytes()
                self.assertEqual(payload, source)
            args.run_id = "second-run"
            self.assert_failed_unchanged(args, runtime)

    def test_malformed_free_text_and_schema_invalid_verdicts_fail_closed(self):
        samples = ["ACCEPT", "{broken", "{}", '[]', '{"verdict":"ACCEPT"}',
                   '{"schema_version":1,"schema_version":1}', 'NaN']
        for raw in samples:
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as tmp:
                args, _ = self.fixture(Path(tmp))
                self.assert_failed_unchanged(args, args.workload_runtime.read_bytes(),
                                             environment={"P6_TEST_RAW": raw})

    def test_executor_and_instruction_cannot_forge_verdict(self):
        for role in (M.EXECUTOR_RECEIPT, M.REVIEWER_INSTRUCTION):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as tmp:
                args, _ = self.fixture(Path(tmp))
                self.assert_failed_unchanged(args, args.workload_runtime.read_bytes(),
                                             environment={"P6_TEST_INVALID_ROLE": role})

    def test_stale_hashes_step_empty_evidence_and_repair_on_accept_fail_closed(self):
        for mutation in ("target", "runtime", "governance", "step", "empty", "repair", "transition"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, paths = self.fixture(root)
                target, governance = M.validate_preflight(args)
                values = {
                    "target": {"reviewed_target": {"repo": str(target.repo), "branch": target.branch, "head": "0" * 40}},
                    "runtime": {"expected_runtime_sha256": "0" * 64},
                    "governance": {"governance_hashes": {**governance.hashes(), "workload_static_sha256": "0" * 64}},
                    "step": {"active_step_id": "S2"},
                    "empty": {"evidence": []},
                    "repair": {"next_instruction": "repair this"},
                    "transition": {"runtime_transition": {"new_status": "ACTIVE", "next_active_step": None}},
                }
                self.assert_failed_unchanged(args, args.workload_runtime.read_bytes(),
                                             environment=self.overrides(root, values[mutation]))

    def test_missing_unreachable_noncommit_and_revision_expression_evidence(self):
        for kind in ("missing", "unreachable", "blob", "expression"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _ = self.fixture(root)
                tree = M.git_text(args.target_repo, ["rev-parse", "HEAD^{tree}"])
                unreachable = M.git_text(args.target_repo, ["commit-tree", tree, "-m", "unreachable root"])
                blob = M.git_text(args.target_repo, ["rev-parse", "HEAD:README.md"])
                locator = {"missing": "0" * 40, "unreachable": unreachable,
                           "blob": blob, "expression": "HEAD"}[kind]
                evidence = [{"kind": "commit", "locator": locator, "sha256": "0" * 64}]
                self.assert_failed_unchanged(args, args.workload_runtime.read_bytes(),
                                             environment=self.overrides(root, {"evidence": evidence}))

    def commit_evidence(self, args):
        head = M.git_text(args.target_repo, ["rev-parse", "HEAD"])
        return {"kind": "commit", "locator": head,
                "sha256": M.P4.sha256_bytes(M.git_bytes(args.target_repo, ["cat-file", "commit", head]))}

    def test_evidence_boundary_rejects_escape_symlink_relative_missing_and_bad_hash(self):
        for kind in ("outside", "symlink", "relative", "missing", "bad-hash"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _ = self.fixture(root)
                outside = root / "outside.log"
                outside.write_text("evidence")
                if kind == "symlink":
                    locator = args.target_repo / "escape"
                    locator.symlink_to(outside)
                    subprocess.run(["git", "add", "escape"], cwd=args.target_repo, check=True)
                    subprocess.run(["git", "commit", "-qm", "symlink fixture"], cwd=args.target_repo, check=True)
                else:
                    locator = {"outside": outside, "relative": Path("README.md"),
                               "missing": args.target_repo / "missing",
                               "bad-hash": args.target_repo / "README.md"}[kind]
                evidence = [self.commit_evidence(args), {"kind": "artifact", "locator": str(locator), "sha256": "0" * 64}]
                self.assert_failed_unchanged(args, args.workload_runtime.read_bytes(),
                                             environment=self.overrides(root, {"evidence": evidence}))

    def test_target_and_run_file_evidence_with_hashes_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, _ = self.fixture(root)
            # The file is created after run directory creation but before any turn.
            artifact = args.runs_root / args.run_id / "test.log"
            def add_artifact(state, _checkpoint):
                if state == M.PREFLIGHT_PASSED:
                    artifact.write_bytes(b"fixture test PASS\n")
            readme = args.target_repo / "README.md"
            evidence = [self.commit_evidence(args),
                        {"kind": "file", "locator": str(readme.resolve()), "sha256": M.P4.sha256_file(readme)},
                        {"kind": "test", "locator": str(artifact.resolve()), "sha256": M.P4.sha256_bytes(b"fixture test PASS\n")}]
            code, _ = self.run_loop(args, observer=add_artifact,
                                    environment=self.overrides(root, {"evidence": evidence}))
            self.assertEqual(code, 0)
            self.assertEqual(self.checkpoint(args)["runtime_transition"]["record"]["evidence"], evidence)

    def test_reject_and_human_gate_never_change_runtime(self):
        for verdict in ("REJECT", "HUMAN_GATE"):
            with self.subTest(verdict=verdict), tempfile.TemporaryDirectory() as tmp:
                args, _ = self.fixture(Path(tmp))
                before = args.workload_runtime.read_bytes()
                code, _ = self.run_loop(args, environment={"P6_TEST_VERDICT": verdict})
                self.assertEqual(code, 0)
                self.assertEqual(args.workload_runtime.read_bytes(), before)
                self.assertEqual(self.checkpoint(args)["state"], M.HUMAN_GATE)
                if verdict == "HUMAN_GATE":
                    self.assertIn('state="HUMAN_GATE"', self.last_output)
                    self.assertIn('last_activity="logical_outcome@', self.last_output)

    def test_reject_requires_one_bounded_instruction(self):
        for instruction in (None, "", "   ", "x" * 8001):
            with self.subTest(length=len(instruction or "")), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _ = self.fixture(root)
                env = self.overrides(root, {"next_instruction": instruction})
                env["P6_TEST_VERDICT"] = "REJECT"
                self.assert_failed_unchanged(args, args.workload_runtime.read_bytes(), environment=env)

    def test_reject_routes_complete_wrapper_to_next_executor(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, _ = self.fixture(Path(tmp))
            args.max_cycles = 2
            before = args.workload_runtime.read_bytes()
            code, run_root = self.run_loop(args, environment={"P6_TEST_VERDICT": "REJECT", "P5_TEST_SCENARIO": "executor-commit"})
            self.assertEqual(code, 0)
            first_review = (run_root / "cycle-01/reviewer-review/final.txt").read_bytes()
            peer = (run_root / "cycle-02/executor/peer-payload.txt").read_bytes()
            self.assertEqual(peer, first_review)
            self.assertEqual(json.loads(peer)["verdict"], "REJECT")
            self.assertEqual(args.workload_runtime.read_bytes(), before)

    def test_cli_and_machine_capabilities_both_required(self):
        for kind in ("cli", "machine", "consumed", "workload"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                args, _ = self.fixture(Path(tmp))
                if kind == "cli":
                    args.enable_runtime_transition = False
                else:
                    content = args.workload_runtime.read_bytes()
                    old, start, end = M.runtime_state(content)
                    if kind == "machine": old["transition_mode"] = "disabled"
                    if kind == "consumed": old["last_transition_id"] = "previous"
                    if kind == "workload": old["workload_id"] = "different"
                    args.workload_runtime.write_bytes(content[:start] + json.dumps(old).encode() + content[end:])
                self.assert_failed_unchanged(args, args.workload_runtime.read_bytes())

    def test_missing_duplicate_reversed_and_invalid_machine_blocks_fail_closed(self):
        for kind in ("missing", "duplicate", "invalid-json", "reverse", "duplicate-key", "extra-property"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                args, _ = self.fixture(Path(tmp))
                content = args.workload_runtime.read_bytes()
                if kind == "missing": content = b"# Runtime without block\n"
                if kind == "duplicate": content += content
                if kind == "invalid-json": content = content.replace(b'"schema_version": 1', b'invalid')
                if kind == "reverse": content = M.RUNTIME_STATE_END + b"{}" + M.RUNTIME_STATE_BEGIN
                if kind == "duplicate-key": content = content.replace(b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1')
                if kind == "extra-property": content = content.replace(b'"schema_version": 1', b'"schema_version": 1, "override": true')
                args.workload_runtime.write_bytes(content)
                self.assert_failed_unchanged(args, content)

    def test_atomic_replace_failure_leaves_complete_preimage_and_no_temp(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, _ = self.fixture(Path(tmp))
            before = args.workload_runtime.read_bytes()
            original = os.replace
            def fail_runtime(source, destination):
                if Path(destination) == args.workload_runtime.resolve():
                    raise OSError("fixture atomic replace failure")
                return original(source, destination)
            with patch.object(M.os, "replace", side_effect=fail_runtime):
                self.assert_failed_unchanged(args, before)
            self.assertEqual(list(args.workload_runtime.parent.glob(".*.tmp-*")), [])

    def test_restart_pending_after_write_and_committed_are_idempotent(self):
        for boundary in ("pending", "written", "committed"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _ = self.fixture(root)
                before = args.workload_runtime.read_bytes()
                calls = root / "calls.log"
                def crash_checkpoint(state, _checkpoint):
                    if state == {"pending": M.RUNTIME_TRANSITION_PENDING,
                                 "written": "unused", "committed": M.RUNTIME_TRANSITION_COMMITTED}[boundary]:
                        raise SimulatedCrash()
                original = M.atomic_replace_runtime
                def crash_written(*arguments):
                    original(*arguments)
                    if boundary == "written": raise SimulatedCrash()
                with patch.object(M, "atomic_replace_runtime", side_effect=crash_written):
                    with self.assertRaises(SimulatedCrash):
                        self.run_loop(args, observer=crash_checkpoint,
                                      environment={"P5_TEST_CALL_LOG": str(calls)})
                after_crash = args.workload_runtime.read_bytes()
                self.assertEqual(after_crash == before, boundary == "pending")
                calls_before = calls.read_bytes()
                args.resume = True
                with patch.object(M, "atomic_replace_runtime", wraps=original) as writer:
                    code, _ = self.run_loop(args, environment={"P5_TEST_CALL_LOG": str(calls)})
                    self.assertEqual(writer.call_count, 1 if boundary == "pending" else 0)
                self.assertEqual(code, 0)
                self.assertEqual(calls.read_bytes(), calls_before)
                self.assertEqual(args.workload_runtime.read_bytes().count(b"<!-- 1PCLOOP_RUNTIME_TRANSITION_RECORD -->"), 1)
                self.assertEqual(self.checkpoint(args)["state"], M.RUNTIME_TRANSITION_COMMITTED)
                result = args.workload_runtime.read_bytes()
                with patch.object(M, "atomic_replace_runtime") as writer:
                    self.assertEqual(self.run_loop(args)[0], 0)
                    writer.assert_not_called()
                self.assertEqual(args.workload_runtime.read_bytes(), result)

    def test_pending_recovery_rechecks_evidence_and_target(self):
        for mutation in ("target", "evidence", "runtime", "plan"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _ = self.fixture(root)
                def crash(state, _checkpoint):
                    if state == M.RUNTIME_TRANSITION_PENDING: raise SimulatedCrash()
                with self.assertRaises(SimulatedCrash): self.run_loop(args, observer=crash)
                if mutation == "target":
                    M.git_text(args.target_repo, ["commit", "--allow-empty", "-m", "external fixture"])
                elif mutation == "evidence":
                    ref = self.checkpoint(args)["instruction_reference"]
                    (args.runs_root / args.run_id / ref["final_path"]).write_text("ACCEPT")
                elif mutation == "runtime":
                    args.workload_runtime.write_bytes(args.workload_runtime.read_bytes() + b"unknown bytes")
                else:
                    checkpoint = self.checkpoint(args)
                    checkpoint["runtime_transition"]["postimage_sha256"] = "0" * 64
                    M.atomic_write_json(M.checkpoint_path_for_args(args), checkpoint)
                before = args.workload_runtime.read_bytes()
                args.resume = True
                with patch.object(M, "atomic_replace_runtime") as writer:
                    try:
                        code, _ = self.run_loop(args)
                        self.assertEqual(code, 1)
                    except M.InvariantViolation:
                        pass
                    writer.assert_not_called()
                self.assertEqual(args.workload_runtime.read_bytes(), before)

    def test_wrong_profile_role_and_resume_relationship_cannot_authorize(self):
        for mutation in ("profile", "role", "resume", "thread", "schema", "events", "dirty"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _ = self.fixture(root)
                before = args.workload_runtime.read_bytes()
                original = M.invoke_reviewer
                def corrupt(**kwargs):
                    turn = original(**kwargs)
                    if kwargs.get("review"):
                        fields = {
                            "profile": ("codex_home", str(args.executor_home.resolve())),
                            "role": ("role", "executor"), "resume": ("resume_relationship_verified", False),
                            "thread": ("thread_id", "different"), "schema": ("output_schema", M.EXECUTOR_RECEIPT),
                            "dirty": ("reviewer_target_read_only_verified", False),
                            "events": ("exit_code", 9),
                        }
                        key, value = fields[mutation]
                        turn.process[key] = value
                        M.P4.write_json(turn.turn_dir / "process.json", turn.process)
                    return turn
                with patch.object(M, "invoke_reviewer", side_effect=corrupt):
                    self.assert_failed_unchanged(args, before)

    def test_command_schema_is_present_for_fresh_ephemeral_and_resume(self):
        for mode in (M.NEW_PERSISTENT, M.FRESH_EPHEMERAL, M.RESUME):
            command = M.build_codex_command(codex_bin="codex", workspace=Path("/tmp/target"),
                                            final_path=Path("/tmp/final"), session_mode=mode,
                                            resume_target_thread_id="thread" if mode == M.RESUME else None,
                                            output_schema=M.schema_path(M.REVIEWER_VERDICT))
            index = command.index("--output-schema")
            self.assertEqual(command[index + 1], str(M.schema_path(M.REVIEWER_VERDICT)))
            self.assertEqual(command.count("--output-schema"), 1)
            if mode == M.RESUME:
                self.assertLess(index, command.index("resume"))
                self.assertEqual(command[-3:], ["resume", "thread", "-"])
            self.assertEqual("--ephemeral" in command, mode == M.FRESH_EPHEMERAL)

    def test_fresh_review_recovery_requires_complete_persistent_bootstrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, _ = self.fixture(Path(tmp))
            def interrupt_review(state, checkpoint):
                if state == M.REVIEW_PENDING:
                    (Path(checkpoint["run_root"]) / checkpoint["active_turn_relative"]).mkdir()
                    raise SimulatedCrash()
            with self.assertRaises(SimulatedCrash):
                self.run_loop(args, observer=interrupt_review)
            args.resume = True
            code, run_root = self.run_loop(args)
            self.assertEqual(code, 0)
            review = json.loads((run_root / "cycle-01/reviewer-review-attempt-02/process.json").read_bytes())
            self.assertEqual(review["session_mode"], M.NEW_PERSISTENT)
            self.assertEqual(review["authoritative_context"]["freshness_policy"]["injected_files"], list(M.DOCUMENT_ORDER))
            self.assertEqual(self.checkpoint(args)["state"], M.RUNTIME_TRANSITION_COMMITTED)

    def test_pending_file_evidence_mutation_and_invalid_state_fail_closed(self):
        for mutation in ("artifact", "state"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _ = self.fixture(root)
                artifact = args.runs_root / args.run_id / "test.log"
                def checkpoint_hook(state, _checkpoint):
                    if state == M.PREFLIGHT_PASSED: artifact.write_bytes(b"test output\n")
                    if state == M.RUNTIME_TRANSITION_PENDING: raise SimulatedCrash()
                evidence = [self.commit_evidence(args), {
                    "kind": "test", "locator": str(artifact.resolve()),
                    "sha256": M.P4.sha256_bytes(b"test output\n"),
                }]
                with self.assertRaises(SimulatedCrash):
                    self.run_loop(args, observer=checkpoint_hook,
                                  environment=self.overrides(root, {"evidence": evidence}))
                if mutation == "artifact":
                    artifact.write_bytes(b"changed evidence\n")
                else:
                    checkpoint = self.checkpoint(args)
                    checkpoint["last_state_transition"]["from"] = M.EXECUTOR_COMMITTED
                    M.atomic_write_json(M.checkpoint_path_for_args(args), checkpoint)
                before = args.workload_runtime.read_bytes()
                args.resume = True
                with patch.object(M, "atomic_replace_runtime") as writer:
                    try:
                        self.assertEqual(self.run_loop(args)[0], 1)
                    except M.InvariantViolation:
                        pass
                    writer.assert_not_called()
                self.assertEqual(args.workload_runtime.read_bytes(), before)

    def test_io_failure_after_replace_preserves_recoverable_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, _ = self.fixture(Path(tmp))
            original = M.atomic_replace_runtime
            def fail_after_replace(*arguments):
                original(*arguments)
                raise OSError("fixture directory fsync failure after replace")
            with patch.object(M, "atomic_replace_runtime", side_effect=fail_after_replace):
                self.assertEqual(self.run_loop(args)[0], 1)
            self.assertEqual(self.checkpoint(args)["state"], M.RUNTIME_TRANSITION_PENDING)
            postimage = args.workload_runtime.read_bytes()
            args.resume = True
            with patch.object(M, "atomic_replace_runtime") as writer:
                self.assertEqual(self.run_loop(args)[0], 0)
                writer.assert_not_called()
            self.assertEqual(args.workload_runtime.read_bytes(), postimage)

    def test_protected_paths_and_profile_aliases_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, _ = self.fixture(Path(tmp))
            args.workload_runtime = M.DEFAULT_FRAMEWORK_RUNTIME
            with self.assertRaises(M.InvariantViolation): M.validate_preflight(args)
        with tempfile.TemporaryDirectory() as tmp:
            args, _ = self.fixture(Path(tmp))
            args.reviewer_home = args.executor_home
            with self.assertRaisesRegex(M.InvariantViolation, "profiles must be distinct"):
                M.validate_preflight(args)
        with tempfile.TemporaryDirectory() as tmp:
            args, _ = self.fixture(Path(tmp))
            args.reviewer_home = Path.home() / ".codex-B"
            args.executor_home = Path.home() / "allowed-executor-home"
            args.role_runtime_root = Path.home()
            with self.assertRaisesRegex(M.InvariantViolation, "retired account home"):
                M.validate_preflight(args)


if __name__ == "__main__":
    unittest.main()
