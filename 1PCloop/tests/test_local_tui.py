"""F6 read-only local TUI presenter and config-backed integration tests."""

import contextlib
import io
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

import local_tui as TUI


OP = operator_tests.OP
CLI = operator_tests.CLI


def snapshot(
    *, state="FRAMEWORK_EVIDENCE_PUSHED", logical="HUMAN_GATE",
    publication="PUSHED", gate_status="ACTIVE", reason="REVIEWER_HUMAN_GATE",
    recovery="NEW_RUN_AFTER_REVIEW", evidence="AVAILABLE", observation="AVAILABLE",
    actions=None, inspect_status="PASS",
):
    if actions is None:
        actions = ["INSPECT_EVIDENCE", "START_NEW_RUN_AFTER_HUMAN_REVIEW"]
    gate = {
        "gate_status": gate_status,
        "reason_code": reason,
        "recovery_mode": recovery,
        "allowed_actions": actions,
        "evidence_availability": evidence,
    }
    return {
        "status": {
            "command": "status",
            "overall_status": "FAIL" if gate_status == "INVALID" else "PASS",
            "result": {
                "run_id": "run-1",
                "checkpoint_state": state,
                "cycle": 2,
                "role": "Reviewer",
                "target_head": "a" * 40,
                "run_elapsed_seconds": 12.5,
                "stage_elapsed_seconds": 3.25,
                "timeout_remaining_seconds": 24.0,
                "last_activity": {"kind": "turn.completed", "timestamp": "2026-09-17T12:00:00Z"},
                "logical_outcome": logical,
                "runtime_transition": "NOT_APPLIED",
                "evidence_publication": publication,
                "observation_availability": observation,
                "failed_closed": state == "FAILED_CLOSED",
                "human_gate_projection": gate,
                "peer_message": "secret-peer-payload",
            },
            "raw_codex_events": "secret-event-payload",
        },
        "inspect": {
            "command": "inspect",
            "overall_status": inspect_status,
            "result": {
                "run_id": "run-1",
                "checkpoint_state": state,
                "logical_outcome": logical,
                "runtime_transition": "NOT_APPLIED",
                "evidence_publication": publication,
                "human_gate_projection": dict(gate),
            },
            "checks": [
                {"name": "target", "status": inspect_status, "code": "TARGET_PASSED", "detail": "secret-internal-diagnostic"},
            ],
        },
    }


def rendered(value, view="summary", width=160, height=40, scroll=0):
    rows, _ = TUI.render_frame(
        value, view=view, width=width, height=height, scroll=scroll
    )
    return "\n".join(rows)


class FakeSource:
    def __init__(self, value):
        self.value = value
        self.reads = 0

    def read(self):
        self.reads += 1
        return self.value


class FakeTerminal:
    def __init__(self, keys, sizes=None):
        self.keys = list(keys)
        self.sizes = list(sizes or [(30, 100)])
        self.frames = []
        self.timeouts = []
        self.closed = False

    def size(self):
        return self.sizes[min(len(self.frames), len(self.sizes) - 1)]

    def draw(self, rows):
        self.frames.append(list(rows))

    def read_key(self, timeout_ms):
        self.timeouts.append(timeout_ms)
        return self.keys.pop(0) if self.keys else ord("q")

    def close(self):
        self.closed = True


