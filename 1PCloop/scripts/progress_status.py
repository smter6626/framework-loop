#!/usr/bin/env python3
"""F2 structured progress journal, live snapshot, and terminal renderer.

This module is an observation layer. Checkpoint, governance, Git, and actual
artifacts remain authoritative for recovery and control decisions.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import threading
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, TextIO


SCHEMA_VERSION = 1
EVENTS_FILENAME = "control-events.jsonl"
STATUS_FILENAME = "live-status.json"
EVENT_TYPES = frozenset({
    "run_started",
    "run_resumed",
    "state_entered",
    "turn_started",
    "codex_activity",
    "heartbeat",
    "tool_activity",
    "turn_finished",
    "correction",
    "logical_outcome",
    "evidence_finalization",
    "error",
    "run_finished",
})
ROLES = frozenset({"reviewer", "executor", "orchestrator"})
RUNTIME_TRANSITIONS = frozenset({"APPLIED", "NOT_APPLIED", "PENDING"})
EVIDENCE_PUBLICATIONS = frozenset({
    "PUSHED", "COMMITTED", "FAILED", "PENDING", "NOT_ENABLED", "NOT_STARTED",
})
EVENT_FIELDS = (
    "schema_version",
    "sequence",
    "event_id",
    "event_type",
    "timestamp",
    "run_id",
    "cycle",
    "role",
    "control_state",
    "run_elapsed_seconds",
    "stage_elapsed_seconds",
    "timeout_remaining_seconds",
    "last_activity",
    "target_head",
    "logical_outcome",
    "runtime_transition",
    "evidence_publication",
    "tool_activity",
)
LAST_ACTIVITY_FIELDS = ("timestamp", "kind")
TOOL_ACTIVITY_FIELDS = ("count", "last_kind")
TOOL_KINDS = frozenset({"command_execution", "mcp_tool_call", "web_search"})
CODEX_ACTIVITY_KINDS = frozenset({
    "thread.started", "turn.started", "turn.completed", "error",
})
MAX_EVENT_STRING_CHARS = 256
OBJECT_ID_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class ProgressError(RuntimeError):
    """Structured observation state cannot be reconciled mechanically."""


class SystemClock:
    def monotonic(self) -> float:
        return time.monotonic()

    def utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")


def event_identity(event_without_id: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json(event_without_id))


def contains_control(value: str) -> bool:
    return any(
        unicodedata.category(character) in {"Cc", "Cf", "Zl", "Zp"}
        for character in value
    )


def _fsync_directory(path: Path) -> None:
    try:
        directory_fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(
        value, ensure_ascii=True, indent=2, sort_keys=True
    ).encode("ascii") + b"\n"
    temporary: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{path.name}.tmp-", dir=path.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{path.name}.tmp-", dir=path.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def validate_event(event: Mapping[str, Any]) -> None:
    if len(event) != len(EVENT_FIELDS) or set(event) != set(EVENT_FIELDS):
        raise ProgressError("progress event field set is invalid")
    if event.get("schema_version") != SCHEMA_VERSION:
        raise ProgressError("progress event schema version is unsupported")
    if type(event.get("sequence")) is not int or event["sequence"] < 1:
        raise ProgressError("progress event sequence is invalid")
    if event.get("event_type") not in EVENT_TYPES:
        raise ProgressError("progress event type is invalid")
    if (
        not isinstance(event.get("event_id"), str)
        or re.fullmatch(r"[0-9a-f]{64}", event["event_id"]) is None
    ):
        raise ProgressError("progress event identity is missing")
    without_id = {name: event[name] for name in EVENT_FIELDS if name != "event_id"}
    if event["event_id"] != event_identity(without_id):
        raise ProgressError("progress event identity hash mismatch")
    for name in ("timestamp", "run_id", "control_state"):
        if not isinstance(event.get(name), str) or not event[name]:
            raise ProgressError(f"progress event {name} is invalid")
        if len(event[name]) > MAX_EVENT_STRING_CHARS:
            raise ProgressError(f"progress event {name} exceeds its bound")
        if contains_control(event[name]):
            raise ProgressError(f"progress event {name} contains a control character")
    cycle = event.get("cycle")
    if cycle is not None and (type(cycle) is not int or cycle < 1):
        raise ProgressError("progress event cycle is invalid")
    if event.get("role") is not None and event["role"] not in ROLES:
        raise ProgressError("progress event role is invalid")
    target_head = event.get("target_head")
    if target_head is not None and (
        not isinstance(target_head, str)
        or OBJECT_ID_PATTERN.fullmatch(target_head) is None
    ):
        raise ProgressError("progress event target HEAD is invalid")
    logical_outcome = event.get("logical_outcome")
    if logical_outcome is not None and (
        not isinstance(logical_outcome, str)
        or not logical_outcome
        or len(logical_outcome) > MAX_EVENT_STRING_CHARS
        or contains_control(logical_outcome)
    ):
        raise ProgressError("progress logical-outcome projection is invalid")
    for name in ("run_elapsed_seconds", "stage_elapsed_seconds"):
        value = event.get(name)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value < 0
        ):
            raise ProgressError(f"progress event {name} is invalid")
    remaining = event.get("timeout_remaining_seconds")
    if remaining is not None and (
        not isinstance(remaining, (int, float))
        or isinstance(remaining, bool)
        or not math.isfinite(remaining)
        or remaining < 0
    ):
        raise ProgressError("progress event timeout remaining is invalid")
    activity = event.get("last_activity")
    if (
        not isinstance(activity, dict)
        or len(activity) != len(LAST_ACTIVITY_FIELDS)
        or set(activity) != set(LAST_ACTIVITY_FIELDS)
    ):
        raise ProgressError("progress event last activity is invalid")
    if not all(isinstance(activity.get(name), str) and activity[name]
               for name in LAST_ACTIVITY_FIELDS):
        raise ProgressError("progress event last activity content is invalid")
    if any(len(activity[name]) > MAX_EVENT_STRING_CHARS for name in LAST_ACTIVITY_FIELDS):
        raise ProgressError("progress event last activity exceeds its bound")
    if any(contains_control(activity[name]) for name in LAST_ACTIVITY_FIELDS):
        raise ProgressError("progress event last activity contains a control character")
    tool = event.get("tool_activity")
    if (
        not isinstance(tool, dict)
        or len(tool) != len(TOOL_ACTIVITY_FIELDS)
        or set(tool) != set(TOOL_ACTIVITY_FIELDS)
    ):
        raise ProgressError("progress event tool activity is invalid")
    if type(tool.get("count")) is not int or tool["count"] < 0:
        raise ProgressError("progress event tool activity count is invalid")
    if tool.get("last_kind") is not None and tool["last_kind"] not in TOOL_KINDS:
        raise ProgressError("progress event tool activity kind is invalid")
    if event.get("runtime_transition") is not None and (
        event["runtime_transition"] not in RUNTIME_TRANSITIONS
    ):
        raise ProgressError("progress Runtime-transition projection is invalid")
    if event.get("evidence_publication") is not None and (
        event["evidence_publication"] not in EVIDENCE_PUBLICATIONS
    ):
        raise ProgressError("progress evidence-publication projection is invalid")


def scan_events(path: Path) -> tuple[List[Dict[str, Any]], bool]:
    if not path.exists():
        return [], False
    if not path.is_file() or path.is_symlink():
        raise ProgressError("progress event log is missing or aliased")
    data = path.read_bytes()
    recovered_tail = False
    if data and not data.endswith(b"\n"):
        recovered_tail = True
        boundary = data.rfind(b"\n")
        data = data[:boundary + 1] if boundary >= 0 else b""
        atomic_write_bytes(path, data)
    events: List[Dict[str, Any]] = []
    previous: Optional[Dict[str, Any]] = None
    for expected_sequence, line in enumerate(data.splitlines(), start=1):
        try:
            value = json.loads(line.decode("ascii"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ProgressError("progress event log contains an invalid complete line") from exc
        if not isinstance(value, dict):
            raise ProgressError("progress event line is not an object")
        validate_event(value)
        if value["sequence"] != expected_sequence:
            raise ProgressError("progress event sequence is not contiguous")
        if previous is not None:
            if value["run_elapsed_seconds"] < previous["run_elapsed_seconds"]:
                raise ProgressError("progress run elapsed time moved backwards")
            if (
                value["control_state"] == previous["control_state"]
                and value["stage_elapsed_seconds"] < previous["stage_elapsed_seconds"]
            ):
                raise ProgressError("progress stage elapsed time moved backwards")
            prior_remaining = previous["timeout_remaining_seconds"]
            remaining = value["timeout_remaining_seconds"]
            if (
                prior_remaining is not None
                and remaining is not None
                and value["control_state"] == previous["control_state"]
                and remaining > prior_remaining
            ):
                raise ProgressError("progress timeout remaining increased")
        events.append(value)
        previous = value
    return events, recovered_tail


class ProgressStatus:
    """One run's reconstructable observation stream and current projection."""

    def __init__(
        self,
        *,
        run_root: Path,
        run_id: str,
        public_text: Callable[[str], str],
        terminal_scalar: Callable[[Any], str],
        clock: Optional[Any] = None,
        output: Optional[TextIO] = None,
        is_tty: Optional[bool] = None,
        tool_throttle_seconds: float = 1.0,
        status_writer: Callable[[Path, Mapping[str, Any]], None] = atomic_write_json,
        append_hook: Optional[Callable[[str, Mapping[str, Any]], None]] = None,
        resume: bool = False,
        checkpoint_progress: Optional[Mapping[str, Any]] = None,
        checkpoint_state: Optional[str] = None,
    ) -> None:
        self.run_root = run_root.resolve()
        self.run_id = public_text(run_id)
        self.events_path = self.run_root / EVENTS_FILENAME
        self.status_path = self.run_root / STATUS_FILENAME
        self.public_text = public_text
        self.terminal_scalar = terminal_scalar
        self.clock = clock or SystemClock()
        self.output = output
        self.is_tty = bool(output.isatty()) if is_tty is None and output is not None else bool(is_tty)
        self.tool_throttle_seconds = max(float(tool_throttle_seconds), 0.0)
        self.status_writer = status_writer
        self.append_hook = append_hook
        self._lock = threading.RLock()
        self._last_monotonic = float(self.clock.monotonic())
        if not math.isfinite(self._last_monotonic):
            raise ProgressError("initial monotonic clock value is invalid")
        self._invocation_start = self._last_monotonic
        self._stage_start = self._last_monotonic
        self._last_timestamp: Optional[str] = None
        self._run_base = 0.0
        self._stage_base = 0.0
        self._sequence = 0
        self._last_event_id: Optional[str] = None
        self._control_state = "INITIALIZING"
        self._cycle: Optional[int] = None
        self._role: Optional[str] = "orchestrator"
        self._target_head: Optional[str] = None
        self._logical_outcome: Optional[str] = None
        self._runtime_transition: Optional[str] = None
        self._evidence_publication: Optional[str] = None
        self._last_activity: Optional[Dict[str, str]] = None
        self._timeout_deadline: Optional[float] = None
        self._timeout_last: Optional[float] = None
        self._tool_count = 0
        self._tool_last_kind: Optional[str] = None
        self._last_tool_emit: Optional[float] = None
        self._last_tool_emitted_count = 0
        self.status_available = True
        self.terminal_available = True
        self.observation_available = True
        self.observation_error: Optional[str] = None
        self.recovered_incomplete_tail = False
        events, recovered = scan_events(self.events_path)
        self.recovered_incomplete_tail = recovered
        if resume:
            self._resume(events, checkpoint_progress, checkpoint_state)
            self.record(
                "run_resumed",
                activity_kind=(
                    "resume_after_incomplete_event_tail" if recovered else "run_resumed"
                ),
            )
        else:
            if events or self.status_path.exists():
                raise ProgressError("new run progress artifacts already exist")

    def _now(self) -> float:
        observed = float(self.clock.monotonic())
        if not math.isfinite(observed):
            observed = self._last_monotonic
        if observed < self._last_monotonic:
            observed = self._last_monotonic
        self._last_monotonic = observed
        return observed

    def _timestamp(self) -> str:
        observed = self.public_text(str(self.clock.utc_now()))
        if self._last_timestamp is not None and observed < self._last_timestamp:
            observed = self._last_timestamp
        self._last_timestamp = observed
        return observed

    def _elapsed(self, now: float) -> tuple[float, float]:
        run_elapsed = self._run_base + max(0.0, now - self._invocation_start)
        stage_elapsed = self._stage_base + max(0.0, now - self._stage_start)
        return round(run_elapsed, 3), round(stage_elapsed, 3)

    def _remaining(self, now: float) -> Optional[float]:
        if self._timeout_deadline is None:
            return None
        remaining = max(0.0, self._timeout_deadline - now)
        if self._timeout_last is not None:
            remaining = min(remaining, self._timeout_last)
        self._timeout_last = remaining
        return round(remaining, 3)

    def _resume(
        self,
        events: Sequence[Mapping[str, Any]],
        checkpoint_progress: Optional[Mapping[str, Any]],
        checkpoint_state: Optional[str],
    ) -> None:
        if not isinstance(checkpoint_progress, Mapping) or not isinstance(checkpoint_state, str):
            raise ProgressError("resume checkpoint lacks F2 progress metadata")
        if checkpoint_progress.get("schema_version") != SCHEMA_VERSION:
            raise ProgressError("resume progress metadata version is unsupported")
        if (
            checkpoint_progress.get("events_path") != str(self.events_path)
            or checkpoint_progress.get("status_path") != str(self.status_path)
        ):
            raise ProgressError("resume progress paths differ from the run root")
        cursor = checkpoint_progress.get("sequence")
        if type(cursor) is not int or cursor < 0 or cursor > len(events):
            raise ProgressError("resume progress cursor is outside the event log")
        expected_id = checkpoint_progress.get("event_id")
        if cursor == 0:
            if expected_id is not None:
                raise ProgressError("zero progress cursor has an event identity")
        elif events[cursor - 1].get("event_id") != expected_id:
            raise ProgressError("resume progress cursor identity mismatch")
        for event in events:
            if event.get("run_id") != self.run_id:
                raise ProgressError("progress event run identity mismatch")
        for event in events[cursor:]:
            if event.get("control_state") != checkpoint_state:
                raise ProgressError("event suffix conflicts with checkpoint control state")
        self._sequence = len(events)
        self._last_event_id = events[-1]["event_id"] if events else None
        self._control_state = checkpoint_state
        self._cycle = checkpoint_progress.get("cycle")
        self._role = checkpoint_progress.get("role")
        self._target_head = checkpoint_progress.get("target_head")
        self._logical_outcome = checkpoint_progress.get("logical_outcome")
        self._runtime_transition = checkpoint_progress.get("runtime_transition")
        self._evidence_publication = checkpoint_progress.get("evidence_publication")
        last = events[-1] if events else None
        checkpoint_run = checkpoint_progress.get("run_elapsed_seconds")
        checkpoint_stage = checkpoint_progress.get("stage_elapsed_seconds")
        if (
            not isinstance(checkpoint_run, (int, float))
            or isinstance(checkpoint_run, bool)
            or checkpoint_run < 0
            or not isinstance(checkpoint_stage, (int, float))
            or isinstance(checkpoint_stage, bool)
            or checkpoint_stage < 0
        ):
            raise ProgressError("resume progress timing metadata is invalid")
        self._run_base = max(
            float(checkpoint_run),
            float(last.get("run_elapsed_seconds", 0.0)) if last else 0.0,
        )
        last_stage = (
            float(last.get("stage_elapsed_seconds", 0.0))
            if last and last.get("control_state") == checkpoint_state else 0.0
        )
        self._stage_base = max(
            float(checkpoint_stage), last_stage
        )
        self._last_activity = dict(last["last_activity"]) if last else (
            dict(checkpoint_progress["last_activity"])
            if isinstance(checkpoint_progress.get("last_activity"), dict) else None
        )
        if last:
            self._last_timestamp = last["timestamp"]
            tool = last["tool_activity"]
            self._tool_count = tool["count"]
            self._tool_last_kind = tool["last_kind"]
            self._last_tool_emitted_count = self._tool_count
        now = self._now()
        self._invocation_start = now
        self._stage_start = now

    def prepare_state(
        self,
        *,
        control_state: str,
        cycle: Optional[int],
        role: Optional[str],
        target_head: Optional[str],
        logical_outcome: Optional[str],
        runtime_transition: Optional[str],
        evidence_publication: Optional[str],
    ) -> Dict[str, Any]:
        with self._lock:
            now = self._now()
            if control_state != self._control_state:
                self._stage_base = 0.0
                self._stage_start = now
            self._control_state = self.public_text(control_state)[:MAX_EVENT_STRING_CHARS]
            self._cycle = cycle
            self._role = role
            self._target_head = self.public_text(target_head) if target_head is not None else None
            self._logical_outcome = (
                self.public_text(logical_outcome) if logical_outcome is not None else None
            )
            self._runtime_transition = runtime_transition
            self._evidence_publication = evidence_publication
            return self.checkpoint_record()

    def checkpoint_record(self) -> Dict[str, Any]:
        with self._lock:
            now = self._now()
            run_elapsed, stage_elapsed = self._elapsed(now)
            return {
                "control_state": self._control_state,
                "cycle": self._cycle,
                "event_id": self._last_event_id,
                "events_path": str(self.events_path),
                "evidence_publication": self._evidence_publication,
                "last_activity": dict(self._last_activity) if self._last_activity else None,
                "logical_outcome": self._logical_outcome,
                "observation_available": self.observation_available,
                "observation_error": self.observation_error,
                "role": self._role,
                "run_elapsed_seconds": run_elapsed,
                "runtime_transition": self._runtime_transition,
                "schema_version": SCHEMA_VERSION,
                "sequence": self._sequence,
                "stage_elapsed_seconds": stage_elapsed,
                "status_available": self.status_available,
                "status_path": str(self.status_path),
                "target_head": self._target_head,
                "terminal_available": self.terminal_available,
            }

    def commit_state(self) -> Dict[str, Any]:
        return self.record(
            "run_started" if self._sequence == 0 else "state_entered",
            activity_kind="state_transition",
        )

    def turn_started(self, *, role: str, timeout_seconds: float) -> Dict[str, Any]:
        with self._lock:
            now = self._now()
            self._role = role
            self._timeout_deadline = now + max(0.0, float(timeout_seconds))
            self._timeout_last = max(0.0, float(timeout_seconds))
            self._tool_count = 0
            self._tool_last_kind = None
            self._last_tool_emit = None
            self._last_tool_emitted_count = 0
        return self.record("turn_started", activity_kind="turn_started")

    def codex_activity(self, kind: str) -> Optional[Dict[str, Any]]:
        if kind not in CODEX_ACTIVITY_KINDS:
            return None
        return self.record("codex_activity", activity_kind=f"codex:{kind}")

    def tool_activity(self, kind: str) -> Optional[Dict[str, Any]]:
        if kind not in TOOL_KINDS:
            return None
        with self._lock:
            now = self._now()
            self._tool_count += 1
            self._tool_last_kind = kind
            should_emit = (
                self._last_tool_emit is None
                or now - self._last_tool_emit >= self.tool_throttle_seconds
            )
            if not should_emit:
                return None
            self._last_tool_emit = now
            self._last_tool_emitted_count = self._tool_count
        return self.record("tool_activity", activity_kind=f"tool:{kind}")

    def flush_tool_activity(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if (
                self._tool_last_kind is None
                or self._tool_count <= self._last_tool_emitted_count
            ):
                return None
            kind = self._tool_last_kind
            now = self._now()
            if self._last_tool_emit is not None and now == self._last_tool_emit:
                return None
            self._last_tool_emit = now
            self._last_tool_emitted_count = self._tool_count
        return self.record("tool_activity", activity_kind=f"tool:{kind}")

    def heartbeat(self) -> Dict[str, Any]:
        return self.record("heartbeat", activity_kind="heartbeat")

    def turn_finished(self, *, success: bool) -> Dict[str, Any]:
        self.flush_tool_activity()
        with self._lock:
            self._timeout_deadline = None
            self._timeout_last = None
            self._role = "orchestrator"
        return self.record(
            "turn_finished",
            activity_kind="turn_finished_success" if success else "turn_finished_failure",
        )

    def record(
        self,
        event_type: str,
        *,
        activity_kind: str,
        force_terminal: bool = True,
    ) -> Dict[str, Any]:
        if event_type not in EVENT_TYPES:
            raise ProgressError("unknown progress event type")
        with self._lock:
            now = self._now()
            timestamp = self._timestamp()
            self._last_activity = {
                "timestamp": timestamp,
                "kind": self.public_text(activity_kind)[:MAX_EVENT_STRING_CHARS],
            }
            run_elapsed, stage_elapsed = self._elapsed(now)
            without_id: Dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "sequence": self._sequence + 1,
                "event_type": event_type,
                "timestamp": timestamp,
                "run_id": self.run_id,
                "cycle": self._cycle,
                "role": self._role,
                "control_state": self._control_state,
                "run_elapsed_seconds": run_elapsed,
                "stage_elapsed_seconds": stage_elapsed,
                "timeout_remaining_seconds": self._remaining(now),
                "last_activity": dict(self._last_activity),
                "target_head": self._target_head,
                "logical_outcome": self._logical_outcome,
                "runtime_transition": self._runtime_transition,
                "evidence_publication": self._evidence_publication,
                "tool_activity": {
                    "count": self._tool_count,
                    "last_kind": self._tool_last_kind,
                },
            }
            event: Dict[str, Any] = {}
            for name in EVENT_FIELDS:
                event[name] = (
                    event_identity(without_id) if name == "event_id" else without_id[name]
                )
            validate_event(event)
            line = canonical_json(event) + b"\n"
            try:
                if self.append_hook is not None:
                    self.append_hook("before_append", event)
                self.events_path.parent.mkdir(parents=True, exist_ok=True)
                with self.events_path.open("ab") as handle:
                    handle.write(line)
                    handle.flush()
                    os.fsync(handle.fileno())
                _fsync_directory(self.events_path.parent)
                if self.append_hook is not None:
                    self.append_hook("after_append", event)
            except OSError as exc:
                raise ProgressError("progress event append failed") from exc
            self._sequence = event["sequence"]
            self._last_event_id = event["event_id"]
            try:
                self.status_writer(self.status_path, event)
            except Exception:
                self.status_available = False
            if force_terminal and self.output is not None and self.terminal_available:
                try:
                    self._render(event)
                except Exception:
                    self.terminal_available = False
            return event

    def _render(self, event: Mapping[str, Any]) -> None:
        activity = event["last_activity"]
        values = {
            "run": event["run_id"],
            "cycle": event["cycle"],
            "role": event["role"],
            "state": event["control_state"],
            "run_elapsed": event["run_elapsed_seconds"],
            "stage_elapsed": event["stage_elapsed_seconds"],
            "timeout_remaining": event["timeout_remaining_seconds"],
            "last_activity": f"{activity['kind']}@{activity['timestamp']}",
            "target_head": event["target_head"],
        }
        line = "PROGRESS " + " ".join(
            f"{name}={self.terminal_scalar(value)}" for name, value in values.items()
        )
        self.output.write(line + "\n")
        self.output.flush()
