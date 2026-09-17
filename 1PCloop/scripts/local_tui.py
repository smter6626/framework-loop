#!/usr/bin/env python3
"""Read-only terminal presenter for config-backed operator projections.

Only the injected data source may read operator state. Rendering consumes the
structured status/inspect envelopes and never reads raw Agent artifacts.
"""

from __future__ import annotations

import curses
import math
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from human_gate import ALLOWED_ACTIONS, GATE_STATUSES, RECOVERY_MODES
from mutation_contracts import escape_public_text
from progress_status import TURN_CONTROL_STATES


REFRESH_INTERVAL_MS = 1000
GATE_COMPARE_FIELDS = (
    "gate_status",
    "reason_code",
    "allowed_actions",
    "recovery_mode",
    "evidence_availability",
)
STATE_COMPARE_FIELDS = (
    "checkpoint_state",
    "logical_outcome",
    "runtime_transition",
    "evidence_publication",
)
RUN_PROJECTION_FIELDS = (
    "run_id",
    "checkpoint_state",
    "logical_outcome",
    "runtime_transition",
    "evidence_publication",
)
INSPECTION_NAMES = (
    "checkpoint_identity",
    "manifest",
    "observation",
    "summary",
    "framework_commit",
    "framework_push",
    "target",
    "correction_provenance",
    "target_evidence",
)


class OperatorDataSource:
    """Read the existing F3/F5 projections without opening artifacts here."""

    def __init__(self, operator: Any, config: Any) -> None:
        self.operator = operator
        self.config = config

    def read(self) -> Dict[str, Mapping[str, Any]]:
        return {
            "status": self.operator.status(self.config),
            "inspect": self.operator.inspect_run(self.config),
        }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _public(value: Any, limit: int = 96) -> str:
    if limit <= 0:
        return ""
    if value is None:
        return "-"
    if isinstance(value, bool):
        value = "yes" if value else "no"
    if not isinstance(value, (str, int, float)):
        return "-"
    if isinstance(value, float):
        if not math.isfinite(value):
            return "-"
    safe = escape_public_text(str(value))[:limit]
    return safe or "-"


