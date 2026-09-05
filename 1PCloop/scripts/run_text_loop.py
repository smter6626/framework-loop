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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def read_role_prompt(filename: str) -> bytes:
    return (ROLES_ROOT / filename).read_bytes()


def compose_peer_prompt(prefix: bytes, peer_payload: bytes) -> Tuple[bytes, int]:
    """Append the peer payload without decoding, parsing, or rewriting it."""
    offset = len(prefix) + len(PEER_MARKER)
    prompt = prefix + PEER_MARKER + peer_payload
    if prompt[offset : offset + len(peer_payload)] != peer_payload:
        raise AssertionError("peer payload was not preserved verbatim")
    return prompt, offset


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

    command = [
        codex_bin,
        "exec",
        "--ephemeral",
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
        "-",
    ]
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
    final_message = final_path.read_bytes() if final_path.is_file() else b""
    success = exit_code == 0 and bool(final_message)
    if not success and failure is None:
        failure = "Codex exited unsuccessfully or did not write a final message"

    process: Dict[str, Any] = {
        "codex_home": str(codex_home),
        "command": command,
        "duration_seconds": duration_seconds,
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
        "prompt_path": relative_path(prompt_path, run_root),
        "prompt_sha256": sha256_bytes(prompt),
        "role": role,
        "sandbox": "read-only",
        "started_at": started_at,
        "stderr_path": relative_path(stderr_path, run_root),
        "success": success,
        "transport": transport,
        "turn": number,
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
) -> None:
    transports = [
        turn.process["transport"]
        for turn in turns
        if turn.process["transport"] is not None
    ]
    manifest = {
        "finished_at": utc_now() if status != "running" else None,
        "repo_root": str(repo_root),
        "run_id": run_id,
        "schema_version": 1,
        "started_at": started_at,
        "status": status,
        "transports": transports,
        "turns": [turn.process for turn in turns],
    }
    write_json(run_root / "manifest.json", manifest)


def write_transcript(run_root: Path, run_id: str, turns: List[TurnResult]) -> None:
    lines = [f"# 1PCloop transcript — {run_id}", ""]
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
) -> Tuple[int, Path]:
    run_id = validate_run_id(run_id)
    run_root = runs_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    started_at = utc_now()
    turns: List[TurnResult] = []
    write_manifest(run_root, repo_root, run_id, started_at, turns, "running")

    turn1 = run_turn(
        run_root=run_root,
        repo_root=repo_root,
        codex_bin=codex_bin,
        timeout_seconds=timeout_seconds,
        number=1,
        role="reviewer",
        codex_home=reviewer_home,
        prompt=read_role_prompt("reviewer-initial.md"),
    )
    turns.append(turn1)
    if not turn1.success:
        write_manifest(run_root, repo_root, run_id, started_at, turns, "failed")
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
        peer_payload=turn1.final_message,
        peer_payload_offset=executor_offset,
        peer_source=relative_path(turn1.turn_dir / "final.txt", run_root),
    )
    turns.append(turn2)
    if not turn2.success:
        write_manifest(run_root, repo_root, run_id, started_at, turns, "failed")
        write_transcript(run_root, run_id, turns)
        return 1, run_root

    review_prompt, review_offset = compose_peer_prompt(
        read_role_prompt("reviewer-review.md"), turn2.final_message
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
        peer_payload=turn2.final_message,
        peer_payload_offset=review_offset,
        peer_source=relative_path(turn2.turn_dir / "final.txt", run_root),
    )
    turns.append(turn3)

    status = "completed" if turn3.success else "failed"
    write_manifest(run_root, repo_root, run_id, started_at, turns, status)
    write_transcript(run_root, run_id, turns)
    return (0 if status == "completed" else 1), run_root


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--reviewer-home", type=Path, default=DEFAULT_REVIEWER_HOME)
    parser.add_argument("--executor-home", type=Path, default=DEFAULT_EXECUTOR_HOME)
    parser.add_argument("--run-id", default=default_run_id())
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
    exit_code, run_root = orchestrate(
        repo_root=args.repo_root.resolve(),
        runs_root=args.runs_root.resolve(),
        codex_bin=args.codex_bin,
        reviewer_home=args.reviewer_home.resolve(),
        executor_home=args.executor_home.resolve(),
        run_id=args.run_id,
        timeout_seconds=args.timeout_seconds,
    )
    print(run_root)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
