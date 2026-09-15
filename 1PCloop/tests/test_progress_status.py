"""F2 structured progress, timing, recovery, and rendering tests."""

import io
import json
import os
import subprocess
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import test_evidence_summary as p63_tests
import test_run_mutation_loop as legacy
import test_verdict_correction as f1_tests


M = legacy.MODULE
P = M.PROGRESS


class FakeClock:
    def __init__(self, monotonic=0.0, wall_seconds=0.0):
        self.value = float(monotonic)
        self.wall_seconds = float(wall_seconds)
        self.base = datetime(2026, 9, 15, tzinfo=timezone.utc)
        self.lock = threading.Lock()

    def monotonic(self):
        with self.lock:
            return self.value

    def utc_now(self):
        with self.lock:
            current = self.base + timedelta(seconds=self.wall_seconds)
            return current.isoformat(timespec="milliseconds")

    def advance(self, seconds, wall_seconds=None):
        with self.lock:
            self.value += float(seconds)
            self.wall_seconds += float(
                seconds if wall_seconds is None else wall_seconds
            )

    def set_monotonic(self, value):
        with self.lock:
            self.value = float(value)


class SimulatedObservationCrash(BaseException):
    pass


class FailingTerminal(io.StringIO):
    def write(self, _value):
        raise OSError("terminal fixture failure")


