#!/usr/bin/env python3
"""Deterministic P6.3 summary, framework commit, and push helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


SUMMARY_BEGIN = "<!-- 1PCLOOP_SUMMARY_ENTRY_BEGIN "
SUMMARY_END = "<!-- 1PCLOOP_SUMMARY_ENTRY_END "


class EvidenceError(RuntimeError):
    """P6.3 evidence state cannot be reconciled mechanically."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_bytes(repo: Path, arguments: Sequence[str], *, check: bool = True) -> bytes:
    completed = subprocess.run(
        ["git", *arguments], cwd=str(repo), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode(
            "utf-8", errors="replace"
        ).strip()
        raise EvidenceError(
            f"framework git {' '.join(arguments)} failed "
            f"({completed.returncode}): {detail}"
        )
    return completed.stdout


def git_text(repo: Path, arguments: Sequence[str]) -> str:
    return git_bytes(repo, arguments).decode("utf-8", errors="replace").strip()


def safe_json_bytes(value: Any) -> bytes:
    """Encode JSON for Markdown without allowing fence or marker injection."""
    rendered = json.dumps(
        value, ensure_ascii=False, indent=2, sort_keys=True
    ).replace("`", "\\u0060").replace("<", "\\u003c").replace(">", "\\u003e")
    return rendered.encode("utf-8")


def summary_header(run_id: str, run_root: Path) -> bytes:
    metadata = safe_json_bytes({
        "local_raw_evidence_root": str(run_root.resolve()),
        "run_id": run_id,
        "schema_version": 1,
    })
    return b"# 1PCloop Evidence Summary\n\n```json\n" + metadata + b"\n```\n"


def _relative_turn(turn_dir: Path, run_root: Path) -> str:
    try:
        return turn_dir.resolve().relative_to(run_root.resolve()).as_posix()
    except ValueError as exc:
        raise EvidenceError("turn directory escapes the local run root") from exc


def _raw_artifacts(turn_dir: Path) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for name in (
        "prompt.txt", "events.jsonl", "stderr.txt", "process.json",
        "final.txt", "peer-payload.txt",
    ):
        path = turn_dir / name
        if path.is_file() and not path.is_symlink():
            content = path.read_bytes()
            result.append({
                "bytes": len(content),
                "locator": str(path.resolve()),
                "name": name,
                "sha256": sha256_bytes(content),
            })
    return result


def build_turn_entry(
    *,
    run_id: str,
    run_root: Path,
    cycle_number: int,
    turn_dir: Path,
    process: Mapping[str, Any],
    structured_payload: Optional[Mapping[str, Any]],
    target_before: Optional[Mapping[str, Any]],
    target_after: Optional[Mapping[str, Any]],
    governance_hashes: Optional[Mapping[str, str]],
) -> Dict[str, Any]:
    """Build bounded metadata; never copy prompt, peer_message, or raw bodies."""
    turn_relative = _relative_turn(turn_dir, run_root)
    final_sha = process.get("final_message_sha256")
    process_path = turn_dir / "process.json"
    if not process_path.is_file():
        raise EvidenceError("turn process evidence is missing")
    identity = safe_json_bytes({
        "final_sha256": final_sha,
        "message_type": process.get("output_schema"),
        "process_sha256": sha256_file(process_path),
        "run_id": run_id,
        "turn": turn_relative,
    })
    entry_id = sha256_bytes(identity)
    valid_summary = (
        structured_payload is not None
        and isinstance(structured_payload.get("evidence_summary"), str)
        and bool(structured_payload["evidence_summary"].strip())
    )
    entry: Dict[str, Any] = {
        "cycle": cycle_number,
        "entry_id": entry_id,
        "failure": process.get("failure"),
        "finished_at": process.get("finished_at"),
        "governance_hashes": dict(governance_hashes or {}),
        "llm_evidence_summary": (
            {"status": "available", "text": structured_payload["evidence_summary"]}
            if valid_summary else {"status": "invalid_or_unavailable"}
        ),
        "local_raw_evidence_root": str(run_root.resolve()),
        "message_type": process.get("output_schema"),
        "raw_artifacts": _raw_artifacts(turn_dir),
        "role": process.get("role"),
        "run_id": run_id,
        "schema_version": 1,
        "started_at": process.get("started_at"),
        "success": bool(process.get("success")),
        "target_after": dict(target_after) if target_after is not None else None,
        "target_before": dict(target_before) if target_before is not None else None,
        "turn": turn_relative,
    }
    if structured_payload is not None and process.get("output_schema") == "reviewer_verdict":
        entry["reviewer_verdict"] = structured_payload.get("verdict")
        evidence = structured_payload.get("evidence")
        if isinstance(evidence, list):
            entry["structured_evidence"] = evidence
            tests = [item for item in evidence if item.get("kind") == "test"]
            if tests:
                entry["tests"] = tests
    return entry


def encode_entry(entry: Mapping[str, Any]) -> bytes:
    entry_id = entry.get("entry_id")
    if not isinstance(entry_id, str) or re.fullmatch(r"[0-9a-f]{64}", entry_id) is None:
        raise EvidenceError("summary entry ID is invalid")
    return (
        f"\n{SUMMARY_BEGIN}{entry_id} -->\n```json\n".encode("ascii")
        + safe_json_bytes(entry)
        + f"\n```\n{SUMMARY_END}{entry_id} -->\n".encode("ascii")
    )


def expected_summary_bytes(
    run_id: str, run_root: Path, progress: Sequence[Mapping[str, Any]]
) -> bytes:
    content = bytearray(summary_header(run_id, run_root))
    prior_sha = sha256_bytes(bytes(content))
    seen = set()
    for record in progress:
        try:
            entry_id = record["entry_id"]
            entry = bytes.fromhex(record["entry_hex"])
        except (KeyError, TypeError, ValueError) as exc:
            raise EvidenceError("summary progress record is invalid") from exc
        if entry_id in seen:
            raise EvidenceError("summary progress repeats an entry ID")
        if record.get("preimage_sha256") != prior_sha:
            raise EvidenceError("summary progress preimage chain is invalid")
        if record.get("entry_sha256") != sha256_bytes(entry):
            raise EvidenceError("summary progress entry hash mismatch")
        content.extend(entry)
        prior_sha = sha256_bytes(bytes(content))
        if record.get("postimage_sha256") != prior_sha:
            raise EvidenceError("summary progress postimage chain is invalid")
        seen.add(entry_id)
    return bytes(content)


def _entry_from_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    try:
        block = bytes.fromhex(record["entry_hex"])
        body = block.split(b"```json\n", 1)[1].split(b"\n```", 1)[0]
        value = json.loads(body)
    except (KeyError, TypeError, ValueError, IndexError, json.JSONDecodeError) as exc:
        raise EvidenceError("summary entry payload is invalid") from exc
    if not isinstance(value, dict) or value.get("entry_id") != record.get("entry_id"):
        raise EvidenceError("summary entry payload does not match its checkpoint ID")
    return value


def validate_summary_artifacts(
    *, run_id: str, run_root: Path, progress: Sequence[Mapping[str, Any]]
) -> None:
    run_root = run_root.resolve()
    for record in progress:
        entry = _entry_from_record(record)
        if entry.get("run_id") != run_id or entry.get("local_raw_evidence_root") != str(run_root):
            raise EvidenceError("summary entry run identity is stale")
        artifacts = entry.get("raw_artifacts")
        if not isinstance(artifacts, list):
            raise EvidenceError("summary entry raw artifact list is invalid")
        by_name: Dict[str, Mapping[str, Any]] = {}
        for artifact in artifacts:
            if not isinstance(artifact, dict) or not isinstance(artifact.get("name"), str):
                raise EvidenceError("summary raw artifact metadata is invalid")
            path = Path(artifact.get("locator", "")).resolve()
            try:
                path.relative_to(run_root)
            except ValueError as exc:
                raise EvidenceError("summary raw artifact escapes the run root") from exc
            if not path.is_file() or path.is_symlink():
                raise EvidenceError("summary raw artifact is missing or aliased")
            content = path.read_bytes()
            if artifact.get("bytes") != len(content) or artifact.get("sha256") != sha256_bytes(content):
                raise EvidenceError("summary raw artifact hash/length mismatch")
            by_name[artifact["name"]] = artifact
        process = by_name.get("process.json")
        if process is None:
            raise EvidenceError("summary entry lacks process evidence")
        final = by_name.get("final.txt")
        identity = safe_json_bytes({
            "final_sha256": final.get("sha256") if final is not None else None,
            "message_type": entry.get("message_type"),
            "process_sha256": process["sha256"],
            "run_id": run_id,
            "turn": entry.get("turn"),
        })
        if sha256_bytes(identity) != entry.get("entry_id"):
            raise EvidenceError("summary entry deterministic ID mismatch")


def validate_summary_file(
    *, summary_path: Path, run_id: str, run_root: Path,
    progress: Sequence[Mapping[str, Any]],
) -> bytes:
    expected = expected_summary_bytes(run_id, run_root, progress)
    if progress:
        if not summary_path.is_file() or summary_path.is_symlink():
            raise EvidenceError("tracked summary is missing or aliased")
        if summary_path.read_bytes() != expected:
            raise EvidenceError("tracked summary has missing, partial, or extra bytes")
    elif summary_path.exists():
        raise EvidenceError("unexpected tracked summary exists before its first entry")
    validate_summary_artifacts(run_id=run_id, run_root=run_root, progress=progress)
    return expected


def build_summary_plan(
    *, summary_path: Path, run_id: str, run_root: Path,
    progress: Sequence[Mapping[str, Any]], entry: Mapping[str, Any],
) -> Dict[str, Any]:
    preimage = validate_summary_file(
        summary_path=summary_path, run_id=run_id, run_root=run_root,
        progress=progress,
    )
    encoded = encode_entry(entry)
    postimage = preimage + encoded
    return {
        "entry_hex": encoded.hex(),
        "entry_id": entry["entry_id"],
        "entry_sha256": sha256_bytes(encoded),
        "postimage_sha256": sha256_bytes(postimage),
        "preimage_exists": bool(progress),
        "preimage_sha256": sha256_bytes(preimage),
        "summary_path": str(summary_path.resolve()),
        "turn": entry["turn"],
    }


def _atomic_replace(path: Path, data: bytes) -> None:
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
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def reconcile_summary_plan(
    *, plan: Mapping[str, Any], summary_path: Path, run_id: str,
    run_root: Path, progress: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    if plan.get("summary_path") != str(summary_path.resolve()):
        raise EvidenceError("summary plan path differs from configured summary")
    preimage = expected_summary_bytes(run_id, run_root, progress)
    try:
        entry = bytes.fromhex(plan["entry_hex"])
    except (KeyError, TypeError, ValueError) as exc:
        raise EvidenceError("summary plan entry bytes are invalid") from exc
    expected = dict(plan)
    postimage = preimage + entry
    if (
        expected.get("preimage_sha256") != sha256_bytes(preimage)
        or expected.get("postimage_sha256") != sha256_bytes(postimage)
        or expected.get("entry_sha256") != sha256_bytes(entry)
        or expected.get("preimage_exists") != bool(progress)
    ):
        raise EvidenceError("summary plan hashes do not match checkpointed progress")
    current_exists = summary_path.exists()
    current = summary_path.read_bytes() if current_exists and summary_path.is_file() else None
    if current == postimage:
        return expected
    permitted_preimage = (
        (not progress and not current_exists)
        or (bool(progress) and current_exists and current == preimage)
    )
    if not permitted_preimage:
        raise EvidenceError("summary is neither the permitted preimage nor postimage")
    _atomic_replace(summary_path, postimage)
    if summary_path.read_bytes() != postimage:
        raise EvidenceError("summary post-write verification failed")
    return expected


def _nul_paths(data: bytes) -> List[str]:
    return sorted({part.decode("utf-8") for part in data.split(b"\0") if part})


def changed_paths(repo: Path) -> List[str]:
    paths = set(_nul_paths(git_bytes(repo, ["diff", "--name-only", "-z"])))
    paths.update(_nul_paths(git_bytes(repo, ["diff", "--cached", "--name-only", "-z"])))
    paths.update(_nul_paths(git_bytes(
        repo, ["ls-files", "--others", "--exclude-standard", "-z"]
    )))
    return sorted(paths)


def staged_paths(repo: Path) -> List[str]:
    return _nul_paths(git_bytes(repo, ["diff", "--cached", "--name-only", "-z"]))


def remote_head(repo: Path, remote: str, push_ref: str) -> Optional[str]:
    output = git_bytes(repo, ["ls-remote", "--heads", remote, push_ref])
    lines = output.decode("ascii", errors="strict").splitlines()
    if not lines:
        return None
    if len(lines) != 1:
        raise EvidenceError("framework remote ref is ambiguous")
    fields = lines[0].split()
    if len(fields) != 2 or fields[1] != push_ref:
        raise EvidenceError("framework remote ref response is invalid")
    return fields[0]


def capture_framework(
    *, repo: Path, branch: str, remote: str, push_ref: str,
    require_clean: bool,
) -> Dict[str, Any]:
    repo = repo.resolve()
    if not repo.is_dir() or git_text(repo, ["rev-parse", "--is-inside-work-tree"]) != "true":
        raise EvidenceError("framework path is not a Git repository")
    top = Path(git_text(repo, ["rev-parse", "--show-toplevel"])).resolve()
    if top != repo:
        raise EvidenceError("framework path must be the repository root")
    observed_branch = git_text(repo, ["branch", "--show-current"])
    if observed_branch != branch:
        raise EvidenceError(
            f"framework branch mismatch: expected {branch!r}, observed {observed_branch!r}"
        )
    if re.fullmatch(r"[A-Za-z0-9._-]+", remote) is None or remote.startswith("-"):
        raise EvidenceError("framework remote name is invalid")
    if push_ref != f"refs/heads/{branch}":
        raise EvidenceError("framework push ref must name the configured branch")
    remote_url = git_text(repo, ["remote", "get-url", remote])
    head = git_text(repo, ["rev-parse", "--verify", "HEAD"])
    changes = changed_paths(repo)
    if require_clean and changes:
        raise EvidenceError("framework working tree must be clean before a new run")
    return {
        "branch": observed_branch,
        "changes": changes,
        "head": head,
        "push_ref": push_ref,
        "remote": remote,
        "remote_head": remote_head(repo, remote, push_ref),
        "remote_url": remote_url,
        "repo": str(repo),
    }


def relative_repo_path(repo: Path, path: Path) -> Optional[str]:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return None


def build_framework_commit_plan(
    *, repo: Path, branch: str, remote: str, push_ref: str,
    expected_parent: str, expected_remote_head: str, expected_remote_url: str,
    run_id: str,
    allowed_paths: Sequence[Path], required_summary: Path,
) -> Dict[str, Any]:
    state = capture_framework(
        repo=repo, branch=branch, remote=remote, push_ref=push_ref,
        require_clean=False,
    )
    if state["head"] != expected_parent:
        raise EvidenceError("framework HEAD changed before evidence commit planning")
    if state["remote_head"] != expected_remote_head:
        raise EvidenceError("framework remote ref changed before evidence commit planning")
    if state["remote_url"] != expected_remote_url:
        raise EvidenceError("framework remote URL changed before evidence commit planning")
    allow = {
        relative for path in allowed_paths
        if (relative := relative_repo_path(repo, path)) is not None
    }
    summary_relative = relative_repo_path(repo, required_summary)
    if summary_relative is None or summary_relative not in allow:
        raise EvidenceError("summary path is outside the framework commit allowlist")
    changes = changed_paths(repo)
    if summary_relative not in changes or not set(changes).issubset(allow):
        raise EvidenceError("framework changes exceed the evidence commit allowlist")
    if staged_paths(repo):
        raise EvidenceError("framework index must be empty before commit planning")
    hashes: Dict[str, str] = {}
    for relative in changes:
        path = repo / relative
        if not path.is_file() or path.is_symlink():
            raise EvidenceError("framework evidence commit accepts regular files only")
        hashes[relative] = sha256_file(path)
    subject = f"Record 1PCloop evidence for {run_id}"
    trailer = f"1PCloop-Run-ID: {run_id}"
    return {
        "branch": branch,
        "content_sha256": hashes,
        "expected_parent": expected_parent,
        "expected_remote_head": expected_remote_head,
        "expected_remote_url": expected_remote_url,
        "paths": changes,
        "push_ref": push_ref,
        "remote": remote,
        "repo": str(repo.resolve()),
        "run_id": run_id,
        "subject": subject,
        "trailer": trailer,
    }


def _validate_commit(plan: Mapping[str, Any], commit: str) -> None:
    repo = Path(plan["repo"])
    parent_line = git_text(repo, ["rev-list", "--parents", "-n", "1", commit]).split()
    if len(parent_line) != 2 or parent_line[1] != plan["expected_parent"]:
        raise EvidenceError("framework evidence commit is not the expected ordinary child")
    paths = _nul_paths(git_bytes(
        repo, ["diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit]
    ))
    if paths != plan["paths"]:
        raise EvidenceError("framework evidence commit path set differs from its plan")
    for relative, expected_sha in plan["content_sha256"].items():
        content = git_bytes(repo, ["show", f"{commit}:{relative}"])
        if sha256_bytes(content) != expected_sha:
            raise EvidenceError("framework evidence commit content hash mismatch")
    body = git_text(repo, ["show", "-s", "--format=%B", commit])
    if body != f"{plan['subject']}\n\n{plan['trailer']}":
        raise EvidenceError("framework evidence commit message does not bind the run ID")


def commit_or_reconcile(plan: Mapping[str, Any]) -> tuple[str, str]:
    repo = Path(plan["repo"])
    state = capture_framework(
        repo=repo, branch=plan["branch"], remote=plan["remote"],
        push_ref=plan["push_ref"], require_clean=False,
    )
    if state["remote_url"] != plan["expected_remote_url"]:
        raise EvidenceError("framework remote URL changed before evidence commit")
    head = state["head"]
    if head != plan["expected_parent"]:
        _validate_commit(plan, head)
        if changed_paths(repo):
            raise EvidenceError("framework worktree is dirty after the candidate commit")
        return head, "reconciled"
    if set(changed_paths(repo)) != set(plan["paths"]):
        raise EvidenceError("framework evidence files changed after commit planning")
    for relative, expected_sha in plan["content_sha256"].items():
        path = repo / relative
        if not path.is_file() or sha256_file(path) != expected_sha:
            raise EvidenceError("framework evidence content changed after commit planning")
    git_bytes(repo, ["add", "--", *plan["paths"]])
    if staged_paths(repo) != plan["paths"]:
        raise EvidenceError("framework staged path set differs from the commit plan")
    completed = subprocess.run(
        ["git", "commit", "--no-gpg-sign", "-m", plan["subject"],
         "-m", plan["trailer"], "--", *plan["paths"]],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode("utf-8", errors="replace").strip()
        raise EvidenceError(f"framework evidence commit failed: {detail}")
    commit = git_text(repo, ["rev-parse", "HEAD"])
    _validate_commit(plan, commit)
    if changed_paths(repo):
        raise EvidenceError("framework worktree is not clean after evidence commit")
    return commit, "created"


def push_or_reconcile(plan: Mapping[str, Any], commit: str) -> str:
    repo = Path(plan["repo"])
    state = capture_framework(
        repo=repo, branch=plan["branch"], remote=plan["remote"],
        push_ref=plan["push_ref"], require_clean=True,
    )
    if state["remote_url"] != plan["expected_remote_url"]:
        raise EvidenceError("framework remote URL changed before evidence push")
    if state["head"] != commit:
        raise EvidenceError("framework HEAD changed before evidence push")
    _validate_commit(plan, commit)
    observed = state["remote_head"]
    if observed == commit:
        return "already-present"
    if observed != plan["expected_remote_head"]:
        raise EvidenceError("framework remote ref is neither preimage nor evidence commit")
    completed = subprocess.run(
        ["git", "push", "--porcelain", plan["remote"],
         f"{commit}:{plan['push_ref']}"],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode("utf-8", errors="replace").strip()
        raise EvidenceError(f"framework evidence push failed: {detail}")
    if remote_head(repo, plan["remote"], plan["push_ref"]) != commit:
        raise EvidenceError("framework remote ref did not reach the evidence commit")
    return "succeeded"
