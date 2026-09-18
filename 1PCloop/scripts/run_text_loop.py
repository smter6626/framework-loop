#!/usr/bin/env python3
"""Run the minimal Reviewer -> Executor -> Reviewer Codex transport loop."""

from __future__ import annotations

import argparse
import copy
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
DEFAULT_RUNS_ROOT = ACTIVE_ROOT / "runs"
DEFAULT_REVIEWER_HOME = Path.home() / ".codex-mix/.mix/runtimes/1pcloop-reviewer"
DEFAULT_EXECUTOR_HOME = Path.home() / ".codex-mix/.mix/runtimes/1pcloop-executor"
RETIRED_CODEX_HOMES = (Path.home() / ".codex-A", Path.home() / ".codex-B")
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
STATIC_RELATIVE_PATH = Path("1PCloop/docs/miniloop_static.md")
RUNTIME_RELATIVE_PATH = Path("1PCloop/docs/miniloop_runtime.md")
AUTHORITATIVE_CONTEXT_MARKER = (
    b"\n\n--- BEGIN DETERMINISTIC AUTHORITATIVE CONTEXT ---\n"
)
AUTHORITATIVE_CONTEXT_END_MARKER = (
    b"\n--- END DETERMINISTIC AUTHORITATIVE CONTEXT ---\n"
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


def read_role_prompt(filename: str, *, repo_root: Path = REPO_ROOT) -> bytes:
    path = repo_root / "1PCloop/roles" / filename
    if not path.is_file():
        raise RuntimeError(f"required role prompt is missing: {path}")
    return path.read_bytes()


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


def count_lines(value: bytes) -> int:
    """Count logical lines without decoding governance content."""
    if not value:
        return 0
    return value.count(b"\n") + (0 if value.endswith(b"\n") else 1)


@dataclass(frozen=True)
class AuthoritativeDocument:
    name: str
    relative_path: str
    absolute_path: Path
    content: bytes
    sha256: str
    byte_length: int
    line_count: int

    def metadata(self) -> Dict[str, Any]:
        return {
            "path": self.relative_path,
            "sha256": self.sha256,
            "bytes": self.byte_length,
            "lines": self.line_count,
        }


@dataclass(frozen=True)
class AuthoritativeSnapshot:
    git_head: str
    static: AuthoritativeDocument
    runtime: AuthoritativeDocument

    def hashes(self) -> Dict[str, str]:
        return {
            "static_sha256": self.static.sha256,
            "runtime_sha256": self.runtime.sha256,
        }


@dataclass(frozen=True)
class AuthoritativePrompt:
    prompt: bytes
    payload: bytes
    payload_offset: int
    evidence: Dict[str, Any]
    snapshot: AuthoritativeSnapshot
    document_offsets: Dict[str, int]


def read_authoritative_document(
    *, repo_root: Path, name: str, relative: Path
) -> AuthoritativeDocument:
    path = repo_root / relative
    if not path.is_file():
        raise RuntimeError(f"required governance file is missing: {path}")
    content = path.read_bytes()
    return AuthoritativeDocument(
        name=name,
        relative_path=relative.as_posix(),
        absolute_path=path,
        content=content,
        sha256=sha256_bytes(content),
        byte_length=len(content),
        line_count=count_lines(content),
    )


def read_authoritative_snapshot(repo_root: Path) -> AuthoritativeSnapshot:
    """Read complete governance bytes and bind them to one Git HEAD."""
    git_head_before = command_stdout(["git", "rev-parse", "HEAD"], cwd=repo_root)
    static = read_authoritative_document(
        repo_root=repo_root, name="static", relative=STATIC_RELATIVE_PATH
    )
    runtime = read_authoritative_document(
        repo_root=repo_root, name="runtime", relative=RUNTIME_RELATIVE_PATH
    )
    git_head_after = command_stdout(["git", "rev-parse", "HEAD"], cwd=repo_root)
    if git_head_before != git_head_after:
        raise RuntimeError("Git HEAD changed while governance context was captured")
    return AuthoritativeSnapshot(
        git_head=git_head_before,
        static=static,
        runtime=runtime,
    )


def reviewer_context_policy(
    *,
    current: AuthoritativeSnapshot,
    session_known: Optional[AuthoritativeSnapshot],
    fresh_reason: str,
) -> Dict[str, Any]:
    """Choose a byte-injection policy using hashes, never document semantics."""
    if session_known is None:
        return {
            "bootstrap_performed": True,
            "bootstrap_required": True,
            "fresh_reason": fresh_reason,
            "injected_files": ["static", "runtime"],
            "injection_mode": "full-bootstrap",
            "refresh_performed": False,
            "refresh_required": False,
            "rollover_performed": False,
            "rollover_required": False,
        }
    if session_known.static.sha256 != current.static.sha256:
        return {
            "bootstrap_performed": True,
            "bootstrap_required": True,
            "fresh_reason": "static-hash-changed",
            "injected_files": ["static", "runtime"],
            "injection_mode": "full-rebootstrap-static-change",
            "refresh_performed": True,
            "refresh_required": True,
            "rollover_performed": True,
            "rollover_required": True,
        }
    if session_known.runtime.sha256 != current.runtime.sha256:
        return {
            "bootstrap_performed": False,
            "bootstrap_required": False,
            "fresh_reason": None,
            "injected_files": ["runtime"],
            "injection_mode": "runtime-refresh",
            "refresh_performed": True,
            "refresh_required": True,
            "rollover_performed": False,
            "rollover_required": False,
        }
    return {
        "bootstrap_performed": False,
        "bootstrap_required": False,
        "fresh_reason": None,
        "injected_files": [],
        "injection_mode": "resume-unchanged",
        "refresh_performed": False,
        "refresh_required": False,
        "rollover_performed": False,
        "rollover_required": False,
    }


def build_authoritative_prompt(
    *,
    role_prompt: bytes,
    current: AuthoritativeSnapshot,
    session_known: Optional[AuthoritativeSnapshot],
    fresh_reason: str,
    peer_payload: Optional[bytes] = None,
) -> Tuple[AuthoritativePrompt, Optional[int]]:
    """Build a deterministic context envelope with exact document byte ranges."""
    policy = reviewer_context_policy(
        current=current,
        session_known=session_known,
        fresh_reason=fresh_reason,
    )
    control_metadata = {
        "bootstrap_performed": policy["bootstrap_performed"],
        "bootstrap_required": policy["bootstrap_required"],
        "current_git_head": current.git_head,
        "current_hashes": current.hashes(),
        "fresh_reason": policy["fresh_reason"],
        "injected_files": policy["injected_files"],
        "injection_mode": policy["injection_mode"],
        "refresh_performed": policy["refresh_performed"],
        "refresh_required": policy["refresh_required"],
        "rollover_performed": policy["rollover_performed"],
        "rollover_required": policy["rollover_required"],
        "schema_version": 1,
        "session_known_git_head": (
            session_known.git_head if session_known is not None else None
        ),
        "session_known_hashes": (
            session_known.hashes() if session_known is not None else None
        ),
        "static": current.static.metadata(),
        "runtime": current.runtime.metadata(),
    }
    payload_parts = [
        AUTHORITATIVE_CONTEXT_MARKER,
        json.dumps(
            control_metadata,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8"),
        b"\n",
    ]
    document_payload_offsets: Dict[str, int] = {}
    documents = {"static": current.static, "runtime": current.runtime}
    for name in policy["injected_files"]:
        document = documents[name]
        payload_parts.append(
            f"--- BEGIN COMPLETE {name.upper()} BYTES ---\n".encode("ascii")
        )
        document_payload_offsets[name] = sum(len(part) for part in payload_parts)
        payload_parts.append(document.content)
        if document.content and not document.content.endswith(b"\n"):
            payload_parts.append(b"\n")
        payload_parts.append(
            f"--- END COMPLETE {name.upper()} BYTES ---\n".encode("ascii")
        )
    payload_parts.append(AUTHORITATIVE_CONTEXT_END_MARKER)
    payload = b"".join(payload_parts)
    payload_offset = len(role_prompt)
    prompt = role_prompt + payload
    document_offsets = {
        name: payload_offset + offset
        for name, offset in document_payload_offsets.items()
    }
    peer_payload_offset: Optional[int] = None
    if peer_payload is not None:
        prompt, peer_payload_offset = compose_peer_prompt(prompt, peer_payload)

    evidence = {
        **control_metadata,
        "authoritative_payload_bytes": len(payload),
        "authoritative_payload_offset": payload_offset,
        "authoritative_payload_sha256": sha256_bytes(payload),
        "document_prompt_offsets": document_offsets,
        "prompt_bytes": len(prompt),
        "prompt_sha256": sha256_bytes(prompt),
        "validation": {
            "failure": None,
            "performed_before_launch": False,
            "prompt_bytes_verified": False,
            "source_bytes_verified": False,
        },
    }
    return (
        AuthoritativePrompt(
            prompt=prompt,
            payload=payload,
            payload_offset=payload_offset,
            evidence=evidence,
            snapshot=current,
            document_offsets=document_offsets,
        ),
        peer_payload_offset,
    )


def validate_authoritative_prompt(authoritative: AuthoritativePrompt) -> None:
    """Fail closed unless source, metadata, payload, and prompt bytes agree."""
    evidence = authoritative.evidence
    if sha256_bytes(authoritative.prompt) != evidence.get("prompt_sha256"):
        raise RuntimeError("authoritative prompt hash mismatch")
    payload_offset = authoritative.payload_offset
    payload_end = payload_offset + len(authoritative.payload)
    if authoritative.prompt[payload_offset:payload_end] != authoritative.payload:
        raise RuntimeError("authoritative payload does not match prompt bytes")
    if sha256_bytes(authoritative.payload) != evidence.get(
        "authoritative_payload_sha256"
    ):
        raise RuntimeError("authoritative payload hash mismatch")

    documents = {
        "static": authoritative.snapshot.static,
        "runtime": authoritative.snapshot.runtime,
    }
    injected_files = evidence.get("injected_files")
    if set(authoritative.document_offsets) != set(injected_files or []):
        raise RuntimeError("authoritative injected-file metadata mismatch")
    for name, document in documents.items():
        content = document.absolute_path.read_bytes() if document.absolute_path.is_file() else None
        if content != document.content:
            raise RuntimeError(f"{name} governance bytes changed before launch")
        if document.sha256 != sha256_bytes(document.content):
            raise RuntimeError(f"{name} governance SHA-256 mismatch")
        if document.byte_length != len(document.content):
            raise RuntimeError(f"{name} governance byte-length mismatch")
        if document.line_count != count_lines(document.content):
            raise RuntimeError(f"{name} governance line-count mismatch")
        if name in authoritative.document_offsets:
            offset = authoritative.document_offsets[name]
            if authoritative.prompt[offset : offset + len(document.content)] != document.content:
                raise RuntimeError(f"{name} governance prompt-byte mismatch")


def extract_event_metadata(events_jsonl: bytes) -> Dict[str, Any]:
    """Extract control metadata without reading agent-message natural language."""
    thread_id: Optional[str] = None
    usage: Dict[str, Optional[Any]] = {field: None for field in USAGE_FIELDS}
    counts = {
        "ambiguous_usage_events": 0,
        "blank_lines": 0,
        "invalid_cached_input_relationships": 0,
        "irrelevant_json_events": 0,
        "malformed_json_lines": 0,
        "thread_started_events": 0,
        "turn_completed_events": 0,
        "usage_events": 0,
        "valid_json_lines": 0,
    }
    usage_candidates: List[Dict[str, Optional[Any]]] = []

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
                usage_candidates.append({
                    field: (
                        candidate_usage[field]
                        if type(candidate_usage.get(field)) is int
                        and candidate_usage[field] >= 0
                        else None
                    )
                    for field in USAGE_FIELDS
                })
            continue

        counts["irrelevant_json_events"] += 1

    if len(usage_candidates) == 1:
        usage = usage_candidates[0]
    elif len(usage_candidates) > 1:
        # Event order does not establish which completion record is authoritative.
        # Telemetry must be unavailable rather than silently selecting one record.
        counts["ambiguous_usage_events"] = len(usage_candidates) - 1
    input_tokens = usage["input_tokens"]
    cached_input_tokens = usage["cached_input_tokens"]
    if input_tokens is not None and cached_input_tokens is not None:
        if cached_input_tokens > input_tokens:
            # Do not emit impossible negative uncached tokens.  Preserve unrelated
            # output metrics, but mark cache-derived telemetry unavailable.
            counts["invalid_cached_input_relationships"] = 1
            input_tokens = None
            cached_input_tokens = None
            uncached_input_tokens = None
            cache_hit_ratio = None
        else:
            uncached_input_tokens = input_tokens - cached_input_tokens
            cache_hit_ratio = (
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
    authoritative_context: Optional[AuthoritativePrompt] = None,
) -> TurnResult:
    turn_dir = run_root / f"turn-{number:02d}-{role}"
    turn_dir.mkdir(parents=True)

    prompt_path = turn_dir / "prompt.txt"
    events_path = turn_dir / "events.jsonl"
    stderr_path = turn_dir / "stderr.txt"
    final_path = turn_dir / "final.txt"
    process_path = turn_dir / "process.json"
    prompt_path.write_bytes(prompt)

    authoritative_evidence: Optional[Dict[str, Any]] = None
    authoritative_failure: Optional[str] = None
    if authoritative_context is not None:
        authoritative_evidence = copy.deepcopy(authoritative_context.evidence)
        try:
            if prompt != authoritative_context.prompt:
                raise RuntimeError("turn prompt differs from authoritative prompt")
            validate_authoritative_prompt(authoritative_context)
        except (OSError, RuntimeError) as exc:
            authoritative_failure = str(exc)
            authoritative_evidence["validation"] = {
                "failure": authoritative_failure,
                "performed_before_launch": True,
                "prompt_bytes_verified": False,
                "source_bytes_verified": False,
            }
        else:
            authoritative_evidence["validation"] = {
                "failure": None,
                "performed_before_launch": True,
                "prompt_bytes_verified": True,
                "source_bytes_verified": True,
            }

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
    environment["CODEX_SQLITE_HOME"] = str(codex_home)

    started_at = utc_now()
    started_monotonic = time.monotonic()
    exit_code: Optional[int] = None
    failure: Optional[str] = (
        f"authoritative-context validation failed: {authoritative_failure}"
        if authoritative_failure is not None
        else None
    )
    stdout = b""
    stderr = b""

    if authoritative_failure is None:
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
        "authoritative_context": authoritative_evidence,
        "codex_home": str(codex_home),
        "codex_sqlite_home": str(codex_home),
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
    failure: Optional[str] = None,
) -> None:
    transports = [
        turn.process["transport"]
        for turn in turns
        if turn.process["transport"] is not None
    ]
    manifest = {
        "experiment": experiment,
        "failure": failure,
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

    try:
        reviewer_session_context = read_authoritative_snapshot(repo_root)
    except (OSError, RuntimeError) as exc:
        failure = f"authoritative-context bootstrap failed: {exc}"
        write_manifest(
            run_root,
            repo_root,
            run_id,
            started_at,
            turns,
            "failed",
            session_mode,
            experiment,
            failure=failure,
        )
        write_transcript(run_root, run_id, turns)
        return 1, run_root

    reviewer_initial_mode = (
        FRESH_EPHEMERAL if session_mode == CONTROL_MODE else NEW_PERSISTENT
    )
    reviewer_initial_context, _ = build_authoritative_prompt(
        role_prompt=read_role_prompt("reviewer-initial.md", repo_root=repo_root),
        current=reviewer_session_context,
        session_known=None,
        fresh_reason="reviewer-initial-thread",
    )

    turn1 = run_turn(
        run_root=run_root,
        repo_root=repo_root,
        codex_bin=codex_bin,
        timeout_seconds=timeout_seconds,
        number=1,
        role="reviewer",
        codex_home=reviewer_home,
        prompt=reviewer_initial_context.prompt,
        session_mode=reviewer_initial_mode,
        authoritative_context=reviewer_initial_context,
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
        read_role_prompt("executor.md", repo_root=repo_root), turn1.final_message
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

    try:
        current_reviewer_context = read_authoritative_snapshot(repo_root)
    except (OSError, RuntimeError) as exc:
        failure = f"authoritative-context freshness check failed: {exc}"
        write_manifest(
            run_root,
            repo_root,
            run_id,
            started_at,
            turns,
            "failed",
            session_mode,
            experiment,
            failure=failure,
        )
        write_transcript(run_root, run_id, turns)
        return 1, run_root

    session_known_context = (
        reviewer_session_context if session_mode == TREATMENT_MODE else None
    )
    reviewer_review_context, review_offset = build_authoritative_prompt(
        role_prompt=read_role_prompt("reviewer-review.md", repo_root=repo_root),
        current=current_reviewer_context,
        session_known=session_known_context,
        fresh_reason="reviewer-review-fresh-thread",
        peer_payload=turn2.final_message,
    )
    if session_mode == CONTROL_MODE:
        reviewer_review_mode = FRESH_EPHEMERAL
        resume_target_thread_id = None
    elif reviewer_review_context.evidence["rollover_required"]:
        reviewer_review_mode = NEW_PERSISTENT
        resume_target_thread_id = None
    else:
        reviewer_review_mode = RESUME
        resume_target_thread_id = turn1.process["created_thread_id"]
    if review_offset is None:
        raise AssertionError("reviewer peer payload offset was not constructed")
    turn3 = run_turn(
        run_root=run_root,
        repo_root=repo_root,
        codex_bin=codex_bin,
        timeout_seconds=timeout_seconds,
        number=3,
        role="reviewer",
        codex_home=reviewer_home,
        prompt=reviewer_review_context.prompt,
        session_mode=reviewer_review_mode,
        resume_target_thread_id=resume_target_thread_id,
        peer_payload=turn2.final_message,
        peer_payload_offset=review_offset,
        peer_source=relative_path(turn2.turn_dir / "final.txt", run_root),
        authoritative_context=reviewer_review_context,
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
    repo_root = args.repo_root.resolve()
    runs_root = args.runs_root.resolve()
    reviewer_home = args.reviewer_home.resolve()
    executor_home = args.executor_home.resolve()
    if reviewer_home == executor_home:
        raise SystemExit("Reviewer and Executor profiles must be distinct")
    for role, selected in (("Reviewer", reviewer_home), ("Executor", executor_home)):
        if any(
            selected == retired.resolve() or retired.resolve() in selected.parents
            for retired in RETIRED_CODEX_HOMES
        ):
            raise SystemExit(
                f"{role} CODEX_HOME resolves inside a retired account home"
            )
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