def _seconds(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "-"
    try:
        valid = math.isfinite(value) and value >= 0
    except (OverflowError, ValueError):
        valid = False
    if not valid:
        return "-"
    return f"{value:.1f}s"


def _has_run_projection(result: Mapping[str, Any]) -> bool:
    return any(result.get(name) is not None for name in RUN_PROJECTION_FIELDS)


def _stable_no_checkpoint(
    status: Mapping[str, Any],
    inspect: Mapping[str, Any],
    result: Mapping[str, Any],
    inspect_result: Mapping[str, Any],
    gate: Mapping[str, Any],
    inspect_gate: Mapping[str, Any],
) -> bool:
    """Recognize the exact F3 no-checkpoint pair, not an arbitrary inspect FAIL."""
    checks = inspect.get("checks")
    checkpoint_check = (
        checks[0]
        if isinstance(checks, list) and len(checks) == 1
        and isinstance(checks[0], Mapping)
        else {}
    )
    status_artifacts = _mapping(status.get("artifacts"))
    inspect_artifacts = _mapping(inspect.get("artifacts"))
    return (
        not _has_run_projection(result)
        and gate.get("gate_status") == "NOT_APPLICABLE"
        and gate.get("reason_code") == "NO_CHECKPOINT"
        and gate.get("recovery_mode") == "NO_ACTION"
        and gate.get("allowed_actions") == ["NO_AUTOMATIC_REPAIR"]
        and gate.get("evidence_availability") == "UNAVAILABLE"
        and result.get("safe_next_action") == "START_NEW_RUN_ALLOWED"
        and not _has_run_projection(inspect_result)
        and inspect.get("overall_status") == "FAIL"
        and checkpoint_check.get("name") == "checkpoint_identity"
        and checkpoint_check.get("status") == "FAIL"
        and checkpoint_check.get("code") == "CHECKPOINT_IDENTITY_FAILED"
        and inspect_gate.get("gate_status") == "INVALID"
        and inspect_gate.get("reason_code") == "IDENTITY_CONFLICT"
        and inspect_gate.get("recovery_mode") == "HUMAN_REMEDIATION_REQUIRED"
        and inspect_gate.get("allowed_actions") == [
            "INSPECT_EVIDENCE",
            "REMEDIATE_EXTERNAL_STATE",
            "NO_AUTOMATIC_REPAIR",
        ]
        and inspect_gate.get("evidence_availability") == "UNAVAILABLE"
        and inspect_result.get("safe_next_action") == "STATE_UNAVAILABLE"
        and status.get("config_identity") == inspect.get("config_identity")
        and status_artifacts.get("checkpoint") == inspect_artifacts.get("checkpoint")
    )


def _snapshot_parts(
    snapshot: Mapping[str, Any],
) -> Tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], bool, bool]:
    status = _mapping(snapshot.get("status"))
    inspect = _mapping(snapshot.get("inspect"))
    result = _mapping(status.get("result"))
    inspect_result = _mapping(inspect.get("result"))
    gate = _mapping(result.get("human_gate_projection"))
    inspect_gate = _mapping(inspect_result.get("human_gate_projection"))
    actions = gate.get("allowed_actions")
    no_checkpoint = _stable_no_checkpoint(
        status, inspect, result, inspect_result, gate, inspect_gate
    )
    basic_contract = (
        status.get("command") == "status"
        and inspect.get("command") == "inspect"
        and status.get("config_identity") == inspect.get("config_identity")
        and isinstance(gate.get("gate_status"), str)
        and gate.get("gate_status") in GATE_STATUSES
        and isinstance(gate.get("recovery_mode"), str)
        and gate.get("recovery_mode") in RECOVERY_MODES
        and isinstance(actions, list)
        and all(isinstance(action, str) and action in ALLOWED_ACTIONS for action in actions)
        and not (
            gate.get("gate_status") in {"INVALID", "UNAVAILABLE"}
            and any(action in {"FINALIZE_EVIDENCE", "START_NEW_RUN_AFTER_HUMAN_REVIEW"} for action in actions)
        )
    )
    existing_run_consistent = (
        isinstance(result.get("run_id"), str)
        and bool(result.get("run_id"))
        and isinstance(inspect_result.get("run_id"), str)
        and all(gate.get(key) == inspect_gate.get(key) for key in GATE_COMPARE_FIELDS)
        and all(result.get(key) == inspect_result.get(key) for key in STATE_COMPARE_FIELDS)
        and result.get("run_id") == inspect_result.get("run_id")
        and (inspect.get("overall_status") != "FAIL" or gate.get("gate_status") == "INVALID")
    )
    consistent = basic_contract and (no_checkpoint or existing_run_consistent)
    return result, inspect, gate, no_checkpoint, consistent


def _banner(result: Mapping[str, Any], gate: Mapping[str, Any], no_checkpoint: bool) -> str:
    if no_checkpoint:
        return "NO CHECKPOINT -- no run was opened"
    gate_status = gate.get("gate_status")
    if gate_status == "INVALID":
        return "IDENTITY INVALID -- no automatic action"
    if gate_status == "UNAVAILABLE":
        return "EVIDENCE UNAVAILABLE -- no automatic action"
    if result.get("failed_closed") is True:
        return "FAILED CLOSED -- inspect evidence"
    if gate_status == "ACTIVE":
        return "HUMAN GATE -- Human review required"
    publication = result.get("evidence_publication")
    state = result.get("checkpoint_state")
    if isinstance(publication, str) and publication in {"PENDING", "FAILED", "COMMITTED"}:
        return "PUBLICATION INCOMPLETE -- logical outcome unchanged"
    if isinstance(state, str) and state in TURN_CONTROL_STATES:
        return "ACTIVE TURN -- observed progress only"
    if publication == "PUSHED":
        return "PUBLICATION COMPLETE -- check logical outcome separately"
    return "RUN STATE -- read-only observation"