class LocalTuiTests(unittest.TestCase):
    def test_presenter_uses_active_time_without_wall_time_and_separates_outcomes(self):
        value = snapshot(logical="FAILED_CLOSED", publication="PUSHED")
        text = rendered(value)
        self.assertIn("Run elapsed: 12.5s", text)
        self.assertIn("Stage elapsed: 3.2s", text)
        self.assertIn("Timeout remaining: 24.0s", text)
        self.assertIn("Logical outcome: FAILED_CLOSED", text)
        self.assertIn("Evidence publication: PUSHED", text)
        self.assertIn("PUSHED records publication, not logical success", text)

    def test_fixed_state_banners_and_recovery_boundaries(self):
        cases = (
            ({"state": "EXECUTOR_RUNNING", "logical": "UNDETERMINED", "publication": "NOT_STARTED", "gate_status": "NOT_APPLICABLE", "reason": "NOT_A_HUMAN_GATE", "recovery": "NO_ACTION", "actions": ["NO_AUTOMATIC_REPAIR"]}, "ACTIVE TURN"),
            ({"state": "FAILED_CLOSED", "logical": "FAILED_CLOSED", "gate_status": "NOT_APPLICABLE", "reason": "NOT_A_HUMAN_GATE", "recovery": "NO_ACTION", "actions": ["NO_AUTOMATIC_REPAIR"]}, "FAILED CLOSED"),
            ({"state": "EVIDENCE_FINALIZATION_PENDING", "publication": "PENDING", "recovery": "FINALIZATION_ONLY", "actions": ["INSPECT_EVIDENCE", "FINALIZE_EVIDENCE"]}, "finalization only; no Agent resume"),
            ({"logical": "RUNTIME_TRANSITION_COMMITTED", "gate_status": "NOT_APPLICABLE", "reason": "NOT_A_HUMAN_GATE", "recovery": "NO_ACTION", "actions": ["INSPECT_EVIDENCE", "NO_AUTOMATIC_REPAIR"]}, "PUBLICATION COMPLETE"),
            ({"gate_status": "UNAVAILABLE", "reason": "REQUIRED_EVIDENCE_UNAVAILABLE", "recovery": "HUMAN_REMEDIATION_REQUIRED", "evidence": "UNAVAILABLE", "actions": ["INSPECT_EVIDENCE", "REMEDIATE_EXTERNAL_STATE", "NO_AUTOMATIC_REPAIR"]}, "EVIDENCE UNAVAILABLE"),
            ({"gate_status": "INVALID", "reason": "IDENTITY_CONFLICT", "recovery": "HUMAN_REMEDIATION_REQUIRED", "evidence": "INVALID", "actions": ["INSPECT_EVIDENCE", "REMEDIATE_EXTERNAL_STATE", "NO_AUTOMATIC_REPAIR"], "inspect_status": "FAIL"}, "IDENTITY INVALID"),
        )
        for changes, expected in cases:
            with self.subTest(expected=expected):
                value = snapshot(**changes)
                text = rendered(value)
                self.assertIn(expected, text)
                if changes.get("gate_status") in {"INVALID", "UNAVAILABLE"}:
                    self.assertNotIn("START_NEW_RUN_AFTER_HUMAN_REVIEW", text)
                    self.assertNotIn("FINALIZE_EVIDENCE", text)
        complete = rendered(snapshot())
        self.assertIn("Terminal Human Gate -- new run only after Human review", complete)
        self.assertNotIn("Agent resume", complete)

    def test_no_checkpoint_and_unverified_progress_are_explicit(self):
        value = snapshot()
        status = value["status"]["result"]
        status.update({
            "run_id": None,
            "checkpoint_state": None,
            "human_gate_projection": {
                "gate_status": "NOT_APPLICABLE",
                "reason_code": "NO_CHECKPOINT",
                "recovery_mode": "NO_ACTION",
                "allowed_actions": ["NO_AUTOMATIC_REPAIR"],
                "evidence_availability": "UNAVAILABLE",
            },
        })
        text = rendered(value)
        self.assertIn("NO CHECKPOINT", text)
        self.assertIn("  - NO_AUTOMATIC_REPAIR", text)
        value = snapshot(observation="UNAVAILABLE")
        text = rendered(value)
        self.assertIn("Observation: UNAVAILABLE", text)
        self.assertIn("Run elapsed: -", text)
        self.assertIn("Target HEAD: -", text)

    def test_malicious_unstructured_payload_and_control_characters_do_not_render(self):
        value = snapshot()
        value["status"]["result"]["run_id"] = "run\x1b[31m\nnext"
        value["inspect"]["result"]["run_id"] = "run\x1b[31m\nnext"
        value["status"]["result"]["prompt"] = "secret-prompt"
        value["inspect"]["checks"][0]["detail"] = "secret-stderr-command-output"
        for view in ("summary", "inspect"):
            text = rendered(value, view=view)
            for secret in ("secret-peer", "secret-event", "secret-prompt", "secret-stderr", "secret-internal"):
                self.assertNotIn(secret, text)
            self.assertNotIn("\x1b", text)
            self.assertNotIn("\nnext", text)
            if view == "summary":
                self.assertIn("run?[31m?next", text)

    def test_disagreeing_operator_projections_fail_closed_in_presenter(self):
        value = snapshot()
        value["inspect"]["result"]["human_gate_projection"]["recovery_mode"] = "NO_ACTION"
        text = rendered(value)
        self.assertIn("SNAPSHOT UNAVAILABLE", text)
        self.assertNotIn("START_NEW_RUN_AFTER_HUMAN_REVIEW", text)
        self.assertNotIn("FINALIZE_EVIDENCE", text)

    def test_malformed_actions_and_numbers_fail_closed_or_hide_timing(self):
        value = snapshot(gate_status="INVALID", reason="IDENTITY_CONFLICT",
                         recovery="HUMAN_REMEDIATION_REQUIRED", evidence="INVALID",
                         actions=["START_NEW_RUN_AFTER_HUMAN_REVIEW"])
        value["inspect"]["result"]["human_gate_projection"] = dict(
            value["status"]["result"]["human_gate_projection"]
        )
        text = rendered(value)
        self.assertIn("SNAPSHOT UNAVAILABLE", text)
        self.assertNotIn("START_NEW_RUN_AFTER_HUMAN_REVIEW", text)

        value = snapshot()
        value["status"]["result"]["run_elapsed_seconds"] = 10 ** 1000
        value["status"]["result"]["stage_elapsed_seconds"] = float("inf")
        self.assertIn("Run elapsed: -    Stage elapsed: -", rendered(value))

    def test_fake_keys_refresh_help_scroll_resize_and_cleanup(self):
        source = FakeSource(snapshot())
        terminal = FakeTerminal(
            [ord("j"), ord("k"), 9, ord("?"), ord("?"), TUI.curses.KEY_RESIZE, -1, ord("r"), ord("q")],
            sizes=[(8, 50), (8, 50), (8, 50), (8, 50), (8, 50), (4, 18), (30, 90)],
        )
        self.assertEqual(TUI.run_dashboard(source, terminal), 0)
        self.assertEqual(source.reads, 3)
        self.assertTrue(terminal.closed)
        self.assertTrue(all(timeout == TUI.REFRESH_INTERVAL_MS for timeout in terminal.timeouts))
        self.assertIn("HELP", "\n".join("\n".join(frame) for frame in terminal.frames))
        self.assertIn("Terminal too smal", "\n".join("\n".join(frame) for frame in terminal.frames))
        self.assertTrue(all(len(row) < 90 for row in terminal.frames[-1]))

    def test_terminal_close_on_error(self):
        class FailingSource:
            def read(self):
                raise RuntimeError("private error")

        terminal = FakeTerminal([])
        with self.assertRaises(RuntimeError):
            TUI.run_dashboard(FailingSource(), terminal)
        self.assertTrue(terminal.closed)

    def test_non_tty_never_reads_or_emits_screen_controls(self):
        source = FakeSource(snapshot())
        error = io.StringIO()
        with patch.object(TUI.curses, "wrapper") as wrapper:
            code = TUI.main(source, stdin=io.StringIO(), stdout=io.StringIO(), stderr=error)
        self.assertEqual(code, 2)
        self.assertEqual(source.reads, 0)
        wrapper.assert_not_called()
        self.assertEqual(error.getvalue(), "tui requires an interactive terminal\n")
        self.assertNotIn("\x1b", error.getvalue())

    def test_wrapper_exception_has_bounded_message_and_restores_terminal(self):
        class Tty(io.StringIO):
            def isatty(self):
                return True

        error = io.StringIO()
        code = TUI.main(
            FakeSource(snapshot()), stdin=Tty(), stdout=Tty(), stderr=error,
            wrapper=lambda _callback: (_ for _ in ()).throw(RuntimeError("private error")),
        )
        self.assertEqual(code, 1)
        self.assertEqual(error.getvalue(), "tui unavailable; terminal restored\n")

    def test_curses_adapter_clips_and_handles_resize_race(self):
        class Window:
            def __init__(self):
                self.drawn = []
                self.width = 8

            def keypad(self, value):
                self.keypad_value = value

            def getmaxyx(self):
                return (3, self.width)

            def erase(self):
                pass

            def addnstr(self, row, column, text, length):
                self.drawn.append((row, column, text[:length]))
                if row == 1:
                    raise TUI.curses.error("resized")

            def refresh(self):
                pass

            def timeout(self, value):
                self.timeout_value = value

            def getch(self):
                return ord("q")

        window = Window()
        with patch.object(TUI.curses, "curs_set", side_effect=TUI.curses.error("unsupported")):
            terminal = TUI.CursesTerminal(window)
        terminal.draw(["long line", "second line", "third line"])
        self.assertEqual(window.drawn[0], (0, 0, "long li"))
        self.assertEqual(len(window.drawn), 2)
        self.assertEqual(terminal.read_key(1000), ord("q"))
        self.assertEqual(window.timeout_value, 1000)

    def test_disposable_two_refreshes_preserve_artifacts_and_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            helper = operator_tests.OperatorCliTests()
            config_path, _value, args, framework, _remote, *_ = helper.fixture(
                Path(temporary), run_id="tui-read-only"
            )
            config = OP.load_config(config_path)
            code, run_root = helper.run_config(config)
            self.assertEqual(code, 0)
            checkpoint = OP.checkpoint_path(config)
            protected = [
                checkpoint,
                run_root / "manifest.json",
                run_root / OP.RUNNER.PROGRESS.EVENTS_FILENAME,
                run_root / OP.RUNNER.PROGRESS.STATUS_FILENAME,
                Path(config.resolved["evidence"]["summary_root"]) / "tui-read-only.md",
            ]
            before_bytes = {path: path.read_bytes() if path.is_file() else None for path in protected}

            def git_state(repo):
                return tuple(subprocess.check_output(
                    ["git", *command], cwd=repo
                ) for command in (
                    ["rev-parse", "HEAD"], ["branch", "--show-current"],
                    ["status", "--porcelain=v1", "--untracked-files=all"],
                    ["ls-remote", "--heads", "origin"],
                ))

            before_git = {repo: git_state(repo) for repo in (framework, args.target_repo)}
            source = TUI.OperatorDataSource(OP, config)
            terminal = FakeTerminal([ord("r"), ord("q")], sizes=[(40, 180)])
            self.assertEqual(TUI.run_dashboard(source, terminal), 0)
            text = "\n".join(terminal.frames[-1])
            self.assertIn("HUMAN GATE", text)
            self.assertIn("NEW_RUN_AFTER_REVIEW", text)
            self.assertIn("REVIEWER_HUMAN_GATE", text)
            self.assertEqual(
                {path: path.read_bytes() if path.is_file() else None for path in protected},
                before_bytes,
            )
            self.assertEqual({repo: git_state(repo) for repo in before_git}, before_git)

    def test_config_backed_non_tty_command_creates_no_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            helper = operator_tests.OperatorCliTests()
            config_path, _value, args, *_ = helper.fixture(Path(temporary))
            with contextlib.redirect_stdout(io.StringIO()) as output, contextlib.redirect_stderr(io.StringIO()) as error:
                code = CLI.main(["--config", str(config_path), "tui"])
            self.assertEqual(code, 2)
            self.assertEqual(output.getvalue(), "")
            self.assertEqual(error.getvalue(), "tui requires an interactive terminal\n")
            self.assertFalse(args.runs_root.exists())
            self.assertFalse(args.state_root.exists())

    def test_config_backed_tty_dispatch_reads_only_existing_projections(self):
        class Tty(io.StringIO):
            def isatty(self):
                return True

        with tempfile.TemporaryDirectory() as temporary:
            helper = operator_tests.OperatorCliTests()
            config_path, _value, args, *_ = helper.fixture(Path(temporary))
            terminal = FakeTerminal([ord("q")])
            with patch.object(TUI.sys, "stdin", Tty()), patch.object(TUI.sys, "stdout", Tty()), \
                    patch.object(TUI, "CursesTerminal", return_value=terminal), \
                    patch.object(TUI.curses, "wrapper", side_effect=lambda callback: callback(object())):
                code = CLI.main(["--config", str(config_path), "tui"])
            self.assertEqual(code, 0)
            self.assertTrue(terminal.closed)
            self.assertIn("NO CHECKPOINT", "\n".join(terminal.frames[0]))
            self.assertFalse(args.runs_root.exists())
            self.assertFalse(args.state_root.exists())


if __name__ == "__main__":
    unittest.main()
