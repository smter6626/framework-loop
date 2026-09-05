#!/usr/bin/env python3
"""Run the minimal Reviewer -> Executor -> Reviewer Codex transport loop."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
ACTIVE_ROOT = REPO_ROOT / "1PCloop"
ROLES_ROOT = ACTIVE_ROOT / "roles"
DEFAULT_RUNS_ROOT = ACTIVE_ROOT / "runs"
DEFAULT_REVIEWER_HOME = Path("/Users/smterpro/.codex-B")
DEFAULT_EXECUTOR_HOME = Path("/Users/smterpro/.codex-A")
PEER_MARKER = b"\n\n--- BEGIN VERBATIM PEER PAYLOAD ---\n"
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
EXPERIMENT_ID_PATTERN = RUN_ID_PATTERN
CONTROL_MODE = "ephemeral-control"
TREATMENT_MODE = "reviewer-resume-treatment"
RUN_SESSION_MODES = (CONTROL_MODE, TREATMENT_MODE)
FRESH_EPHEMERAL = "fresh-ephemeral"
NEW_PERSISTENT = "new-persistent"
RESUME = "resume"
TURN_SESSION_MODES = (FRESH_EPHEMERAL, NEW_PERSISTENT, RESUME)
USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def default_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{os.getpid()}"


def validate_run_id(value: str) -> str:
    if not RUN_ID_PATTERN.fullmatch(value):
        raise ValueError(
            "run id must start with an alphanumeric character and contain only "
            "letters, digits, dot, underscore, or hyphen"
        )
    return value


def validate_experiment_id(value: str) -> str:
    if not EXPERIMENT_ID_PATTERN.fullmatch(value):
        raise ValueError(
            "experiment id must start with an alphanumeric character and contain "
            "only letters, digits, dot, underscore, or hyphen"
        )
    return value


def command_stdout(command: List[str], *, cwd: Optional[Path] = None) -> str:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"command failed ({completed.returncode}): {detail}")
    return completed.stdout.strip()


def parse_top_level_toml_string(config: bytes, key: str) -> Optional[str]:
    """Read one simple top-level TOML string without exposing other config data."""
    try:
        text = config.decode("utf-8")
    except UnicodeDecodeError:
        return None
    pattern = re.compile(
        rf"^\s*{re.escape(key)}\s*=\s*(\"(?:[^\"\\]|\\.)*\"|'[^']*')\s*(?:#.*)?$"
    )
    values: List[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("["):
            break
        match = pattern.fullmatch(line)
        if match is None:
            continue
        literal = match.group(1)
        try:
            value = json.loads(literal) if literal.startswith('"') else literal[1:-1]
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        if not isinstance(value, str):
            return None
        values.append(value)
    return values[0] if len(values) == 1 else None


def profile_config_metadata(codex_home: Path) -> Dict[str, Any]:
    config_path = codex_home / "config.toml"
    if not config_path.is_file():
        return {
            "config_path": str(config_path),
            "config_sha256": None,
            "model": None,
            "model_reasoning_effort": None,
        }
    config = config_path.read_bytes()
    return {
        "config_path": str(config_path),
        "config_sha256": sha256_bytes(config),
        "model": parse_top_level_toml_string(config, "model"),
        "model_reasoning_effort": parse_top_level_toml_string(
            config, "model_reasoning_effort"
        ),
    }


def capture_frozen_context(
    *,
    repo_root: Path,
    codex_bin: str,
    reviewer_home: Path,
    executor_home: Path,
) -> Dict[str, Any]:
    git_status = command_stdout(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=repo_root
    )
    git_branch = command_stdout(["git", "branch", "--show-current"], cwd=repo_root)
    if git_status:
        raise RuntimeError("paired experiment requires a clean working tree")
    if git_branch != "main":
        raise RuntimeError("paired experiment requires branch main")

    static_path = repo_root / "1PCloop/docs/miniloop_static.md"
    runtime_path = repo_root / "1PCloop/docs/miniloop_runtime.md"
    roles_root = repo_root / "1PCloop/roles"
    prompt_paths = {
        "reviewer_initial_prompt_sha256": roles_root / "reviewer-initial.md",
        "executor_prompt_sha256": roles_root / "executor.md",
        "reviewer_review_prompt_sha256": roles_root / "reviewer-review.md",
    }
    return {
        "approval_policy": "never",
        "codex_executable": str(
            Path(shutil.which(codex_bin) or codex_bin).resolve()
        ),
        "codex_version": command_stdout([codex_bin, "--version"]),
        "executor_codex_home": str(executor_home),
        "executor_config": profile_config_metadata(executor_home),
        "git_branch": git_branch,
        "git_head": command_stdout(["git", "rev-parse", "HEAD"], cwd=repo_root),
        "git_status_clean": True,
        "reviewer_codex_home": str(reviewer_home),
        "reviewer_config": profile_config_metadata(reviewer_home),
        "runtime_sha256": sha256_file(runtime_path),
        "sandbox": "read-only",
        "session_modes": {
            CONTROL_MODE: [FRESH_EPHEMERAL, FRESH_EPHEMERAL, FRESH_EPHEMERAL],
            TREATMENT_MODE: [NEW_PERSISTENT, FRESH_EPHEMERAL, RESUME],
        },
        "static_sha256": sha256_file(static_path),
        **{key: sha256_file(path) for key, path in prompt_paths.items()},
    }


def read_role_prompt(filename: str) -> bytes:
    return (ROLES_ROOT / filename).read_bytes()


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def prepare_experiment(
    *,
    experiment_file: Path,
    experiment_id: str,
    session_mode: str,
    run_id: str,
    runs_root: Path,
    frozen_context: Dict[str, Any],
) -> Tuple[Dict[str, Any], int]:
    """Freeze paired context and register the next run in fixed order."""
    experiment_id = validate_experiment_id(experiment_id)
    run_order = [CONTROL_MODE, TREATMENT_MODE]
    if experiment_file.exists():
        try:
            document = json.loads(experiment_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RuntimeError(f"invalid experiment metadata: {exc}") from exc
        if not isinstance(document, dict):
            raise RuntimeError("invalid experiment metadata root")
    else:
        experiment_file.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "experiment_id": experiment_id,
            "frozen_at": utc_now(),
            "frozen_context": frozen_context,
            "run_order": run_order,
            "runs": [],
            "schema_version": 1,
        }

    if document.get("experiment_id") != experiment_id:
        raise RuntimeError("experiment id does not match frozen metadata")
    if document.get("run_order") != run_order:
        raise RuntimeError("experiment run order does not match P4-A")
    if document.get("frozen_context") != frozen_context:
        raise RuntimeError("current context does not match frozen experiment metadata")
    runs = document.get("runs")
    if not isinstance(runs, list):
        raise RuntimeError("invalid experiment run records")
    if any(not isinstance(run, dict) or run.get("status") != "completed" for run in runs):
        raise RuntimeError("previous experiment run is incomplete or failed")
    if len(runs) >= len(run_order):
        raise RuntimeError("paired experiment already has all planned runs")
    expected_mode = run_order[len(runs)]
    if session_mode != expected_mode:
        raise RuntimeError(
            f"next experiment run must be {expected_mode}, not {session_mode}"
        )

    run_index = len(runs)
    runs.append(
        {
            "finished_at": None,
            "manifest_path": None,
            "manifest_sha256": None,
            "requested_at": utc_now(),
            "run_id": run_id,
            "run_order_index": run_index + 1,
            "runs_root": str(runs_root),
            "session_mode": session_mode,
            "started_at": None,
            "status": "running",
        }
    )
    write_json(experiment_file, document)
    return (
        {
            "experiment_id": experiment_id,
            "frozen_at": document["frozen_at"],
            "frozen_context": frozen_context,
            "run_order": run_order,
            "run_order_index": run_index + 1,
        },
        run_index,
    )


def finalize_experiment(
    *, experiment_file: Path, run_index: int, manifest_path: Path
) -> None:
    document = json.loads(experiment_file.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run = document["runs"][run_index]
    if run.get("status") != "running":
        raise RuntimeError("experiment run record is not active")
    run.update(
        {
            "finished_at": manifest.get("finished_at"),
            "manifest_path": str(manifest_path),
            "manifest_sha256": sha256_file(manifest_path),
            "started_at": manifest.get("started_at"),
            "status": manifest.get("status"),
        }
    )
    write_json(experiment_file, document)


def compose_peer_prompt(prefix: bytes, peer_payload: bytes) -> Tuple[bytes, int]:
    """Append the peer payload without decoding, parsing, or rewriting it."""
    offset = len(prefix) + len(PEER_MARKER)
    prompt = prefix + PEER_MARKER + peer_payload
    if prompt[offset : offset + len(peer_payload)] != peer_payload:
        raise AssertionError("peer payload was not preserved verbatim")
    return prompt, offset


def extract_event_metadata(events_jsonl: bytes) -> Dict[str, Any]:
    """Extract control metadata without reading agent-message natural language."""
    thread_id: Optional[str] = None
    usage: Dict[str, Optional[Any]] = {field: None for field in USAGE_FIELDS}
    counts = {
        "blank_lines": 0,
        "irrelevant_json_events": 0,
        "malformed_json_lines": 0,
        "thread_started_events": 0,
        "turn_completed_events": 0,
        "usage_events": 0,
        "valid_json_lines": 0,
    }

    for raw_line in events_jsonl.splitlines():
        if not raw_line.strip():
            counts["blank_lines"] += 1
            continue
        try:
            event = json.loads(raw_line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            counts["malformed_json_lines"] += 1
            continue
        counts["valid_json_lines"] += 1
        if not isinstance(event, dict):
            counts["irrelevant_json_events"] += 1
            continue

        event_type = event.get("type")
        if event_type == "thread.started":
            counts["thread_started_events"] += 1
            candidate = event.get("thread_id")
            if isinstance(candidate, str) and candidate:
                thread_id = candidate
            continue

        if event_type == "turn.completed":
            counts["turn_completed_events"] += 1
            candidate_usage = event.get("usage")
            if isinstance(candidate_usage, dict):
                counts["usage_events"] += 1
                usage = {
                    field: (
                        candidate_usage[field]
                        if type(candidate_usage.get(field)) is int
                        and candidate_usage[field] >= 0
                        else None
                    )
                    for field in USAGE_FIELDS
                }
            continue

        counts["irrelevant_json_events"] += 1

    input_tokens = usage["input_tokens"]
    cached_input_tokens = usage["cached_input_tokens"]
    if input_tokens is not None and cached_input_tokens is not None:
        uncached_input_tokens: Optional[int] = input_tokens - cached_input_tokens
        cache_hit_ratio: Optional[float] = (
            round(cached_input_tokens / input_tokens, 6) if input_tokens > 0 else None
        )
    else:
        uncached_input_tokens = None
        cache_hit_ratio = None

    return {
        "cache_hit_ratio": cache_hit_ratio,
        "cache_write_input_tokens": usage["cache_write_input_tokens"],
        "cached_input_tokens": cached_input_tokens,
        "event_parse": counts,
        "input_tokens": input_tokens,
        "output_tokens": usage["output_tokens"],
        "reasoning_output_tokens": usage["reasoning_output_tokens"],
        "thread_id": thread_id,
        "uncached_input_tokens": uncached_input_tokens,
    }


def fenced_block(value: bytes) -> str:
    text = value.decode("utf-8")
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    ending = "" if text.endswith("\n") else "\n"
    return f"{fence}text\n{text}{ending}{fence}"


@dataclass
class TurnResult:
    number: int
    role: str
    turn_dir: Path
    final_message: bytes
    process: Dict[str, Any]

    @property
    def success(self) -> bool:
        return bool(self.process["success"])


def summarize_turns(turns: List[TurnResult]) -> Dict[str, Any]:
    total_fields = USAGE_FIELDS + ("uncached_input_tokens",)

    def total_if_complete(field: str) -> Optional[int]:
        values = [turn.process.get(field) for turn in turns]
        if not values or any(type(value) is not int for value in values):
            return None
        return sum(values)

    usage_totals = {field: total_if_complete(field) for field in total_fields}
    total_input = usage_totals["input_tokens"]
    total_cached = usage_totals["cached_input_tokens"]
    usage_totals["cache_hit_ratio"] = (
        round(total_cached / total_input, 6)
        if total_input is not None
        and total_cached is not None
        and total_input > 0
        else None
    )
    availability_fields = total_fields + ("cache_hit_ratio",)
    return {
        "duration_seconds": round(
            sum(float(turn.process["duration_seconds"]) for turn in turns), 3
        ),
        "successful_turns": sum(1 for turn in turns if turn.success),
        "thread_ids": [
            turn.process["thread_id"]
            for turn in turns
            if turn.process.get("thread_id") is not None
        ],
        "turn_count": len(turns),
        "usage_available_turns": {
            field: sum(
                1 for turn in turns if turn.process.get(field) is not None
            )
            for field in availability_fields
        },
        "usage_totals": usage_totals,
    }


def build_codex_command(
    *,
    codex_bin: str,
    repo_root: Path,
    final_path: Path,
    session_mode: str,
    resume_target_thread_id: Optional[str] = None,
) -> List[str]:
    if session_mode not in TURN_SESSION_MODES:
        raise ValueError(f"unknown turn session mode: {session_mode}")
    if session_mode == RESUME and not resume_target_thread_id:
        raise ValueError("resume requires an explicit target thread id")
    if session_mode != RESUME and resume_target_thread_id is not None:
        raise ValueError("resume target is only valid for a resume turn")

    command = [codex_bin, "exec"]
    if session_mode == FRESH_EPHEMERAL:
        command.append("--ephemeral")
    command.extend(
        [
            "--json",
            "--color",
            "never",
            "-c",
            'approval_policy="never"',
            "--sandbox",
            "read-only",
            "--cd",
            str(repo_root),
            "--output-last-message",
            str(final_path),
        ]
    )
    if session_mode == RESUME:
        command.extend(["resume", str(resume_target_thread_id), "-"])
    else:
        command.append("-")
    return command


def run_turn(
    *,
    run_root: Path,
    repo_root: Path,
    codex_bin: str,
    timeout_seconds: int,
    number: int,
    role: str,
    codex_home: Path,
    prompt: bytes,
    session_mode: str = FRESH_EPHEMERAL,
    resume_target_thread_id: Optional[str] = None,
    peer_payload: Optional[bytes] = None,
    peer_payload_offset: Optional[int] = None,
    peer_source: Optional[str] = None,
) -> TurnResult:
    turn_dir = run_root / f"turn-{number:02d}-{role}"
    turn_dir.mkdir(parents=True)

    prompt_path = turn_dir / "prompt.txt"
    events_path = turn_dir / "events.jsonl"
    stderr_path = turn_dir / "stderr.txt"
    final_path = turn_dir / "final.txt"
    process_path = turn_dir / "process.json"
    prompt_path.write_bytes(prompt)

    transport: Optional[Dict[str, Any]] = None
    if peer_payload is not None:
        if peer_payload_offset is None or peer_source is None:
            raise ValueError("peer payload metadata is incomplete")
        peer_path = turn_dir / "peer-payload.txt"
        peer_path.write_bytes(peer_payload)
        preserved = (
            peer_path.read_bytes() == peer_payload
            and prompt[
                peer_payload_offset : peer_payload_offset + len(peer_payload)
            ]
            == peer_payload
        )
        transport = {
            "byte_length": len(peer_payload),
            "peer_payload_path": relative_path(peer_path, run_root),
            "prompt_offset": peer_payload_offset,
            "preserved_verbatim": preserved,
            "sha256": sha256_bytes(peer_payload),
            "source_final_message": peer_source,
        }

    command = build_codex_command(
        codex_bin=codex_bin,
        repo_root=repo_root,
        final_path=final_path,
        session_mode=session_mode,
        resume_target_thread_id=resume_target_thread_id,
    )
    environment = os.environ.copy()
    environment["CODEX_HOME"] = str(codex_home)

    started_at = utc_now()
    started_monotonic = time.monotonic()
    exit_code: Optional[int] = None
    failure: Optional[str] = None
    stdout = b""
    stderr = b""

    try:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            env=environment,
            input=prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        failure = f"timeout after {timeout_seconds} seconds"
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
    except OSError as exc:
        failure = f"unable to launch Codex: {exc}"

    duration_seconds = round(time.monotonic() - started_monotonic, 3)
    events_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    event_metadata = extract_event_metadata(events_path.read_bytes())
    final_message = final_path.read_bytes() if final_path.is_file() else b""
    success = exit_code == 0 and bool(final_message)
    if not success and failure is None:
        failure = "Codex exited unsuccessfully or did not write a final message"

    observed_thread_id = event_metadata["thread_id"]
    created_thread_id = (
        observed_thread_id if session_mode == NEW_PERSISTENT else None
    )
    observed_resume_thread_id = (
        observed_thread_id if session_mode == RESUME else None
    )
    resume_relationship_verified: Optional[bool] = None
    if session_mode == NEW_PERSISTENT and created_thread_id is None:
        success = False
        failure = "persistent session did not provide a machine-readable thread id"
    if session_mode == RESUME:
        resume_relationship_verified = (
            observed_resume_thread_id is not None
            and observed_resume_thread_id == resume_target_thread_id
        )
        if not resume_relationship_verified:
            success = False
            relationship_failure = (
                "resume event did not prove the target thread relationship"
            )
            failure = (
                f"{failure}; {relationship_failure}"
                if failure is not None
                else relationship_failure
            )

    process: Dict[str, Any] = {
        "codex_home": str(codex_home),
        "created_thread_id": created_thread_id,
        "cache_hit_ratio": event_metadata["cache_hit_ratio"],
        "cache_write_input_tokens": event_metadata["cache_write_input_tokens"],
        "cached_input_tokens": event_metadata["cached_input_tokens"],
        "command": command,
        "duration_seconds": duration_seconds,
        "event_parse": event_metadata["event_parse"],
        "events_path": relative_path(events_path, run_root),
        "exit_code": exit_code,
        "failure": failure,
        "final_message_path": (
            relative_path(final_path, run_root) if final_path.is_file() else None
        ),
        "final_message_sha256": (
            sha256_bytes(final_message) if final_message else None
        ),
        "finished_at": utc_now(),
        "input_tokens": event_metadata["input_tokens"],
        "output_tokens": event_metadata["output_tokens"],
        "prompt_path": relative_path(prompt_path, run_root),
        "prompt_sha256": sha256_bytes(prompt),
        "role": role,
        "reasoning_output_tokens": event_metadata["reasoning_output_tokens"],
        "observed_resume_thread_id": observed_resume_thread_id,
        "resume_relationship_verified": resume_relationship_verified,
        "resume_target_thread_id": resume_target_thread_id,
        "sandbox": "read-only",
        "session_mode": session_mode,
        "started_at": started_at,
        "stderr_path": relative_path(stderr_path, run_root),
        "success": success,
        "thread_id": observed_thread_id,
        "transport": transport,
        "turn": number,
        "uncached_input_tokens": event_metadata["uncached_input_tokens"],
    }
    write_json(process_path, process)
    return TurnResult(number, role, turn_dir, final_message, process)


def write_manifest(
    run_root: Path,
    repo_root: Path,
    run_id: str,
    started_at: str,
    turns: List[TurnResult],
    status: str,
    run_session_mode: str,
    experiment: Optional[Dict[str, Any]] = None,
) -> None:
    transports = [
        turn.process["transport"]
        for turn in turns
        if turn.process["transport"] is not None
    ]
    manifest = {
        "experiment": experiment,
        "finished_at": utc_now() if status != "running" else None,
        "repo_root": str(repo_root),
        "run_id": run_id,
        "schema_version": 1,
        "session_mode": run_session_mode,
        "summary": summarize_turns(turns),
        "started_at": started_at,
        "status": status,
        "transports": transports,
        "turns": [turn.process for turn in turns],
    }
    write_json(run_root / "manifest.json", manifest)


def write_transcript(run_root: Path, run_id: str, turns: List[TurnResult]) -> None:
    summary = summarize_turns(turns)
    lines = [
        f"# 1PCloop transcript — {run_id}",
        "",
        "## Mechanical run summary",
        "",
        fenced_block(
            (
                json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n"
            ).encode("utf-8")
        ),
        "",
    ]
    for turn in turns:
        process = turn.process
        lines.extend(
            [
                f"## Turn {turn.number} — {turn.role}",
                "",
                f"- `CODEX_HOME`: `{process['codex_home']}`",
                f"- Exit code: `{process['exit_code']}`",
                f"- Success: `{str(process['success']).lower()}`",
                f"- Duration: `{process['duration_seconds']}` seconds",
                f"- Session mode: `{process['session_mode']}`",
                f"- Thread ID: `{process['thread_id']}`",
                f"- Created thread ID: `{process['created_thread_id']}`",
                f"- Resume target thread ID: `{process['resume_target_thread_id']}`",
                f"- Observed resume thread ID: `{process['observed_resume_thread_id']}`",
                f"- Resume relationship verified: `{process['resume_relationship_verified']}`",
                f"- Input tokens: `{process['input_tokens']}`",
                f"- Cached input tokens: `{process['cached_input_tokens']}`",
                f"- Uncached input tokens: `{process['uncached_input_tokens']}`",
                f"- Cache hit ratio: `{process['cache_hit_ratio']}`",
                f"- Output tokens: `{process['output_tokens']}`",
                f"- Reasoning output tokens: `{process['reasoning_output_tokens']}`",
                f"- Events: `{process['events_path']}`",
                f"- stderr: `{process['stderr_path']}`",
                "",
            ]
        )
        transport = process["transport"]
        if transport is not None:
            lines.extend(
                [
                    "### Deterministic transport",
                    "",
                    f"- Source: `{transport['source_final_message']}`",
                    f"- SHA-256: `{transport['sha256']}`",
                    f"- Bytes: `{transport['byte_length']}`",
                    f"- Preserved verbatim: `{str(transport['preserved_verbatim']).lower()}`",
                    "",
                ]
            )
        prompt = (turn.turn_dir / "prompt.txt").read_bytes()
        lines.extend(["### Prompt", "", fenced_block(prompt), ""])
        lines.extend(
            ["### Final response", "", fenced_block(turn.final_message), ""]
        )
        lines.extend(
            [
                "### Process result",
                "",
                fenced_block(
                    (
                        json.dumps(process, ensure_ascii=False, indent=2, sort_keys=True)
                        + "\n"
                    ).encode("utf-8")
                ),
                "",
            ]
        )
    (run_root / "transcript.md").write_text("\n".join(lines), encoding="utf-8")


def orchestrate(
    *,
    repo_root: Path,
    runs_root: Path,
    codex_bin: str,
    reviewer_home: Path,
    executor_home: Path,
    run_id: str,
    timeout_seconds: int,
    session_mode: str = CONTROL_MODE,
    experiment: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Path]:
    run_id = validate_run_id(run_id)
    if session_mode not in RUN_SESSION_MODES:
        raise ValueError(f"unknown run session mode: {session_mode}")
    run_root = runs_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    started_at = utc_now()
    turns: List[TurnResult] = []
    write_manifest(
        run_root,
        repo_root,
        run_id,
        started_at,
        turns,
        "running",
        session_mode,
        experiment,
    )

    reviewer_initial_mode = (
        FRESH_EPHEMERAL if session_mode == CONTROL_MODE else NEW_PERSISTENT
    )

    turn1 = run_turn(
        run_root=run_root,
        repo_root=repo_root,
        codex_bin=codex_bin,
        timeout_seconds=timeout_seconds,
        number=1,
        role="reviewer",
        codex_home=reviewer_home,
        prompt=read_role_prompt("reviewer-initial.md"),
        session_mode=reviewer_initial_mode,
    )
    turns.append(turn1)
    if not turn1.success:
        write_manifest(
            run_root,
            repo_root,
            run_id,
            started_at,
            turns,
            "failed",
            session_mode,
            experiment,
        )
        write_transcript(run_root, run_id, turns)
        return 1, run_root

    executor_prompt, executor_offset = compose_peer_prompt(
        read_role_prompt("executor.md"), turn1.final_message
    )
    turn2 = run_turn(
        run_root=run_root,
        repo_root=repo_root,
        codex_bin=codex_bin,
        timeout_seconds=timeout_seconds,
        number=2,
        role="executor",
        codex_home=executor_home,
        prompt=executor_prompt,
        session_mode=FRESH_EPHEMERAL,
        peer_payload=turn1.final_message,
        peer_payload_offset=executor_offset,
        peer_source=relative_path(turn1.turn_dir / "final.txt", run_root),
    )
    turns.append(turn2)
    if not turn2.success:
        write_manifest(
            run_root,
            repo_root,
            run_id,
            started_at,
            turns,
            "failed",
            session_mode,
            experiment,
        )
        write_transcript(run_root, run_id, turns)
        return 1, run_root

    review_prompt, review_offset = compose_peer_prompt(
        read_role_prompt("reviewer-review.md"), turn2.final_message
    )
    resume_target_thread_id = (
        turn1.process["created_thread_id"]
        if session_mode == TREATMENT_MODE
        else None
    )
    reviewer_review_mode = (
        FRESH_EPHEMERAL if session_mode == CONTROL_MODE else RESUME
    )
    turn3 = run_turn(
        run_root=run_root,
        repo_root=repo_root,
        codex_bin=codex_bin,
        timeout_seconds=timeout_seconds,
        number=3,
        role="reviewer",
        codex_home=reviewer_home,
        prompt=review_prompt,
        session_mode=reviewer_review_mode,
        resume_target_thread_id=resume_target_thread_id,
        peer_payload=turn2.final_message,
        peer_payload_offset=review_offset,
        peer_source=relative_path(turn2.turn_dir / "final.txt", run_root),
    )
    turns.append(turn3)

    status = "completed" if turn3.success else "failed"
    write_manifest(
        run_root,
        repo_root,
        run_id,
        started_at,
        turns,
        status,
        session_mode,
        experiment,
    )
    write_transcript(run_root, run_id, turns)
    return (0 if status == "completed" else 1), run_root


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--reviewer-home", type=Path, default=DEFAULT_REVIEWER_HOME)
    parser.add_argument("--executor-home", type=Path, default=DEFAULT_EXECUTOR_HOME)
    parser.add_argument("--run-id", default=default_run_id())
    parser.add_argument(
        "--session-mode", choices=RUN_SESSION_MODES, default=CONTROL_MODE
    )
    parser.add_argument("--experiment-file", type=Path)
    parser.add_argument("--experiment-id")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--codex-bin", default=shutil.which("codex") or "codex")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.timeout_seconds <= 0:
        raise SystemExit("--timeout-seconds must be positive")
    for label, path in (
        ("repo root", args.repo_root),
        ("reviewer CODEX_HOME", args.reviewer_home),
        ("executor CODEX_HOME", args.executor_home),
    ):
        if not path.is_dir():
            raise SystemExit(f"{label} does not exist: {path}")
    if (args.experiment_file is None) != (args.experiment_id is None):
        raise SystemExit("--experiment-file and --experiment-id must be used together")
    if args.session_mode == TREATMENT_MODE and args.experiment_file is None:
        raise SystemExit("reviewer-resume treatment requires frozen experiment metadata")

    repo_root = args.repo_root.resolve()
    runs_root = args.runs_root.resolve()
    reviewer_home = args.reviewer_home.resolve()
    executor_home = args.executor_home.resolve()
    experiment: Optional[Dict[str, Any]] = None
    experiment_run_index: Optional[int] = None
    experiment_file: Optional[Path] = None
    if args.experiment_file is not None:
        experiment_file = args.experiment_file.resolve()
        if path_is_within(runs_root, repo_root):
            raise SystemExit("paired experiment runs root must be outside the repository")
        if path_is_within(experiment_file, repo_root):
            raise SystemExit("paired experiment metadata must be outside the repository")
        frozen_context = capture_frozen_context(
            repo_root=repo_root,
            codex_bin=args.codex_bin,
            reviewer_home=reviewer_home,
            executor_home=executor_home,
        )
        experiment, experiment_run_index = prepare_experiment(
            experiment_file=experiment_file,
            experiment_id=args.experiment_id,
            session_mode=args.session_mode,
            run_id=args.run_id,
            runs_root=runs_root,
            frozen_context=frozen_context,
        )
    exit_code, run_root = orchestrate(
        repo_root=repo_root,
        runs_root=runs_root,
        codex_bin=args.codex_bin,
        reviewer_home=reviewer_home,
        executor_home=executor_home,
        run_id=args.run_id,
        timeout_seconds=args.timeout_seconds,
        session_mode=args.session_mode,
        experiment=experiment,
    )
    if experiment_file is not None and experiment_run_index is not None:
        finalize_experiment(
            experiment_file=experiment_file,
            run_index=experiment_run_index,
            manifest_path=run_root / "manifest.json",
        )
    print(run_root)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