def _summary_lines(snapshot: Mapping[str, Any]) -> List[str]:
    result, inspect, gate, no_checkpoint, consistent = _snapshot_parts(snapshot)
    lines = ["1PCloop TUI -- READ ONLY"]
    if not consistent:
        return lines + [
            "SNAPSHOT UNAVAILABLE -- status/inspect projections disagree",
            "No recovery action is displayed. Press r to refresh.",
        ]
    activity = _mapping(result.get("last_activity"))
    observation = result.get("observation_availability")
    progress_available = observation == "AVAILABLE"
    actions = gate.get("allowed_actions", [])
    lines.extend([
        _banner(result, gate, no_checkpoint),
        "",
        "Run: {}    Cycle: {}".format(_public(result.get("run_id")), _public(result.get("cycle") if progress_available else None)),
        "Role: {}    Control: {}".format(_public(result.get("role") if progress_available else None), _public(result.get("checkpoint_state"))),
        "Target HEAD: {}".format(_public(result.get("target_head") if progress_available else None)),
        "",
        "F2 active-time progress -- no offline wall-time added",
        "Run elapsed: {}    Stage elapsed: {}".format(
            _seconds(result.get("run_elapsed_seconds")) if progress_available else "-",
            _seconds(result.get("stage_elapsed_seconds")) if progress_available else "-",
        ),
        "Timeout remaining: {}".format(_seconds(result.get("timeout_remaining_seconds")) if progress_available else "-"),
        "Last activity: {} @ {}".format(
            _public(activity.get("kind") if progress_available else None),
            _public(activity.get("timestamp") if progress_available else None),
        ),
        "",
        "Independent outcomes",
        "Logical outcome: {}".format(_public(result.get("logical_outcome"))),
        "Runtime transition: {}".format(_public(result.get("runtime_transition"))),
        "Evidence publication: {}".format(_public(result.get("evidence_publication"))),
        "",
        "Observation: {}    Inspect/integrity: {}".format(
            _public(observation), _public(inspect.get("overall_status"))
        ),
        "Human Gate: {}    Reason code: {}".format(
            _public(gate.get("gate_status")), _public(gate.get("reason_code"))
        ),
        "Evidence availability: {}".format(_public(gate.get("evidence_availability"))),
        "Recovery mode: {}".format(_public(gate.get("recovery_mode"))),
        "Allowed actions:",
    ])
    lines.extend("  - {}".format(action) for action in actions)
    if gate.get("recovery_mode") == "FINALIZATION_ONLY":
        if gate.get("gate_status") == "ACTIVE":
            lines.append("Terminal Human Gate -- finalization only; no Agent resume")
        else:
            lines.append("Evidence finalization only -- no Agent resume")
    elif gate.get("gate_status") == "ACTIVE" and gate.get("recovery_mode") == "NEW_RUN_AFTER_REVIEW":
        lines.append("Terminal Human Gate -- new run only after Human review")
    if result.get("evidence_publication") == "PUSHED":
        lines.append("PUSHED records publication, not logical success")
    return lines


def _inspection_lines(snapshot: Mapping[str, Any]) -> List[str]:
    result, inspect, gate, no_checkpoint, consistent = _snapshot_parts(snapshot)
    lines = ["1PCloop TUI -- INSPECTION (READ ONLY)"]
    if not consistent:
        return lines + ["SNAPSHOT UNAVAILABLE -- no recovery action is displayed"]
    lines.extend([
        _banner(result, gate, no_checkpoint),
        "Inspect/integrity: {}".format(_public(inspect.get("overall_status"))),
        "Observation: {}".format(_public(result.get("observation_availability"))),
        "Human Gate: {} / {}".format(_public(gate.get("gate_status")), _public(gate.get("reason_code"))),
        "Recovery mode: {}".format(_public(gate.get("recovery_mode"))),
        "Allowed actions:",
        "",
        "Authoritative checks (status/code only)",
    ])
    action_start = lines.index("Allowed actions:") + 1
    lines[action_start:action_start] = [
        "  - {}".format(action) for action in gate.get("allowed_actions", [])
    ]
    checks = inspect.get("checks")
    by_name = {
        item.get("name"): item
        for item in checks if isinstance(item, Mapping) and item.get("name") in INSPECTION_NAMES
    } if isinstance(checks, list) else {}
    for name in INSPECTION_NAMES:
        item = _mapping(by_name.get(name))
        lines.append("{}: {} / {}".format(
            name, _public(item.get("status")), _public(item.get("code"))
        ))
    return lines