class ProgressStatusTests(unittest.TestCase):
    make_legacy_fixture = legacy.MutationLoopTests.make_fixture

    def reporter(
        self,
        root,
        *,
        run_id="f2-test",
        clock=None,
        output=None,
        is_tty=False,
        resume=False,
        checkpoint_progress=None,
        checkpoint_state=None,
        **kwargs,
    ):
        run_root = root / run_id
        run_root.mkdir(parents=True, exist_ok=True)
        return P.ProgressStatus(
            run_root=run_root,
            run_id=run_id,
            public_text=M.escape_public_text,
            terminal_scalar=M.terminal_scalar,
            clock=clock or FakeClock(),
            output=output,
            is_tty=is_tty,
            tool_throttle_seconds=1.0,
            resume=resume,
            checkpoint_progress=checkpoint_progress,
            checkpoint_state=checkpoint_state,
            **kwargs,
        )

    def enter(self, reporter, state="S1", *, role="orchestrator", cycle=1):
        checkpoint = reporter.prepare_state(
            control_state=state,
            cycle=cycle,
            role=role,
            target_head="a" * 40,
            logical_outcome=None,
            runtime_transition=None,
            evidence_publication=None,
        )
        event = reporter.commit_state()
        return checkpoint, event

    def events(self, reporter):
        events, recovered = P.scan_events(reporter.events_path)
        self.assertFalse(recovered)
        return events

    def test_default_progress_artifacts_are_git_ignored(self):
        for relative in (
            "1PCloop/.local/runs/f2-probe/control-events.jsonl",
            "1PCloop/.local/runs/f2-probe/live-status.json",
        ):
            completed = subprocess.run(
                ["git", "check-ignore", "-q", "--no-index", "--", relative],
                cwd=M.FRAMEWORK_ROOT,
                check=False,
            )
            self.assertEqual(completed.returncode, 0)

    def test_event_contract_sequence_identity_and_new_run_initialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clock = FakeClock()
            reporter = self.reporter(root, clock=clock, output=io.StringIO())
            checkpoint, first = self.enter(reporter)
            clock.advance(2)
            second = reporter.heartbeat()
            events = self.events(reporter)

            self.assertEqual(checkpoint["sequence"], 0)
            self.assertEqual([event["sequence"] for event in events], [1, 2])
            self.assertEqual([event["event_type"] for event in events], [
                "run_started", "heartbeat"
            ])
            self.assertNotEqual(first["event_id"], second["event_id"])
            for event in events:
                self.assertEqual(set(event), set(P.EVENT_FIELDS))
                P.validate_event(event)
                without_id = {
                    name: event[name] for name in P.EVENT_FIELDS if name != "event_id"
                }
                self.assertEqual(event["event_id"], P.event_identity(without_id))
            with self.assertRaisesRegex(P.ProgressError, "already exist"):
                self.reporter(root, clock=clock)

    def test_run_stage_timeout_and_last_activity_use_injected_clock(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = FakeClock()
            reporter = self.reporter(Path(tmp), clock=clock, output=io.StringIO())
            self.enter(reporter, "REVIEWER_INSTRUCTION_RUNNING", role="reviewer")
            clock.advance(5)
            heartbeat = reporter.heartbeat()
            self.assertEqual(heartbeat["run_elapsed_seconds"], 5.0)
            self.assertEqual(heartbeat["stage_elapsed_seconds"], 5.0)
            self.assertIsNone(heartbeat["timeout_remaining_seconds"])
            self.assertEqual(heartbeat["last_activity"]["kind"], "heartbeat")

            started = reporter.turn_started(role="reviewer", timeout_seconds=10)
            self.assertEqual(started["timeout_remaining_seconds"], 10.0)
            clock.advance(3)
            active = reporter.heartbeat()
            self.assertEqual(active["timeout_remaining_seconds"], 7.0)
            clock.set_monotonic(1)
            backwards = reporter.heartbeat()
            self.assertGreaterEqual(
                backwards["run_elapsed_seconds"], active["run_elapsed_seconds"]
            )
            self.assertEqual(backwards["timeout_remaining_seconds"], 7.0)
            clock.set_monotonic(float("nan"))
            invalid = reporter.heartbeat()
            self.assertEqual(
                invalid["run_elapsed_seconds"], backwards["run_elapsed_seconds"]
            )
            self.assertEqual(invalid["timeout_remaining_seconds"], 7.0)
            clock.set_monotonic(21)
            expired = reporter.heartbeat()
            self.assertEqual(expired["timeout_remaining_seconds"], 0.0)
            finished = reporter.turn_finished(success=False)
            self.assertIsNone(finished["timeout_remaining_seconds"])

            reporter.prepare_state(
                control_state="INSTRUCTION_READY",
                cycle=1,
                role="orchestrator",
                target_head="a" * 40,
                logical_outcome=None,
                runtime_transition=None,
                evidence_publication=None,
            )
            state_event = reporter.commit_state()
            self.assertEqual(state_event["stage_elapsed_seconds"], 0.0)
            self.assertGreaterEqual(
                state_event["run_elapsed_seconds"], expired["run_elapsed_seconds"]
            )

    def test_resume_excludes_stopped_wall_time_and_continues_same_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_clock = FakeClock()
            first = self.reporter(root, clock=first_clock, output=io.StringIO())
            self.enter(first, "REVIEW_PENDING", role="reviewer")
            first_clock.advance(5)
            last_before = first.heartbeat()
            checkpoint = first.checkpoint_record()

            resumed_clock = FakeClock(monotonic=1000, wall_seconds=1000)
            resumed = self.reporter(
                root,
                clock=resumed_clock,
                output=io.StringIO(),
                resume=True,
                checkpoint_progress=checkpoint,
                checkpoint_state="REVIEW_PENDING",
            )
            resume_event = self.events(resumed)[-1]
            self.assertEqual(resume_event["event_type"], "run_resumed")
            self.assertEqual(
                resume_event["run_elapsed_seconds"],
                last_before["run_elapsed_seconds"],
            )
            self.assertEqual(
                resume_event["stage_elapsed_seconds"],
                last_before["stage_elapsed_seconds"],
            )
            self.assertEqual(resume_event["last_activity"]["kind"], "run_resumed")
            resumed_clock.advance(2)
            continued = resumed.heartbeat()
            self.assertEqual(continued["run_elapsed_seconds"], 7.0)
            self.assertEqual(continued["stage_elapsed_seconds"], 7.0)
            resumed.prepare_state(
                control_state="REVIEW_COMPLETED",
                cycle=1,
                role="orchestrator",
                target_head="a" * 40,
                logical_outcome=None,
                runtime_transition=None,
                evidence_publication=None,
            )
            self.assertEqual(resumed.commit_state()["stage_elapsed_seconds"], 0.0)

    def test_tool_activity_is_aggregated_and_throttled_without_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = FakeClock()
            reporter = self.reporter(Path(tmp), clock=clock, output=io.StringIO())
            self.enter(reporter, "EXECUTOR_RUNNING", role="executor")
            reporter.turn_started(role="executor", timeout_seconds=30)
            first = reporter.tool_activity("command_execution")
            clock.advance(0.2)
            self.assertIsNone(reporter.tool_activity("mcp_tool_call"))
            clock.advance(0.2)
            self.assertIsNone(reporter.tool_activity("web_search"))
            clock.advance(1.0)
            second = reporter.tool_activity("mcp_tool_call")
            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            self.assertEqual(second["tool_activity"], {
                "count": 4, "last_kind": "mcp_tool_call"
            })
            raw = reporter.events_path.read_text(encoding="ascii")
            self.assertNotIn("shell command", raw)
            self.assertNotIn("command output", raw)
            self.assertNotIn("peer_message", raw)
            self.assertEqual(
                [event["event_type"] for event in self.events(reporter)].count(
                    "tool_activity"
                ),
                2,
            )

    def test_incomplete_tail_is_truncated_and_sequence_resumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.reporter(root, output=io.StringIO())
            self.enter(first, "S1")
            checkpoint = first.checkpoint_record()
            with first.events_path.open("ab") as handle:
                handle.write(b'{"incomplete":')

            resumed = self.reporter(
                root,
                clock=FakeClock(10, 10),
                output=io.StringIO(),
                resume=True,
                checkpoint_progress=checkpoint,
                checkpoint_state="S1",
            )
            self.assertTrue(resumed.recovered_incomplete_tail)
            events = self.events(resumed)
            self.assertEqual([event["sequence"] for event in events], [1, 2])
            self.assertEqual(
                events[-1]["last_activity"]["kind"],
                "resume_after_incomplete_event_tail",
            )

    def test_event_append_crash_before_and_after_is_reconciled(self):
        for boundary in ("before_append", "after_append"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                crashed = False

                def hook(stage, _event):
                    nonlocal crashed
                    if stage == boundary and not crashed:
                        crashed = True
                        raise SimulatedObservationCrash()

                reporter = self.reporter(root, output=io.StringIO(), append_hook=hook)
                checkpoint = reporter.prepare_state(
                    control_state="S1",
                    cycle=1,
                    role="orchestrator",
                    target_head="a" * 40,
                    logical_outcome=None,
                    runtime_transition=None,
                    evidence_publication=None,
                )
                with self.assertRaises(SimulatedObservationCrash):
                    reporter.commit_state()
                resumed = self.reporter(
                    root,
                    clock=FakeClock(10, 10),
                    output=io.StringIO(),
                    resume=True,
                    checkpoint_progress=checkpoint,
                    checkpoint_state="S1",
                )
                events = self.events(resumed)
                expected = 1 if boundary == "before_append" else 2
                self.assertEqual(len(events), expected)
                self.assertEqual(events[-1]["event_type"], "run_resumed")
                self.assertEqual(
                    [event["sequence"] for event in events],
                    list(range(1, expected + 1)),
                )

    def test_checkpoint_event_conflicts_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.reporter(root, output=io.StringIO())
            checkpoint, _ = self.enter(first, "S1")
            with self.assertRaisesRegex(P.ProgressError, "conflicts"):
                self.reporter(
                    root,
                    output=io.StringIO(),
                    resume=True,
                    checkpoint_progress=checkpoint,
                    checkpoint_state="S2",
                )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.reporter(root, output=io.StringIO())
            self.enter(first, "S1")
            checkpoint = first.checkpoint_record()
            checkpoint["event_id"] = "0" * 64
            with self.assertRaisesRegex(P.ProgressError, "identity mismatch"):
                self.reporter(
                    root,
                    output=io.StringIO(),
                    resume=True,
                    checkpoint_progress=checkpoint,
                    checkpoint_state="S1",
                )

    def test_live_status_is_atomic_latest_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            reporter = self.reporter(Path(tmp), output=io.StringIO())
            self.enter(reporter, "S1")
            latest = reporter.heartbeat()
            status = json.loads(reporter.status_path.read_text(encoding="ascii"))
            self.assertEqual(status, latest)
            self.assertEqual(list(reporter.status_path.parent.glob(".live-status.json.tmp-*")), [])

    def test_status_and_terminal_failures_do_not_stop_event_journal(self):
        def fail_status(_path, _value):
            raise OSError("status fixture failure")

        with tempfile.TemporaryDirectory() as tmp:
            reporter = self.reporter(
                Path(tmp), output=io.StringIO(), status_writer=fail_status
            )
            self.enter(reporter, "S1")
            reporter.heartbeat()
            self.assertFalse(reporter.status_available)
            self.assertEqual(len(self.events(reporter)), 2)

        with tempfile.TemporaryDirectory() as tmp:
            reporter = self.reporter(Path(tmp), output=FailingTerminal())
            self.enter(reporter, "S1")
            reporter.heartbeat()
            self.assertFalse(reporter.terminal_available)
            self.assertTrue(reporter.status_path.is_file())
            self.assertEqual(len(self.events(reporter)), 2)

    def test_observation_failures_do_not_change_authoritative_transition(self):
        helper = f1_tests.VerdictCorrectionTests(
            methodName="test_corrected_accept_resumes_same_thread_without_executor_replay"
        )
        for failure in ("event", "status", "terminal"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                args, target, governance, _ = helper.runtime_fixture(
                    root, run_id=f"observation-{failure}"
                )
                args.progress_clock = FakeClock()
                args.progress_output = (
                    FailingTerminal() if failure == "terminal" else io.StringIO()
                )
                if failure == "status":
                    def fail_status(_path, _value):
                        raise OSError("status fixture failure")
                    args.progress_status_writer = fail_status
                if failure == "event":
                    def fail_event(stage, _event):
                        if stage == "before_append":
                            raise OSError("event fixture failure")
                    args.progress_append_hook = fail_event
                with patch.dict(os.environ, {
                    "P6_TEST_VERDICT": "ACCEPT",
                }, clear=False):
                    code, _ = M.orchestrate(
                        args=args,
                        target_initial=target,
                        governance_initial=governance,
                    )
                self.assertEqual(code, 0)
                self.assertEqual(
                    args.workload_runtime.read_bytes().count(
                        b"1PCLOOP_RUNTIME_TRANSITION_RECORD"
                    ),
                    1,
                )
                checkpoint = M.CheckpointStore(
                    M.checkpoint_path_for_args(args)
                ).load()
                self.assertTrue(checkpoint["runtime_transition_applied"])
                if failure == "event":
                    self.assertFalse(checkpoint["progress"]["observation_available"])
                elif failure == "status":
                    self.assertFalse(checkpoint["progress"]["status_available"])
                else:
                    self.assertFalse(checkpoint["progress"]["terminal_available"])

    def test_tty_and_non_tty_render_fixed_safe_lines(self):
        for is_tty in (False, True):
            with self.subTest(is_tty=is_tty), tempfile.TemporaryDirectory() as tmp:
                output = io.StringIO()
                reporter = self.reporter(
                    Path(tmp), output=output, is_tty=is_tty,
                    run_id="safe-id",
                )
                self.enter(reporter, "S1")
                lines = output.getvalue().splitlines()
                self.assertEqual(len(lines), 1)
                self.assertTrue(lines[0].startswith("PROGRESS "))
                for field in (
                    "run=", "cycle=", "role=", "state=", "run_elapsed=",
                    "stage_elapsed=", "timeout_remaining=", "last_activity=",
                    "target_head=",
                ):
                    self.assertIn(field, lines[0])

    def test_public_controls_and_private_payload_fields_never_enter_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            reporter = self.reporter(
                Path(tmp), run_id="run\nSECRET", output=io.StringIO()
            )
            reporter.prepare_state(
                control_state="S\r\nFORGED" + ("x" * 400),
                cycle=1,
                role="orchestrator",
                target_head="a" * 40,
                logical_outcome=None,
                runtime_transition=None,
                evidence_publication=None,
            )
            reporter.commit_state()
            raw = reporter.events_path.read_bytes()
            self.assertEqual(len(raw.splitlines()), 1)
            self.assertNotIn(b"peer_message", raw)
            self.assertNotIn(b"prompt", raw)
            self.assertNotIn(b"stderr", raw)
            self.assertNotIn(b"command_output", raw)
            event = self.events(reporter)[0]
            self.assertNotIn("\n", event["run_id"])
            self.assertLessEqual(len(event["control_state"]), P.MAX_EVENT_STRING_CHARS)
            tampered = dict(event)
            tampered["last_activity"] = dict(event["last_activity"])
            tampered["last_activity"]["kind"] = "SECRET\nFORGED"
            without_id = {
                name: tampered[name]
                for name in P.EVENT_FIELDS if name != "event_id"
            }
            tampered["event_id"] = P.event_identity(without_id)
            with self.assertRaisesRegex(P.ProgressError, "control character"):
                P.validate_event(tampered)

    def test_mutation_loop_writes_progress_files_and_normal_state_sequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, target, governance, _ = self.make_legacy_fixture(
                root, run_id="f2-integration"
            )
            args.progress_clock = FakeClock()
            terminal = io.StringIO()
            args.progress_output = terminal
            code, run_root = M.orchestrate(
                args=args, target_initial=target, governance_initial=governance
            )
            self.assertEqual(code, 0)
            events, recovered = P.scan_events(run_root / P.EVENTS_FILENAME)
            self.assertFalse(recovered)
            self.assertEqual(events[-1]["event_type"], "run_finished")
            self.assertEqual(events[-1]["logical_outcome"], M.HUMAN_GATE)
            self.assertEqual(events[-1]["runtime_transition"], "NOT_APPLIED")
            self.assertEqual(events[-1]["evidence_publication"], "NOT_ENABLED")
            state_order = [
                event["control_state"] for event in events
                if event["event_type"] in {"run_started", "state_entered"}
            ]
            self.assertEqual(state_order, [
                M.PREFLIGHT_PASSED,
                M.REVIEWER_INSTRUCTION_RUNNING,
                M.INSTRUCTION_READY,
                M.EXECUTOR_RUNNING,
                M.EXECUTOR_COMMITTED,
                M.REVIEW_PENDING,
                M.REVIEW_COMPLETED,
                M.HUMAN_GATE,
            ])
            status = json.loads((run_root / P.STATUS_FILENAME).read_text())
            self.assertEqual(status, events[-1])
            raw = (run_root / P.EVENTS_FILENAME).read_text()
            self.assertNotIn("Reviewer opaque", raw)
            self.assertNotIn("Executor opaque", raw)
            self.assertNotIn("peer_message", raw)
            checkpoint = M.CheckpointStore(M.checkpoint_path_for_args(args)).load()
            self.assertLessEqual(checkpoint["progress"]["sequence"], events[-1]["sequence"])
            manifest = json.loads((run_root / "manifest.json").read_text())
            self.assertEqual(
                manifest["run_configuration"]["progress"]["events_path"],
                str(run_root / P.EVENTS_FILENAME),
            )
            self.assertIn("PROGRESS run=", terminal.getvalue())

    def test_correction_events_preserve_executor_and_thread_invariants(self):
        helper = f1_tests.VerdictCorrectionTests(
            methodName="test_corrected_accept_resumes_same_thread_without_executor_replay"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, target, governance, _ = helper.runtime_fixture(
                root, run_id="f2-correction"
            )
            calls = root / "calls.log"
            args.progress_clock = FakeClock()
            args.progress_output = io.StringIO()
            with patch.dict(os.environ, {
                "P5_TEST_CALL_LOG": str(calls),
                "P5_TEST_SCENARIO": "executor-commit",
                "P6_TEST_INITIAL_BAD_LOCATOR": "1",
                "P6_TEST_VERDICT": "ACCEPT",
            }, clear=False):
                code, run_root = M.orchestrate(
                    args=args,
                    target_initial=target,
                    governance_initial=governance,
                )
            self.assertEqual(code, 0)
            events, _ = P.scan_events(run_root / P.EVENTS_FILENAME)
            self.assertIn("correction", [event["event_type"] for event in events])
            correction_turns = [
                event for event in events
                if event["event_type"] == "turn_started"
                and event["control_state"] == M.REVIEW_CORRECTION_RUNNING
            ]
            self.assertEqual(len(correction_turns), 1)
            self.assertEqual(correction_turns[0]["role"], "reviewer")
            lines = calls.read_text().splitlines()
            self.assertEqual(lines.count("executor"), 1)
            self.assertEqual(lines.count("reviewer-correction-1"), 1)
            self.assertEqual(
                args.workload_runtime.read_bytes().count(
                    b"1PCLOOP_RUNTIME_TRANSITION_RECORD"
                ),
                1,
            )

    def test_failed_closed_emits_unclassified_error_without_diagnostic_payload(self):
        helper = f1_tests.VerdictCorrectionTests(
            methodName="test_unknown_validation_failure_is_not_correction_eligible"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, target, governance, _ = helper.runtime_fixture(
                root, run_id="f2-failed"
            )
            secret = "SECRET\nerror_code=FORGED"
            args.progress_clock = FakeClock()
            args.progress_output = io.StringIO()
            with patch.object(
                M, "validate_accept_evidence",
                side_effect=M.InvariantViolation(secret),
            ), patch.dict(os.environ, {"P6_TEST_VERDICT": "ACCEPT"}, clear=False):
                code, run_root = M.orchestrate(
                    args=args,
                    target_initial=target,
                    governance_initial=governance,
                )
            self.assertEqual(code, 1)
            events, _ = P.scan_events(run_root / P.EVENTS_FILENAME)
            self.assertIn("error", [event["event_type"] for event in events])
            self.assertEqual(events[-1]["event_type"], "run_finished")
            self.assertEqual(events[-1]["logical_outcome"], M.FAILED_CLOSED)
            raw = (run_root / P.EVENTS_FILENAME).read_text(encoding="ascii")
            self.assertNotIn("SECRET", raw)
            checkpoint = M.CheckpointStore(M.checkpoint_path_for_args(args)).load()
            self.assertIn(
                "SECRET",
                checkpoint["logical_outcome"]["internal_diagnostic"]["reason"],
            )

    def test_deterministic_subprocess_timeout_finishes_turn_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, target, governance, _ = self.make_legacy_fixture(
                root, run_id="f2-timeout"
            )
            args.progress_clock = FakeClock()
            args.progress_output = io.StringIO()

            def timeout_without_sleep(**kwargs):
                kwargs["events_path"].write_bytes(b"")
                kwargs["stderr_path"].write_bytes(b"")
                return None, b"", b"", "timeout after 10 seconds"

            with patch.object(M, "stream_subprocess", side_effect=timeout_without_sleep):
                code, run_root = M.orchestrate(
                    args=args,
                    target_initial=target,
                    governance_initial=governance,
                )
            self.assertEqual(code, 1)
            events, _ = P.scan_events(run_root / P.EVENTS_FILENAME)
            started = next(
                event for event in events if event["event_type"] == "turn_started"
            )
            finished = next(
                event for event in events if event["event_type"] == "turn_finished"
            )
            self.assertEqual(started["timeout_remaining_seconds"], 10.0)
            self.assertIsNone(finished["timeout_remaining_seconds"])
            self.assertEqual(
                finished["last_activity"]["kind"], "turn_finished_failure"
            )
            self.assertEqual(events[-1]["logical_outcome"], M.FAILED_CLOSED)
            process = json.loads((
                run_root / "cycle-01/reviewer-instruction/process.json"
            ).read_text())
            self.assertIn("timeout after 10 seconds", process["failure"])

    def test_publication_failure_and_resume_keep_logical_projection(self):
        helper = p63_tests.EvidenceSummaryTests(
            methodName="test_runtime_transition_is_not_replayed_while_push_recovers"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, _, remote, _, _, _ = helper.fixture(
                root, run_id="f2-publication", runtime_transition=True
            )
            calls = root / "calls.log"
            hook = remote / "hooks/pre-receive"
            hook.write_text("#!/bin/sh\nexit 1\n")
            hook.chmod(0o755)
            args.progress_clock = FakeClock()
            args.progress_output = io.StringIO()
            target, governance = M.validate_preflight(args)
            with patch.dict(os.environ, {
                "P5_TEST_CALL_LOG": str(calls),
                "P6_TEST_VERDICT": "ACCEPT",
            }, clear=False):
                code, run_root = M.orchestrate(
                    args=args, target_initial=target, governance_initial=governance
                )
            self.assertEqual(code, 1)
            first_events, _ = P.scan_events(run_root / P.EVENTS_FILENAME)
            self.assertEqual(first_events[-1]["logical_outcome"], M.RUNTIME_TRANSITION_COMMITTED)
            self.assertEqual(first_events[-1]["runtime_transition"], "APPLIED")
            self.assertEqual(first_events[-1]["evidence_publication"], "FAILED")
            calls_before = calls.read_bytes()

            hook.unlink()
            args.resume = True
            args.progress_clock = FakeClock(monotonic=1000, wall_seconds=1000)
            current_target, current_governance = M.validate_preflight(args)
            with patch.dict(os.environ, {
                "P5_TEST_CALL_LOG": str(calls),
            }, clear=False):
                code, _ = M.orchestrate(
                    args=args,
                    target_initial=current_target,
                    governance_initial=current_governance,
                )
            self.assertEqual(code, 0)
            self.assertEqual(calls.read_bytes(), calls_before)
            events, _ = P.scan_events(run_root / P.EVENTS_FILENAME)
            self.assertEqual(
                [event["sequence"] for event in events],
                list(range(1, len(events) + 1)),
            )
            self.assertEqual(events[-1]["logical_outcome"], M.RUNTIME_TRANSITION_COMMITTED)
            self.assertEqual(events[-1]["runtime_transition"], "APPLIED")
            self.assertEqual(events[-1]["evidence_publication"], "PUSHED")


if __name__ == "__main__":
    unittest.main()
