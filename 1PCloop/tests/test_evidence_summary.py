"""P6.3 evidence retention/finalization tests with disposable Git repositories."""

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


class EvidenceSummaryTests(unittest.TestCase):
    make_legacy_fixture = legacy.MutationLoopTests.make_fixture

    def git(self, repo, *arguments):
        return subprocess.check_output(
            ["git", *arguments], cwd=repo, text=True
        ).strip()

    def fixture(self, root, *, run_id="p63-test", runtime_transition=False):
        args, _, _, old_paths = self.make_legacy_fixture(root, run_id=run_id)
        framework = root / "framework"
        framework.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=framework, check=True)
        subprocess.run(["git", "config", "user.name", "P63 Test"], cwd=framework, check=True)
        subprocess.run(
            ["git", "config", "user.email", "p63@example.invalid"],
            cwd=framework,
            check=True,
        )
        (framework / ".gitignore").write_text("1PCloop/.local/\n", encoding="utf-8")
        docs = framework / "1PCloop/docs"
        workload = framework / "1PCloop/workloads/fixture"
        history = framework / "1PCloop/runs"
        docs.mkdir(parents=True)
        workload.mkdir(parents=True)
        history.mkdir(parents=True)
        (docs / "miniloop_static.md").write_bytes(old_paths[M.FRAMEWORK_STATIC].read_bytes())
        (docs / "miniloop_runtime.md").write_bytes(old_paths[M.FRAMEWORK_RUNTIME].read_bytes())
        (workload / "workload_static.md").write_bytes(old_paths[M.WORKLOAD_STATIC].read_bytes())
        (workload / "workload_runtime.md").write_bytes(old_paths[M.WORKLOAD_RUNTIME].read_bytes())
        (history / "historical-evidence.txt").write_text(
            "committed history remains\n", encoding="utf-8"
        )
        if runtime_transition:
            machine = {
                "schema_version": 1,
                "workload_id": "fixture-workload",
                "transition_mode": "reviewer_accept_once",
                "active_step": {"id": "S1", "status": "ACTIVE"},
                "last_transition_id": None,
            }
            (workload / "workload_static.md").write_text(
                "# Fixture Static\nHuman authorizes one orchestrator transition.\n",
                encoding="utf-8",
            )
            (workload / "workload_runtime.md").write_bytes(
                b"# Fixture Runtime\n" + M.RUNTIME_STATE_BEGIN + b"\n"
                + json.dumps(machine).encode("utf-8") + b"\n"
                + M.RUNTIME_STATE_END + b"\n"
            )
        subprocess.run(["git", "add", "--", ".gitignore", "1PCloop"], cwd=framework, check=True)
        subprocess.run(["git", "commit", "-qm", "framework fixture"], cwd=framework, check=True)
        remote = root / "framework-remote.git"
        subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=framework, check=True)
        subprocess.run(["git", "push", "-q", "-u", "origin", "main"], cwd=framework, check=True)

        target_remote = root / "target-remote.git"
        subprocess.run(["git", "init", "-q", "--bare", target_remote], check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", str(target_remote)],
            cwd=args.target_repo,
            check=True,
        )
        subprocess.run(
            ["git", "push", "-q", "-u", "origin", args.target_branch],
            cwd=args.target_repo,
            check=True,
        )

        args.framework_repo = framework
        args.framework_branch = "main"
        args.framework_remote = "origin"
        args.framework_push_ref = "refs/heads/main"
        args.framework_static = docs / "miniloop_static.md"
        args.framework_runtime = docs / "miniloop_runtime.md"
        args.workload_static = workload / "workload_static.md"
        args.workload_runtime = workload / "workload_runtime.md"
        args.runs_root = framework / "1PCloop/.local/runs"
        args.state_root = framework / "1PCloop/.local/state"
        args.summary_root = framework / "1PCloop/evidence-summaries"
        args.enable_runtime_transition = runtime_transition
        baseline = self.git(framework, "rev-parse", "HEAD")
        target_remote_head = self.git(target_remote, "rev-parse", args.target_branch)
        return args, framework, remote, target_remote, baseline, target_remote_head

    def run_loop(self, args, *, environment=None, observer=None):
        target, governance = M.validate_preflight(args)
        with patch.dict(os.environ, environment or {}, clear=False), redirect_stdout(
            io.StringIO()
        ) as output:
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

    def entries(self, checkpoint):
        values = []
        for record in checkpoint["summary_progress"]:
            block = bytes.fromhex(record["entry_hex"])
            body = block.split(b"```json\n", 1)[1].split(b"\n```", 1)[0]
            values.append(json.loads(body))
        return values

    def test_default_raw_root_is_ignored_and_explicit_root_remains_supported(self):
        parsed = M.normalize_cli_args(M.parse_args([
            "--target-repo", "/tmp/target",
            "--target-branch", "fixture",
            "--workload-static", "/tmp/workload-static",
            "--workload-runtime", "/tmp/workload-runtime",
        ]))
        self.assertEqual(parsed.runs_root, M.FRAMEWORK_ROOT / "1PCloop/.local/runs")
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", "--",
             "1PCloop/.local/runs/probe/events.jsonl"],
            cwd=M.FRAMEWORK_ROOT,
            check=False,
        )
        self.assertEqual(ignored.returncode, 0)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, _, _, _, _, _ = self.fixture(root, run_id="explicit-root")
            args.runs_root = root / "explicit-runs"
            code, run_root = self.run_loop(
                args, environment={"P6_TEST_VERDICT": "HUMAN_GATE"}
            )
            self.assertEqual(code, 0)
            self.assertEqual(run_root, (args.runs_root / args.run_id).resolve())

    def test_cli_preflight_uses_injected_framework_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, framework, _, _, baseline, _ = self.fixture(
                Path(tmp), run_id="cli-preflight"
            )
            argv = [
                "--target-repo", str(args.target_repo),
                "--target-branch", args.target_branch,
                "--workload-static", str(args.workload_static),
                "--workload-runtime", str(args.workload_runtime),
                "--framework-repo", str(framework),
                "--framework-branch", "main",
                "--framework-remote", "origin",
                "--framework-push-ref", "refs/heads/main",
                "--framework-static", str(args.framework_static),
                "--framework-runtime", str(args.framework_runtime),
                "--runs-root", str(args.runs_root),
                "--state-root", str(args.state_root),
                "--summary-root", str(args.summary_root),
                "--reviewer-home", str(args.reviewer_home),
                "--executor-home", str(args.executor_home),
                "--codex-bin", args.codex_bin,
                "--run-id", args.run_id,
                "--workload-id", args.workload_id,
                "--preflight-only",
            ]
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(M.main(argv), 0)
            report = json.loads(output.getvalue())
            self.assertEqual(report["evidence_finalization"]["repo"], str(framework.resolve()))
            self.assertEqual(report["evidence_finalization"]["summary_path"], str(M.summary_path_for_args(args, args.run_id)))
            self.assertEqual(self.git(framework, "rev-parse", "HEAD"), baseline)
            self.assertFalse(args.runs_root.exists())

    def test_checkpoint_configuration_binds_summary_and_framework_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, framework, _, _, _, _ = self.fixture(Path(tmp), run_id="bound-config")
            configuration = M.checkpoint_configuration(args)
            self.assertEqual(configuration["framework_repo"], str(framework.resolve()))
            self.assertEqual(configuration["framework_branch"], "main")
            self.assertEqual(configuration["framework_remote"], "origin")
            self.assertEqual(configuration["framework_push_ref"], "refs/heads/main")
            self.assertEqual(
                configuration["evidence_summary"],
                str(M.summary_path_for_args(args, args.run_id)),
            )

    def test_summary_path_cannot_alias_governance(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, _, _, _, _, _ = self.fixture(Path(tmp), run_id="workload_runtime")
            args.summary_root = args.workload_runtime.parent
            with self.assertRaisesRegex(M.InvariantViolation, "distinct from governance"):
                M.validate_preflight(args)

    def test_framework_push_ref_must_match_configured_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, _, _, _, _, _ = self.fixture(Path(tmp), run_id="wrong-ref")
            args.framework_push_ref = "refs/heads/elsewhere"
            with self.assertRaisesRegex(M.InvariantViolation, "configured branch"):
                M.validate_preflight(args)

    def test_old_logical_terminal_cannot_be_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, _, _, _, _, _ = self.fixture(Path(tmp), run_id="old-terminal")
            M.CheckpointStore(M.checkpoint_path_for_args(args)).write(
                M.HUMAN_GATE, {"run_id": "old-run"}
            )
            target, governance = M.validate_preflight(args)
            with self.assertRaisesRegex(M.InvariantViolation, "incomplete checkpoint"):
                M.orchestrate(
                    args=args,
                    target_initial=target,
                    governance_initial=governance,
                )

    def test_terminal_progress_reports_summary_commit_push_without_payload(self):
        special = "SECRET-SUMMARY-CONTENT"
        with tempfile.TemporaryDirectory() as tmp:
            args, _, _, _, _, _ = self.fixture(Path(tmp), run_id="progress-events")
            self.assertEqual(self.run_loop(args, environment={
                "P6_TEST_VERDICT": "HUMAN_GATE",
                "P6_TEST_SUMMARY": special,
            })[0], 0)
            self.assertIn("PROGRESS run=", self.output)
            self.assertIn('state="EVIDENCE_FINALIZATION_PENDING"', self.output)
            self.assertIn('state="FRAMEWORK_EVIDENCE_COMMITTED"', self.output)
            self.assertIn('state="FRAMEWORK_EVIDENCE_PUSHED"', self.output)
            self.assertIn('last_activity="logical_outcome@', self.output)
            self.assertIn('logical_outcome="HUMAN_GATE"', self.output)
            self.assertNotIn(special, self.output)

    def test_raw_manifest_remains_local_and_outside_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, framework, _, _, baseline, _ = self.fixture(
                Path(tmp), run_id="raw-manifest"
            )
            code, run_root = self.run_loop(
                args, environment={"P6_TEST_VERDICT": "HUMAN_GATE"}
            )
            self.assertEqual(code, 0)
            self.assertTrue((run_root / "manifest.json").is_file())
            paths = self.git(
                framework, "diff-tree", "--no-commit-id", "--name-only", "-r",
                f"{baseline}..HEAD",
            ).splitlines()
            self.assertEqual(paths, [f"1PCloop/evidence-summaries/{args.run_id}.md"])

    def test_three_turns_create_three_bounded_entries_and_preserve_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, framework, remote, _, baseline, _ = self.fixture(root)
            historical = framework / "1PCloop/runs/historical-evidence.txt"
            before = historical.read_bytes()
            test_evidence = {
                "kind": "test",
                "locator": str((args.target_repo / "README.md").resolve()),
                "sha256": M.P4.sha256_file(args.target_repo / "README.md"),
            }
            override = root / "summary-override.json"
            override.write_text(json.dumps({"evidence": [test_evidence]}))
            code, run_root = self.run_loop(
                args,
                environment={
                    "P6_TEST_VERDICT": "HUMAN_GATE",
                    "P6_TEST_OVERRIDE": str(override),
                },
            )
            self.assertEqual(code, 0)
            checkpoint = self.checkpoint(args)
            self.assertEqual(checkpoint["state"], M.FRAMEWORK_EVIDENCE_PUSHED)
            entries = self.entries(checkpoint)
            self.assertEqual(len(entries), 3)
            self.assertEqual(
                [entry["role"] for entry in entries],
                ["reviewer", "executor", "reviewer"],
            )
            for entry in entries:
                self.assertRegex(entry["entry_id"], r"^[0-9a-f]{64}$")
                self.assertEqual(entry["llm_evidence_summary"]["text"], "Fixture evidence summary")
                self.assertIsInstance(entry["started_at"], str)
                self.assertIsInstance(entry["finished_at"], str)
                self.assertTrue(entry["governance_hashes"])
                self.assertIsNotNone(entry["target_before"])
                self.assertIsNotNone(entry["target_after"])
                names = {artifact["name"] for artifact in entry["raw_artifacts"]}
                self.assertTrue({"prompt.txt", "events.jsonl", "stderr.txt", "process.json", "final.txt"}.issubset(names))
                for artifact in entry["raw_artifacts"]:
                    self.assertTrue(Path(artifact["locator"]).is_file())
                    self.assertEqual(artifact["sha256"], M.P4.sha256_file(Path(artifact["locator"])))
            self.assertEqual(entries[-1]["tests"], [test_evidence])
            summary = M.summary_path_for_args(args, args.run_id).read_bytes()
            self.assertEqual(summary.count(M.P63.SUMMARY_BEGIN.encode()), 3)
            self.assertNotIn(b"Reviewer opaque", summary)
            self.assertNotIn(b"Executor opaque", summary)
            self.assertEqual(historical.read_bytes(), before)
            self.assertTrue(M.P4.path_is_within(run_root, framework / "1PCloop/.local/runs"))
            self.assertEqual(self.git(remote, "rev-parse", "main"), checkpoint["framework_commit_id"])
            self.assertEqual(self.git(framework, "rev-list", "--count", f"{baseline}..HEAD"), "1")

    def test_special_summary_text_cannot_inject_markdown_control(self):
        special = "line one\n## forged\n```\n<!-- 1PCLOOP_SUMMARY_ENTRY_BEGIN bad -->\n你好 🌍"
        with tempfile.TemporaryDirectory() as tmp:
            args, _, _, _, _, _ = self.fixture(Path(tmp), run_id="safe-summary")
            code, _ = self.run_loop(
                args,
                environment={
                    "P6_TEST_VERDICT": "HUMAN_GATE",
                    "P6_TEST_SUMMARY": special,
                },
            )
            self.assertEqual(code, 0)
            checkpoint = self.checkpoint(args)
            self.assertTrue(all(
                entry["llm_evidence_summary"]["text"] == special
                for entry in self.entries(checkpoint)
            ))
            rendered = M.summary_path_for_args(args, args.run_id).read_text()
            self.assertNotIn("\n## forged", rendered)
            self.assertNotIn("<!-- 1PCLOOP_SUMMARY_ENTRY_BEGIN bad -->", rendered)
            self.assertIn("你好 🌍", rendered)

    def test_summary_recovery_boundaries_do_not_repeat_entries_or_turns(self):
        for boundary in ("before-write", "after-write", "after-checkpoint"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _, _, _, _, _ = self.fixture(root, run_id=f"summary-{boundary}")
                calls = root / "calls.log"
                crashed = False

                def observer(_state, checkpoint):
                    nonlocal crashed
                    if crashed:
                        return
                    pending = checkpoint.get("summary_pending")
                    progress = checkpoint.get("summary_progress", [])
                    if boundary == "before-write" and pending is not None:
                        crashed = True
                        raise SimulatedCrash()
                    if boundary == "after-checkpoint" and pending is None and len(progress) == 1:
                        crashed = True
                        raise SimulatedCrash()

                original = M.P63.reconcile_summary_plan

                def write_then_crash(**kwargs):
                    nonlocal crashed
                    result = original(**kwargs)
                    if boundary == "after-write" and not crashed:
                        crashed = True
                        raise SimulatedCrash()
                    return result

                with patch.dict(os.environ, {
                    "P6_TEST_VERDICT": "HUMAN_GATE",
                    "P5_TEST_CALL_LOG": str(calls),
                }, clear=False), patch.object(
                    M.P63, "reconcile_summary_plan", side_effect=write_then_crash
                ):
                    with self.assertRaises(SimulatedCrash):
                        self.run_loop(args, observer=observer)
                args.resume = True
                code, _ = self.run_loop(
                    args,
                    environment={
                        "P6_TEST_VERDICT": "HUMAN_GATE",
                        "P5_TEST_CALL_LOG": str(calls),
                    },
                )
                self.assertEqual(code, 0)
                checkpoint = self.checkpoint(args)
                self.assertEqual(len(checkpoint["summary_progress"]), 3)
                self.assertEqual(len(calls.read_text().splitlines()), 3)
                summary = M.summary_path_for_args(args, args.run_id).read_bytes()
                self.assertEqual(summary.count(M.P63.SUMMARY_BEGIN.encode()), 3)

    def test_summary_tamper_fails_closed_without_overwrite(self):
        for mutation in ("summary", "raw-artifact"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, _, _, _, _, _ = self.fixture(
                    root, run_id=f"tamper-{mutation}"
                )
                crashed = False

                def observer(_state, checkpoint):
                    nonlocal crashed
                    if not crashed and len(checkpoint.get("summary_progress", [])) == 1:
                        crashed = True
                        raise SimulatedCrash()

                with self.assertRaises(SimulatedCrash):
                    self.run_loop(args, observer=observer)
                summary = M.summary_path_for_args(args, args.run_id)
                if mutation == "summary":
                    summary.write_bytes(summary.read_bytes() + b"unexplained bytes\n")
                    expected_error = "partial, or extra"
                    changed = summary.read_bytes()
                else:
                    entry = self.entries(self.checkpoint(args))[0]
                    events = next(
                        Path(item["locator"])
                        for item in entry["raw_artifacts"]
                        if item["name"] == "events.jsonl"
                    )
                    events.write_bytes(events.read_bytes() + b"tampered\n")
                    expected_error = "artifact hash/length"
                    changed = summary.read_bytes()
                args.resume = True
                with self.assertRaisesRegex(M.P63.EvidenceError, expected_error):
                    self.run_loop(args)
                self.assertEqual(summary.read_bytes(), changed)

    def test_all_logical_outcomes_create_one_allowlisted_framework_commit(self):
        cases = (
            ("accept", {"P6_TEST_VERDICT": "ACCEPT"}, True, 0),
            ("human", {"P6_TEST_VERDICT": "HUMAN_GATE"}, False, 0),
            ("failed", {"P6_TEST_INVALID_ROLE": M.EXECUTOR_RECEIPT}, False, 1),
        )
        for name, environment, transition, expected_code in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                args, framework, remote, target_remote, baseline, target_remote_head = self.fixture(
                    Path(tmp), run_id=f"outcome-{name}", runtime_transition=transition
                )
                code, _ = self.run_loop(args, environment=environment)
                self.assertEqual(code, expected_code)
                checkpoint = self.checkpoint(args)
                self.assertEqual(checkpoint["state"], M.FRAMEWORK_EVIDENCE_PUSHED)
                commit = checkpoint["framework_commit_id"]
                self.assertEqual(self.git(framework, "rev-list", "--count", f"{baseline}..HEAD"), "1")
                paths = self.git(framework, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines()
                expected = [f"1PCloop/evidence-summaries/{args.run_id}.md"]
                if transition:
                    expected.append("1PCloop/workloads/fixture/workload_runtime.md")
                    runtime = args.workload_runtime.read_bytes()
                    self.assertEqual(runtime.count(b"1PCLOOP_RUNTIME_TRANSITION_RECORD"), 1)
                self.assertEqual(sorted(paths), sorted(expected))
                self.assertEqual(self.git(remote, "rev-parse", "main"), commit)
                self.assertEqual(self.git(target_remote, "rev-parse", args.target_branch), target_remote_head)
                if name == "failed":
                    invalid = [
                        entry for entry in self.entries(checkpoint)
                        if entry["llm_evidence_summary"]["status"] == "invalid_or_unavailable"
                    ]
                    self.assertEqual(len(invalid), 1)

    def test_dirty_branch_head_and_staged_changes_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, framework, _, _, _, _ = self.fixture(root, run_id="dirty-start")
            (framework / "unrelated.txt").write_text("human edit\n")
            with self.assertRaisesRegex(M.InvariantViolation, "must be clean"):
                M.validate_preflight(args)
        with tempfile.TemporaryDirectory() as tmp:
            args, _, _, _, _, _ = self.fixture(Path(tmp), run_id="wrong-branch")
            args.framework_branch = "other"
            args.framework_push_ref = "refs/heads/other"
            with self.assertRaisesRegex(M.InvariantViolation, "branch mismatch"):
                M.validate_preflight(args)
        for mutation in ("head", "staged", "runtime", "remote"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, framework, _, _, baseline, _ = self.fixture(
                    root, run_id=f"finalizer-{mutation}"
                )
                alternate_remote = root / "alternate-framework-remote.git"
                if mutation == "remote":
                    subprocess.run(
                        ["git", "init", "-q", "--bare", alternate_remote],
                        check=True,
                    )
                    subprocess.run(
                        ["git", "push", "-q", str(alternate_remote), "main"],
                        cwd=framework,
                        check=True,
                    )
                mutated = False

                def observer(state, _checkpoint):
                    nonlocal mutated
                    if state != M.HUMAN_GATE or mutated:
                        return
                    mutated = True
                    if mutation == "head":
                        subprocess.run(
                            ["git", "commit", "--allow-empty", "-qm", "unexpected"],
                            cwd=framework,
                            check=True,
                        )
                    elif mutation == "staged":
                        (framework / "unrelated.txt").write_text("unexpected\n")
                        subprocess.run(
                            ["git", "add", "--", "unrelated.txt"],
                            cwd=framework,
                            check=True,
                        )
                    elif mutation == "runtime":
                        args.workload_runtime.write_text(
                            args.workload_runtime.read_text(encoding="utf-8")
                            + "unauthorized Runtime edit\n",
                            encoding="utf-8",
                        )
                    else:
                        subprocess.run(
                            ["git", "remote", "set-url", "origin", str(alternate_remote)],
                            cwd=framework,
                            check=True,
                        )

                code, _ = self.run_loop(
                    args,
                    environment={"P6_TEST_VERDICT": "HUMAN_GATE"},
                    observer=observer,
                )
                self.assertEqual(code, 1)
                checkpoint = self.checkpoint(args)
                self.assertEqual(checkpoint["state"], M.EVIDENCE_FINALIZATION_PENDING)
                self.assertFalse(checkpoint["framework_evidence_committed"])
                if mutation == "staged":
                    self.assertEqual(self.git(framework, "rev-parse", "HEAD"), baseline)

    def test_commit_after_crash_is_reconciled_without_second_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, framework, remote, _, baseline, _ = self.fixture(root, run_id="commit-recovery")
            calls = root / "calls.log"
            original = M.P63.commit_or_reconcile
            crashed = False

            def commit_then_crash(plan):
                nonlocal crashed
                result = original(plan)
                if not crashed:
                    crashed = True
                    raise SimulatedCrash()
                return result

            with patch.dict(os.environ, {
                "P6_TEST_VERDICT": "HUMAN_GATE",
                "P5_TEST_CALL_LOG": str(calls),
            }, clear=False), patch.object(
                M.P63, "commit_or_reconcile", side_effect=commit_then_crash
            ):
                with self.assertRaises(SimulatedCrash):
                    self.run_loop(args)
            committed = self.git(framework, "rev-parse", "HEAD")
            self.assertNotEqual(committed, baseline)
            args.resume = True
            code, _ = self.run_loop(
                args,
                environment={"P5_TEST_CALL_LOG": str(calls)},
            )
            self.assertEqual(code, 0)
            checkpoint = self.checkpoint(args)
            self.assertEqual(checkpoint["framework_commit_id"], committed)
            self.assertEqual(self.git(framework, "rev-list", "--count", f"{baseline}..HEAD"), "1")
            self.assertEqual(self.git(remote, "rev-parse", "main"), committed)
            self.assertEqual(len(calls.read_text().splitlines()), 3)

    def test_push_failure_and_post_push_crash_resume_only_the_push(self):
        for boundary in ("failure", "post-push"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, framework, remote, _, baseline, _ = self.fixture(
                    root, run_id=f"push-{boundary}"
                )
                calls = root / "calls.log"
                hook = remote / "hooks/pre-receive"
                if boundary == "failure":
                    hook.write_text("#!/bin/sh\nexit 1\n")
                    hook.chmod(0o755)
                original = M.P63.push_or_reconcile
                crashed = False

                def push_then_crash(plan, commit):
                    nonlocal crashed
                    result = original(plan, commit)
                    if boundary == "post-push" and not crashed:
                        crashed = True
                        raise SimulatedCrash()
                    return result

                environment = {
                    "P6_TEST_VERDICT": "HUMAN_GATE",
                    "P5_TEST_CALL_LOG": str(calls),
                }
                if boundary == "post-push":
                    with patch.object(M.P63, "push_or_reconcile", side_effect=push_then_crash):
                        with self.assertRaises(SimulatedCrash):
                            self.run_loop(args, environment=environment)
                else:
                    self.assertEqual(self.run_loop(args, environment=environment)[0], 1)
                checkpoint = self.checkpoint(args)
                commit = self.git(framework, "rev-parse", "HEAD")
                self.assertNotEqual(commit, baseline)
                self.assertEqual(checkpoint["state"], M.FRAMEWORK_EVIDENCE_COMMITTED)
                if boundary == "failure":
                    self.assertEqual(self.git(remote, "rev-parse", "main"), baseline)
                    hook.unlink()
                else:
                    self.assertEqual(self.git(remote, "rev-parse", "main"), commit)
                calls_before = calls.read_bytes()
                args.resume = True
                code, _ = self.run_loop(args, environment={"P5_TEST_CALL_LOG": str(calls)})
                self.assertEqual(code, 0)
                self.assertEqual(calls.read_bytes(), calls_before)
                checkpoint = self.checkpoint(args)
                self.assertEqual(checkpoint["state"], M.FRAMEWORK_EVIDENCE_PUSHED)
                self.assertEqual(self.git(remote, "rev-parse", "main"), commit)
                self.assertIn(checkpoint["framework_push_result"], {"succeeded", "already-present"})

    def test_runtime_transition_is_not_replayed_while_push_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, framework, remote, _, _, _ = self.fixture(
                root, run_id="runtime-push-recovery", runtime_transition=True
            )
            hook = remote / "hooks/pre-receive"
            hook.write_text("#!/bin/sh\nexit 1\n")
            hook.chmod(0o755)
            code, _ = self.run_loop(args, environment={"P6_TEST_VERDICT": "ACCEPT"})
            self.assertEqual(code, 1)
            commit = self.git(framework, "rev-parse", "HEAD")
            runtime = args.workload_runtime.read_bytes()
            self.assertEqual(runtime.count(b"1PCLOOP_RUNTIME_TRANSITION_RECORD"), 1)
            hook.unlink()
            args.resume = True
            with patch.object(M, "atomic_replace_runtime") as writer:
                self.assertEqual(self.run_loop(args)[0], 0)
                writer.assert_not_called()
            self.assertEqual(args.workload_runtime.read_bytes(), runtime)
            self.assertEqual(self.git(remote, "rev-parse", "main"), commit)


if __name__ == "__main__":
    unittest.main()