def _help_lines() -> List[str]:
    return [
        "1PCloop TUI -- HELP (READ ONLY)",
        "",
        "r -- refresh structured operator projections",
        "Tab -- switch summary/inspection view",
        "j / Down -- scroll down",
        "k / Up -- scroll up",
        "? -- show/hide help",
        "q / Esc -- quit",
        "",
        "This dashboard never starts or resumes an Agent.",
        "It never executes a Human Gate action or finalization.",
        "Elapsed time is F2 active time, not offline wall time.",
        "Inspect PASS does not resolve a Human Gate.",
    ]


def render_frame(
    snapshot: Mapping[str, Any], *, view: str, width: int, height: int, scroll: int
) -> Tuple[List[str], int]:
    """Return bounded printable rows and the clamped scroll offset."""
    if width <= 0 or height <= 0:
        return [], 0
    if width < 48 or height < 4:
        lines = ["1PCloop TUI", "Terminal too small", "q quit / resize"]
        return [_public(line, max(width - 1, 0)) for line in lines[:height]], 0
    content = _help_lines() if view == "help" else (
        _inspection_lines(snapshot) if view == "inspect" else _summary_lines(snapshot)
    )
    footer = "r refresh | Tab view | j/k scroll | ? help | q quit"
    visible = max(height - 1, 0)
    offset = max(0, min(scroll, max(len(content) - visible, 0)))
    rows = content[offset:offset + visible]
    rows.extend([""] * (visible - len(rows)))
    rows.append(footer)
    return [_public(row, max(width - 1, 0)) if row else "" for row in rows], offset


class CursesTerminal:
    """Thin terminal adapter; curses.wrapper owns terminal restoration."""

    def __init__(self, window: Any) -> None:
        self.window = window
        self.window.keypad(True)
        try:
            curses.curs_set(0)
        except curses.error:
            pass

    def size(self) -> Tuple[int, int]:
        return self.window.getmaxyx()

    def draw(self, rows: Sequence[str]) -> None:
        self.window.erase()
        height, width = self.size()
        for row, line in enumerate(rows[:height]):
            if width <= 1:
                break
            try:
                self.window.addnstr(row, 0, line, width - 1)
            except curses.error:
                # Resize may occur between size() and addnstr().
                break
        self.window.refresh()

    def read_key(self, timeout_ms: int) -> int:
        self.window.timeout(timeout_ms)
        return self.window.getch()

    def close(self) -> None:
        # curses.wrapper restores keypad, echo, cbreak, and endwin.
        pass


def run_dashboard(source: Any, terminal: Any) -> int:
    """Bounded refresh loop; fake terminals can exercise it without sleep."""
    snapshot: Mapping[str, Any] = {}
    view = "summary"
    previous_view = "summary"
    scroll = 0
    try:
        snapshot = source.read()
        while True:
            height, width = terminal.size()
            rows, scroll = render_frame(
                snapshot, view=view, width=width, height=height, scroll=scroll
            )
            terminal.draw(rows)
            key = terminal.read_key(REFRESH_INTERVAL_MS)
            if key in (ord("q"), 27):
                return 0
            if key in (-1, ord("r")):
                snapshot = source.read()
            elif key == 9:
                if view == "help":
                    view = previous_view
                view = "inspect" if view == "summary" else "summary"
                scroll = 0
            elif key == ord("?"):
                if view == "help":
                    view = previous_view
                else:
                    previous_view = view
                    view = "help"
                scroll = 0
            elif key in (ord("j"), curses.KEY_DOWN):
                scroll += 1
            elif key in (ord("k"), curses.KEY_UP):
                scroll = max(scroll - 1, 0)
            elif key == curses.KEY_RESIZE:
                scroll = 0
    finally:
        terminal.close()


def main(source: Any, *, stdin: Any = None, stdout: Any = None, stderr: Any = None,
         wrapper: Any = None) -> int:
    """Reject non-TTY use before any operator read or terminal initialization."""
    input_stream = sys.stdin if stdin is None else stdin
    output_stream = sys.stdout if stdout is None else stdout
    error_stream = sys.stderr if stderr is None else stderr
    if not input_stream.isatty() or not output_stream.isatty():
        print("tui requires an interactive terminal", file=error_stream)
        return 2
    invoke = curses.wrapper if wrapper is None else wrapper
    try:
        return invoke(lambda window: run_dashboard(source, CursesTerminal(window)))
    except KeyboardInterrupt:
        return 130
    except Exception:
        print("tui unavailable; terminal restored", file=error_stream)
        return 1
