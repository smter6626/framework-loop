#!/usr/bin/env python3
"""Run a fail-closed, multi-cycle Reviewer/Executor mutation loop.

This is the first P5 orchestrator.  It deliberately treats Agent final messages as
opaque byte payloads: Python routes them and verifies mechanical state, but never
interprets readiness, acceptance, rejection, repair, or blocker semantics.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


SCRIPT_PATH = Path(__file__).resolve()
FRAMEWORK_ROOT = SCRIPT_PATH.parents[2]
ACTIVE_ROOT = FRAMEWORK_ROOT / "1PCloop"
DEFAULT_RUNS_ROOT = ACTIVE_ROOT / "runs"
DEFAULT_FRAMEWORK_STATIC = ACTIVE_ROOT / "docs/miniloop_static.md"
DEFAULT_FRAMEWORK_RUNTIME = ACTIVE_ROOT / "docs/miniloop_runtime.md"
DEFAULT_REVIEWER_HOME = Path("/Users/smterpro/.codex-B")
DEFAULT_EXECUTOR_HOME = Path("/Users/smterpro/.codex-A")

FRESH_EPHEMERAL = "fresh-ephemeral"
NEW_PERSISTENT = "new-persistent"
RESUME = "resume"
NO_CODEX_SANDBOX = "none"
BYPASS_APPROVALS_AND_SANDBOX_FLAG = "--dangerously-bypass-approvals-and-sandbox"

FRAMEWORK_STATIC = "framework_static"
FRAMEWORK_RUNTIME = "framework_runtime"
WORKLOAD_STATIC = "workload_static"
WORKLOAD_RUNTIME = "workload_runtime"
DOCUMENT_ORDER = (
    FRAMEWORK_STATIC,
    FRAMEWORK_RUNTIME,
    WORKLOAD_STATIC,
    WORKLOAD_RUNTIME,
)
STATIC_DOCUMENTS = (FRAMEWORK_STATIC, WORKLOAD_STATIC)
RUNTIME_DOCUMENTS = (FRAMEWORK_RUNTIME, WORKLOAD_RUNTIME)

CONTEXT_BEGIN = b"\n\n--- BEGIN P5 DETERMINISTIC AUTHORITATIVE CONTEXT ---\n"
CONTEXT_END = b"--- END P5 DETERMINISTIC AUTHORITATIVE CONTEXT ---\n"


def load_p4_helpers() -> ModuleType:
    """Load the accepted P3/P4 transport helpers without changing their API."""
    path = SCRIPT_PATH.with_name("run_text_loop.py")
    spec = importlib.util.spec_from_file_location("_p4_run_text_loop", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load P4 helpers: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


P4 = load_p4_helpers()


class InvariantViolation(RuntimeError):
    """A mechanical invariant failed and the loop must not continue."""


@dataclass(frozen=True)
class GovernanceDocument:
    name: str
    state_class: str
    path: Path
    content: bytes
    sha256: str
    byte_length: int
    line_count: int

    def metadata(self) -> Dict[str, Any]:
        return {
            "bytes": self.byte_length,
            "class": self.state_class,
            "lines": self.line_count,
            "path": str(self.path),
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class GovernanceSnapshot:
    documents: Mapping[str, GovernanceDocument]

    def hashes(self) -> Dict[str, str]:
        return {
            f"{name}_sha256": self.documents[name].sha256
            for name in DOCUMENT_ORDER
        }

    def metadata(self) -> Dict[str, Any]:
        return {
            name: self.documents[name].metadata() for name in DOCUMENT_ORDER
        }


@dataclass
class ReviewerState:
    reviewer_thread_id: Optional[str]
    known_hashes: Optional[Dict[str, str]]
    cycle_number: int
    known_target_head: Optional[str] = None

    def metadata(self) -> Dict[str, Any]:
        return {
            "cycle_number": self.cycle_number,
            "known_framework_runtime_sha": (
                self.known_hashes.get(f"{FRAMEWORK_RUNTIME}_sha256")
                if self.known_hashes is not None
                else None
            ),
            "known_framework_static_sha": (
                self.known_hashes.get(f"{FRAMEWORK_STATIC}_sha256")
                if self.known_hashes is not None
                else None
            ),
            "known_workload_runtime_sha": (
                self.known_hashes.get(f"{WORKLOAD_RUNTIME}_sha256")
                if self.known_hashes is not None
                else None
            ),
            "known_workload_static_sha": (
                self.known_hashes.get(f"{WORKLOAD_STATIC}_sha256")
                if self.known_hashes is not None
                else None
            ),
            "reviewer_known_target_head": self.known_target_head,
            "reviewer_thread_id": self.reviewer_thread_id,
        }


@dataclass(frozen=True)
class FreshnessPolicy:
    injection_mode: str
    injected_files: Tuple[str, ...]
    session_mode: str
    resume_target_thread_id: Optional[str]
    abandoned_thread_id: Optional[str]
    changed_files: Tuple[str, ...]

    def metadata(self) -> Dict[str, Any]:
        return {
            "abandoned_thread_id": self.abandoned_thread_id,
            "changed_files": list(self.changed_files),
            "injected_files": list(self.injected_files),
            "injection_mode": self.injection_mode,
            "resume_target_thread_id": self.resume_target_thread_id,
            "session_mode": self.session_mode,
        }


@dataclass(frozen=True)
class AuthoritativePrompt:
    prompt: bytes
    payload: bytes
    payload_offset: int
    document_offsets: Mapping[str, int]
    peer_payload: Optional[bytes]
    peer_payload_offset: Optional[int]
    snapshot: GovernanceSnapshot
    evidence: Dict[str, Any]


@dataclass(frozen=True)
class TargetState:
    repo: Path
    branch: str
    head: str
    clean: bool
    porcelain: str

    def metadata(self) -> Dict[str, Any]:
        return {
            "branch": self.branch,
            "clean": self.clean,
            "head": self.head,
            "repo": str(self.repo),
            "status_porcelain": self.porcelain,
        }


@dataclass
class TurnResult:
    turn_dir: Path
    final_message: bytes
    process: Dict[str, Any]

    @property
    def success(self) -> bool:
        return bool(self.process.get("success"))


def git_bytes(repo: Path, args: Sequence[str], *, check: bool = True) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode(
            "utf-8", errors="replace"
        ).strip()
        raise InvariantViolation(
            f"git {' '.join(args)} failed ({completed.returncode}): {detail}"
        )
    return completed.stdout


def git_text(repo: Path, args: Sequence[str]) -> str:
    return git_bytes(repo, args).decode("utf-8", errors="replace").strip()


def paths_overlap(left: Path, right: Path) -> bool:
    left = left.resolve()
    right = right.resolve()
    try:
        left.relative_to(right)
        return True
    except ValueError:
        pass
    try:
        right.relative_to(left)
        return True
    except ValueError:
        return False


def capture_target_state(
    target_repo: Path,
    requested_branch: str,
    *,
    require_clean: bool,
    enforce_branch: bool = True,
) -> TargetState:
    target_repo = target_repo.resolve()
    if not target_repo.is_dir():
        raise InvariantViolation(f"target repository does not exist: {target_repo}")
    if git_text(target_repo, ["rev-parse", "--is-inside-work-tree"]) != "true":
        raise InvariantViolation(f"target path is not a Git repository: {target_repo}")
    top_level = Path(
        git_text(target_repo, ["rev-parse", "--show-toplevel"])
    ).resolve()
    if top_level != target_repo:
        raise InvariantViolation(
            f"target path must be the repository root: {target_repo} != {top_level}"
        )
    branch = git_text(target_repo, ["branch", "--show-current"])
    if not branch and enforce_branch:
        raise InvariantViolation("target repository is in detached HEAD state")
    if enforce_branch and branch != requested_branch:
        raise InvariantViolation(
            f"target branch mismatch: requested {requested_branch!r}, observed {branch!r}"
        )
    head = git_text(target_repo, ["rev-parse", "--verify", "HEAD"])
    porcelain = git_bytes(
        target_repo, ["status", "--porcelain", "--untracked-files=all"]
    ).decode("utf-8", errors="replace")
    clean = not porcelain
    if require_clean and not clean:
        raise InvariantViolation(
            "target working tree must be clean; no automatic checkout, reset, clean, "
            "stash, or repair is permitted"
        )
    return TargetState(target_repo, branch, head, clean, porcelain)


def is_ancestor(repo: Path, before: str, after: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", before, after],
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    detail = (completed.stderr or completed.stdout).decode(
        "utf-8", errors="replace"
    ).strip()
    raise InvariantViolation(
        f"unable to verify target history ancestry ({completed.returncode}): {detail}"
    )


def new_history_evidence(
    repo: Path,
    before: str,
    after: str,
    governance: GovernanceSnapshot,
) -> Dict[str, Any]:
    if before == after:
        return {
            "merge_commits": [],
            "new_commits": [],
            "protected_governance_touches": [],
        }
    commits = git_text(repo, ["rev-list", "--reverse", f"{before}..{after}"]).splitlines()
    merge_commits: List[str] = []
    protected_touches: List[Dict[str, str]] = []
    protected_paths: List[Tuple[str, str]] = []
    for name in DOCUMENT_ORDER:
        try:
            relative = governance.documents[name].path.resolve().relative_to(repo.resolve())
        except ValueError:
            continue
        protected_paths.append((name, relative.as_posix()))

    for commit in commits:
        parent_line = git_text(repo, ["rev-list", "--parents", "-n", "1", commit])
        if len(parent_line.split()) > 2:
            merge_commits.append(commit)
        for name, relative in protected_paths:
            touched = git_text(
                repo,
                [
                    "diff-tree",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    "--root",
                    commit,
                    "--",
                    relative,
                ],
            )
            if touched:
                protected_touches.append(
                    {"commit": commit, "document": name, "path": relative}
                )
    return {
        "merge_commits": merge_commits,
        "new_commits": commits,
        "protected_governance_touches": protected_touches,
    }


def read_governance_document(
    name: str, state_class: str, path: Path
) -> GovernanceDocument:
    path = path.resolve()
    if not path.is_file():
        raise InvariantViolation(f"required governance file is missing: {path}")
    content = path.read_bytes()
    return GovernanceDocument(
        name=name,
        state_class=state_class,
        path=path,
        content=content,
        sha256=P4.sha256_bytes(content),
        byte_length=len(content),
        line_count=P4.count_lines(content),
    )


def capture_governance(paths: Mapping[str, Path]) -> GovernanceSnapshot:
    resolved = [paths[name].resolve() for name in DOCUMENT_ORDER]
    if len(set(resolved)) != len(resolved):
        raise InvariantViolation("all four governance input paths must be distinct")
    documents = {
        FRAMEWORK_STATIC: read_governance_document(
            FRAMEWORK_STATIC, "static", paths[FRAMEWORK_STATIC]
        ),
        FRAMEWORK_RUNTIME: read_governance_document(
            FRAMEWORK_RUNTIME, "runtime", paths[FRAMEWORK_RUNTIME]
        ),
        WORKLOAD_STATIC: read_governance_document(
            WORKLOAD_STATIC, "static", paths[WORKLOAD_STATIC]
        ),
        WORKLOAD_RUNTIME: read_governance_document(
            WORKLOAD_RUNTIME, "runtime", paths[WORKLOAD_RUNTIME]
        ),
    }
    snapshot = GovernanceSnapshot(documents)
    validate_snapshot_sources(snapshot)
    return snapshot


def validate_snapshot_sources(snapshot: GovernanceSnapshot) -> None:
    for name in DOCUMENT_ORDER:
        document = snapshot.documents[name]
        if not document.path.is_file():
            raise InvariantViolation(f"required governance file is missing: {document.path}")
        current = document.path.read_bytes()
        if current != document.content:
            raise InvariantViolation(f"{name} source bytes changed after snapshot")
        if P4.sha256_bytes(current) != document.sha256:
            raise InvariantViolation(f"{name} source/hash mismatch")
        if len(current) != document.byte_length:
            raise InvariantViolation(f"{name} source byte-length mismatch")
        if P4.count_lines(current) != document.line_count:
            raise InvariantViolation(f"{name} source line-count mismatch")


def compare_governance(
    before: GovernanceSnapshot, after: GovernanceSnapshot
) -> List[str]:
    return [
        name
        for name in DOCUMENT_ORDER
        if before.documents[name].sha256 != after.documents[name].sha256
    ]


def choose_freshness_policy(
    current: GovernanceSnapshot, state: ReviewerState
) -> FreshnessPolicy:
    current_hashes = current.hashes()
    if state.reviewer_thread_id is None:
        if state.known_hashes is not None or state.known_target_head is not None:
            raise InvariantViolation(
                "known Reviewer state exists without a Reviewer thread"
            )
        return FreshnessPolicy(
            injection_mode="full-bootstrap",
            injected_files=DOCUMENT_ORDER,
            session_mode=NEW_PERSISTENT,
            resume_target_thread_id=None,
            abandoned_thread_id=None,
            changed_files=DOCUMENT_ORDER,
        )
    if state.known_hashes is None:
        raise InvariantViolation("Reviewer thread exists without known governance hashes")
    if state.known_target_head is None:
        raise InvariantViolation("Reviewer thread exists without a known target HEAD")
    if set(state.known_hashes) != set(current_hashes):
        raise InvariantViolation("Reviewer known-hash field set is incomplete")

    changed = tuple(
        name
        for name in DOCUMENT_ORDER
        if state.known_hashes[f"{name}_sha256"]
        != current_hashes[f"{name}_sha256"]
    )
    if any(name in STATIC_DOCUMENTS for name in changed):
        return FreshnessPolicy(
            injection_mode="full-rebootstrap-static-change",
            injected_files=DOCUMENT_ORDER,
            session_mode=NEW_PERSISTENT,
            resume_target_thread_id=None,
            abandoned_thread_id=state.reviewer_thread_id,
            changed_files=changed,
        )
    changed_runtime = tuple(name for name in RUNTIME_DOCUMENTS if name in changed)
    if changed_runtime:
        return FreshnessPolicy(
            injection_mode="runtime-refresh",
            injected_files=changed_runtime,
            session_mode=RESUME,
            resume_target_thread_id=state.reviewer_thread_id,
            abandoned_thread_id=None,
            changed_files=changed,
        )
    if changed:
        raise InvariantViolation(f"unclassified governance change: {changed}")
    return FreshnessPolicy(
        injection_mode="resume-unchanged",
        injected_files=(),
        session_mode=RESUME,
        resume_target_thread_id=state.reviewer_thread_id,
        abandoned_thread_id=None,
        changed_files=(),
    )


def build_authoritative_prompt(
    *,
    role_prompt: bytes,
    current: GovernanceSnapshot,
    state: ReviewerState,
    policy: FreshnessPolicy,
    target_state: TargetState,
    cycle_number: int,
    peer_payload: Optional[bytes],
) -> AuthoritativePrompt:
    control_metadata = {
        "current_documents": current.metadata(),
        "current_hashes": current.hashes(),
        "cycle_number": cycle_number,
        "freshness_policy": policy.metadata(),
        "schema_version": 1,
        "session_known_hashes": copy.deepcopy(state.known_hashes),
        "session_known_target_head": state.known_target_head,
        "session_known_thread_id": state.reviewer_thread_id,
        "target": target_state.metadata(),
        "target_freshness": {
            "current_target_head": target_state.head,
            "reviewer_known_target_head": state.known_target_head,
            "target_head_changed": (
                state.known_target_head is not None
                and state.known_target_head != target_state.head
            ),
        },
    }
    parts = [
        CONTEXT_BEGIN,
        json.dumps(
            control_metadata, ensure_ascii=False, indent=2, sort_keys=True
        ).encode("utf-8"),
        b"\n",
    ]
    payload_offsets: Dict[str, int] = {}
    for name in policy.injected_files:
        document = current.documents[name]
        parts.append(f"--- BEGIN COMPLETE {name.upper()} BYTES ---\n".encode("ascii"))
        payload_offsets[name] = sum(len(part) for part in parts)
        parts.append(document.content)
        if document.content and not document.content.endswith(b"\n"):
            parts.append(b"\n")
        parts.append(f"--- END COMPLETE {name.upper()} BYTES ---\n".encode("ascii"))
    parts.append(CONTEXT_END)
    payload = b"".join(parts)
    payload_offset = len(role_prompt)
    prompt = role_prompt + payload
    peer_offset: Optional[int] = None
    if peer_payload is not None:
        prompt, peer_offset = P4.compose_peer_prompt(prompt, peer_payload)

    document_offsets = {
        name: payload_offset + offset for name, offset in payload_offsets.items()
    }
    evidence = {
        **control_metadata,
        "authoritative_payload_bytes": len(payload),
        "authoritative_payload_offset": payload_offset,
        "authoritative_payload_sha256": P4.sha256_bytes(payload),
        "document_prompt_offsets": document_offsets,
        "prompt_bytes": len(prompt),
        "prompt_sha256": P4.sha256_bytes(prompt),
        "validation": {
            "failure": None,
            "performed_before_launch": False,
            "prompt_bytes_verified": False,
            "source_bytes_verified": False,
        },
    }
    return AuthoritativePrompt(
        prompt=prompt,
        payload=payload,
        payload_offset=payload_offset,
        document_offsets=document_offsets,
        peer_payload=peer_payload,
        peer_payload_offset=peer_offset,
        snapshot=current,
        evidence=evidence,
    )


def validate_authoritative_prompt(authoritative: AuthoritativePrompt) -> None:
    validate_snapshot_sources(authoritative.snapshot)
    evidence = authoritative.evidence
    if P4.sha256_bytes(authoritative.prompt) != evidence["prompt_sha256"]:
        raise InvariantViolation("authoritative prompt hash mismatch")
    payload_start = authoritative.payload_offset
    payload_end = payload_start + len(authoritative.payload)
    if authoritative.prompt[payload_start:payload_end] != authoritative.payload:
        raise InvariantViolation("authoritative payload/prompt byte mismatch")
    if P4.sha256_bytes(authoritative.payload) != evidence["authoritative_payload_sha256"]:
        raise InvariantViolation("authoritative payload hash mismatch")
    expected = set(evidence["freshness_policy"]["injected_files"])
    if set(authoritative.document_offsets) != expected:
        raise InvariantViolation("injected-file metadata mismatch")
    for name, offset in authoritative.document_offsets.items():
        document = authoritative.snapshot.documents[name]
        if authoritative.prompt[offset : offset + document.byte_length] != document.content:
            raise InvariantViolation(f"{name} prompt-byte mismatch")
    if authoritative.peer_payload is not None:
        if authoritative.peer_payload_offset is None:
            raise InvariantViolation("peer payload offset is missing")
        start = authoritative.peer_payload_offset
        peer = authoritative.peer_payload
        if authoritative.prompt[start : start + len(peer)] != peer:
            raise InvariantViolation("Reviewer peer payload byte mismatch")


def reviewer_initial_prompt(target_repo: Path, target_branch: str) -> bytes:
    return f"""# P5 persistent Reviewer initial turn

You are the Reviewer in a multi-cycle Reviewer/Executor mutation loop. You are not
the Human Owner. The deterministic context envelope below contains complete bytes
for framework Static, framework Runtime, workload Static, and workload Runtime.

Independently inspect the target repository at `{target_repo}` on branch
`{target_branch}`. No Codex filesystem sandbox is active for this experiment. Your
role is inspection/review only. You MUST NOT modify target code or other target
files, alter target Git state, modify framework Static/Runtime, or modify workload
Static/Runtime. These behavioral restrictions are audited mechanically after the
turn.

Perform inspection, planning, review, repair planning, and production of exactly one
bounded natural-language instruction for the next fresh Executor.

Do not ask the Executor to push, merge, rewrite history, change branches, or modify
framework/workload governance. Do not rely on Python interpreting your wording.
Your complete final response is an opaque peer payload; no JSON, XML, marker, or
machine-parsed verdict is required.
""".encode("utf-8")


def reviewer_review_prompt(target_repo: Path, target_branch: str) -> bytes:
    return f"""# P5 persistent Reviewer review turn

You are the Reviewer in a multi-cycle Reviewer/Executor mutation loop. You are not
the Human Owner. The Executor's complete natural-language final response is appended
verbatim after the deterministic context envelope.

Independently inspect the actual target repository at `{target_repo}` on branch
`{target_branch}`, its current commit, diff/history, tests, and cited evidence. No
Codex filesystem sandbox is active for this experiment. Your role is inspection and
review only. You MUST NOT modify target code or other target files, alter target Git
state, modify framework Static/Runtime, or modify workload Static/Runtime. These
behavioral restrictions are audited mechanically after the turn.

Review the prior work and return natural-language review reasoning. If more work is
needed, include exactly one next bounded instruction. Otherwise, return the readiness
or Human-blocker handoff you judge appropriate. Python will not classify any of these
meanings; a following fresh Executor receives the entire final response as an opaque
payload.

Do not ask the Executor to push, merge, rewrite history, change branches, or modify
framework/workload governance. No JSON, XML, marker, or machine-parsed verdict is
required.
""".encode("utf-8")


def reviewer_refresh_prompt(target_repo: Path, target_branch: str) -> bytes:
    return f"""# P5 Reviewer pre-execution freshness turn

Authoritative governance and/or the target repository HEAD changed after your prior
bounded instruction and before the next Executor launch. Apply the deterministic
freshness envelope below, inspect `{target_repo}` on `{target_branch}` without
modifying it,
and replace the stale instruction with exactly one current bounded natural-language
instruction based on the current target HEAD.

No Codex filesystem sandbox is active for this experiment. Your role is inspection
and review only. You MUST NOT modify target code or other target files, alter target
Git state, modify framework Static/Runtime, or modify workload Static/Runtime. These
behavioral restrictions are audited mechanically after the turn. Do not ask the
Executor to push, merge, rewrite history, change branches, or modify governance.
Python routes your complete final response opaquely and does not interpret its
semantics.
""".encode("utf-8")


def executor_prompt(
    target_repo: Path, target_branch: str, governance: GovernanceSnapshot
) -> bytes:
    governance_paths = "\n".join(
        f"- {name}: {governance.documents[name].path}" for name in DOCUMENT_ORDER
    )
    return f"""# P5 fresh Executor mutation turn

You are the Executor, not the Reviewer or Human Owner. The Reviewer's complete
natural-language instruction follows after the transport marker. Execute only that
bounded task inside `{target_repo}` on the already checked-out branch
`{target_branch}`.

Requirements:
- No Codex filesystem sandbox is active for this experiment. These role restrictions
  are behavioral requirements audited mechanically after the turn.
- Modify ONLY the target repository and only as required by the bounded task.
- Inspect your changes, run relevant tests, and report concrete evidence.
- You may create ordinary descendant Git commits on the current target branch.
- Leave the target working tree clean after a meaningful mutation.
- Do not push, merge, rewrite history, reset, clean, stash, or switch branches.
- MUST NOT modify framework Static/Runtime.
- MUST NOT modify workload Static/Runtime.
- MUST NOT modify unrelated files outside the target repository.
- Do not accept your own work; return a concise natural-language execution receipt.

Protected governance inputs:
{governance_paths}

Your final response is transported verbatim. No JSON, XML, marker, or other
machine-parsed semantic schema is required.
""".encode("utf-8")


def build_codex_command(
    *,
    codex_bin: str,
    workspace: Path,
    final_path: Path,
    session_mode: str,
    resume_target_thread_id: Optional[str],
) -> List[str]:
    if session_mode not in (FRESH_EPHEMERAL, NEW_PERSISTENT, RESUME):
        raise ValueError(f"unknown session mode: {session_mode}")
    if session_mode == RESUME and not resume_target_thread_id:
        raise ValueError("resume requires an explicit Reviewer thread id")
    if session_mode != RESUME and resume_target_thread_id is not None:
        raise ValueError("resume target is only valid for resume mode")
    command = [codex_bin, "exec"]
    if session_mode == FRESH_EPHEMERAL:
        command.append("--ephemeral")
    command.extend(
        [
            "--json",
            "--color",
            "never",
            BYPASS_APPROVALS_AND_SANDBOX_FLAG,
            "--cd",
            str(workspace),
            "--output-last-message",
            str(final_path),
        ]
    )
    if session_mode == RESUME:
        command.extend(["resume", str(resume_target_thread_id), "-"])
    else:
        command.append("-")
    return command


def relative_evidence_path(path: Path, run_root: Path) -> str:
    return path.resolve().relative_to(run_root.resolve()).as_posix()


def run_codex_turn(
    *,
    run_root: Path,
    turn_dir: Path,
    codex_bin: str,
    codex_home: Path,
    workspace: Path,
    timeout_seconds: int,
    role: str,
    prompt: bytes,
    session_mode: str,
    resume_target_thread_id: Optional[str] = None,
    authoritative: Optional[AuthoritativePrompt] = None,
    peer_payload: Optional[bytes] = None,
    peer_payload_offset: Optional[int] = None,
    peer_source: Optional[str] = None,
) -> TurnResult:
    turn_dir.mkdir(parents=True, exist_ok=False)
    prompt_path = turn_dir / "prompt.txt"
    events_path = turn_dir / "events.jsonl"
    stderr_path = turn_dir / "stderr.txt"
    final_path = turn_dir / "final.txt"
    process_path = turn_dir / "process.json"
    prompt_path.write_bytes(prompt)

    authoritative_evidence: Optional[Dict[str, Any]] = None
    validation_failure: Optional[str] = (
        "persisted prompt differs from launch bytes"
        if prompt_path.read_bytes() != prompt
        else None
    )
    if authoritative is not None:
        authoritative_evidence = copy.deepcopy(authoritative.evidence)
        try:
            if validation_failure is not None:
                raise InvariantViolation(validation_failure)
            if prompt != authoritative.prompt:
                raise InvariantViolation("turn prompt differs from authoritative prompt")
            validate_authoritative_prompt(authoritative)
        except (OSError, InvariantViolation) as exc:
            validation_failure = str(exc)
            authoritative_evidence["validation"] = {
                "failure": validation_failure,
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
            "bytes": len(peer_payload),
            "peer_payload_path": relative_evidence_path(peer_path, run_root),
            "preserved_verbatim": preserved,
            "prompt_offset": peer_payload_offset,
            "sha256": P4.sha256_bytes(peer_payload),
            "source_final_message": peer_source,
        }
        if not preserved and validation_failure is None:
            validation_failure = "peer payload byte preservation failed"

    command = build_codex_command(
        codex_bin=codex_bin,
        workspace=workspace,
        final_path=final_path,
        session_mode=session_mode,
        resume_target_thread_id=resume_target_thread_id,
    )
    environment = os.environ.copy()
    environment["CODEX_HOME"] = str(codex_home)
    started_at = P4.utc_now()
    started_monotonic = time.monotonic()
    exit_code: Optional[int] = None
    stdout = b""
    stderr = b""
    failure = (
        f"launch validation failed: {validation_failure}"
        if validation_failure is not None
        else None
    )

    if validation_failure is None:
        try:
            completed = subprocess.run(
                command,
                cwd=str(workspace),
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

    duration = round(time.monotonic() - started_monotonic, 3)
    events_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    event_metadata = P4.extract_event_metadata(events_path.read_bytes())
    final_message = final_path.read_bytes() if final_path.is_file() else b""
    success = exit_code == 0 and bool(final_message) and validation_failure is None
    if not success and failure is None:
        failure = "Codex exited unsuccessfully or did not write a final message"

    observed_thread_id = event_metadata["thread_id"]
    created_thread_id = observed_thread_id if session_mode == NEW_PERSISTENT else None
    observed_resume_thread_id = observed_thread_id if session_mode == RESUME else None
    resume_verified: Optional[bool] = None
    if session_mode == NEW_PERSISTENT and created_thread_id is None:
        success = False
        failure = "persistent Reviewer did not provide a machine-readable thread id"
    if session_mode == RESUME:
        resume_verified = (
            observed_resume_thread_id is not None
            and observed_resume_thread_id == resume_target_thread_id
        )
        if not resume_verified:
            success = False
            relationship_failure = "resume event did not prove the target thread relationship"
            failure = (
                f"{failure}; {relationship_failure}"
                if failure is not None
                else relationship_failure
            )

    process = {
        "authoritative_context": authoritative_evidence,
        "approval_policy": "bypassed",
        "approvals_and_sandbox_bypassed": True,
        "cache_hit_ratio": event_metadata["cache_hit_ratio"],
        "cache_write_input_tokens": event_metadata["cache_write_input_tokens"],
        "cached_input_tokens": event_metadata["cached_input_tokens"],
        "codex_home": str(codex_home),
        "command": command,
        "created_thread_id": created_thread_id,
        "duration_seconds": duration,
        "event_parse": event_metadata["event_parse"],
        "events_path": relative_evidence_path(events_path, run_root),
        "exit_code": exit_code,
        "failure": failure,
        "final_message_path": (
            relative_evidence_path(final_path, run_root) if final_path.is_file() else None
        ),
        "final_message_sha256": P4.sha256_bytes(final_message) if final_message else None,
        "finished_at": P4.utc_now(),
        "input_tokens": event_metadata["input_tokens"],
        "observed_resume_thread_id": observed_resume_thread_id,
        "output_tokens": event_metadata["output_tokens"],
        "prompt_path": relative_evidence_path(prompt_path, run_root),
        "prompt_sha256": P4.sha256_bytes(prompt),
        "reasoning_output_tokens": event_metadata["reasoning_output_tokens"],
        "resume_relationship_verified": resume_verified,
        "resume_target_thread_id": resume_target_thread_id,
        "role": role,
        "sandbox": NO_CODEX_SANDBOX,
        "session_mode": session_mode,
        "started_at": started_at,
        "stderr_path": relative_evidence_path(stderr_path, run_root),
        "success": success,
        "thread_id": observed_thread_id,
        "transport": transport,
        "uncached_input_tokens": event_metadata["uncached_input_tokens"],
    }
    P4.write_json(process_path, process)
    return TurnResult(turn_dir, final_message, process)


def invoke_reviewer(
    *,
    run_root: Path,
    turn_dir: Path,
    target: TargetState,
    governance: GovernanceSnapshot,
    state: ReviewerState,
    cycle_number: int,
    role_prompt: bytes,
    peer_payload: Optional[bytes],
    peer_source: Optional[str],
    codex_bin: str,
    reviewer_home: Path,
    timeout_seconds: int,
) -> TurnResult:
    policy = choose_freshness_policy(governance, state)
    authoritative = build_authoritative_prompt(
        role_prompt=role_prompt,
        current=governance,
        state=state,
        policy=policy,
        target_state=target,
        cycle_number=cycle_number,
        peer_payload=peer_payload,
    )
    result = run_codex_turn(
        run_root=run_root,
        turn_dir=turn_dir,
        codex_bin=codex_bin,
        codex_home=reviewer_home,
        workspace=target.repo,
        timeout_seconds=timeout_seconds,
        role="reviewer",
        prompt=authoritative.prompt,
        session_mode=policy.session_mode,
        resume_target_thread_id=policy.resume_target_thread_id,
        authoritative=authoritative,
        peer_payload=peer_payload,
        peer_payload_offset=authoritative.peer_payload_offset,
        peer_source=peer_source,
    )
    reviewer_invariant_failure: Optional[str] = None
    target_after: Optional[TargetState] = None
    try:
        target_after = capture_target_state(
            target.repo,
            target.branch,
            require_clean=False,
            enforce_branch=False,
        )
        target_read_only_verified = (
            target_after.branch == target.branch
            and target_after.head == target.head
            and target_after.clean
        )
        if not target_read_only_verified:
            raise InvariantViolation("Reviewer changed target repository state")
        validate_snapshot_sources(governance)
    except (OSError, RuntimeError) as exc:
        target_read_only_verified = False
        reviewer_invariant_failure = str(exc)

    result.process["reviewer_target_before"] = target.metadata()
    result.process["reviewer_target_after"] = (
        target_after.metadata() if target_after is not None else None
    )
    result.process["reviewer_target_read_only_verified"] = target_read_only_verified
    if reviewer_invariant_failure is not None:
        result.process["success"] = False
        prior_failure = result.process.get("failure")
        result.process["failure"] = (
            f"{prior_failure}; {reviewer_invariant_failure}"
            if prior_failure
            else reviewer_invariant_failure
        )
    if result.success:
        new_thread_id = (
            result.process["created_thread_id"]
            if policy.session_mode == NEW_PERSISTENT
            else result.process["observed_resume_thread_id"]
        )
        if not new_thread_id:
            raise InvariantViolation("successful Reviewer turn lacks a verified thread id")
        state.reviewer_thread_id = new_thread_id
        state.known_hashes = governance.hashes()
        state.known_target_head = target.head
        state.cycle_number = cycle_number
    result.process["reviewer_state_after"] = state.metadata()
    P4.write_json(result.turn_dir / "process.json", result.process)
    return result


def make_peer_prompt(prefix: bytes, payload: bytes) -> Tuple[bytes, int]:
    prompt, offset = P4.compose_peer_prompt(prefix, payload)
    if prompt[offset : offset + len(payload)] != payload:
        raise InvariantViolation("peer payload was not preserved verbatim")
    return prompt, offset


def summarize_processes(processes: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    numeric_fields = (
        "input_tokens",
        "cached_input_tokens",
        "uncached_input_tokens",
        "cache_write_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    )

    def complete_total(field: str) -> Optional[int]:
        values = [process.get(field) for process in processes]
        if not values or any(type(value) is not int for value in values):
            return None
        return sum(values)

    totals = {field: complete_total(field) for field in numeric_fields}
    input_tokens = totals["input_tokens"]
    cached_tokens = totals["cached_input_tokens"]
    totals["cache_hit_ratio"] = (
        round(cached_tokens / input_tokens, 6)
        if input_tokens is not None
        and cached_tokens is not None
        and input_tokens > 0
        else None
    )
    return {
        "duration_seconds": round(
            sum(float(process.get("duration_seconds", 0.0)) for process in processes), 3
        ),
        "successful_turns": sum(bool(process.get("success")) for process in processes),
        "turn_count": len(processes),
        "usage_totals": totals,
    }


def write_manifest(
    *,
    run_root: Path,
    run_id: str,
    started_at: str,
    status: str,
    reason: Optional[str],
    target_initial: TargetState,
    governance_initial: GovernanceSnapshot,
    reviewer_state: ReviewerState,
    cycles: Sequence[Dict[str, Any]],
    processes: Sequence[Dict[str, Any]],
    run_configuration: Mapping[str, Any],
) -> None:
    manifest = {
        "cycles": list(cycles),
        "finished_at": P4.utc_now() if status != "RUNNING" else None,
        "governance_initial": governance_initial.metadata(),
        "reason": reason,
        "reviewer_state": reviewer_state.metadata(),
        "run_configuration": dict(run_configuration),
        "run_id": run_id,
        "schema_version": 1,
        "started_at": started_at,
        "status": status,
        "summary": summarize_processes(processes),
        "target": {
            "initial_target_head": target_initial.head,
            "target_branch": target_initial.branch,
            "target_repo": str(target_initial.repo),
        },
        "turns": list(processes),
    }
    P4.write_json(run_root / "manifest.json", manifest)


def validate_preflight(args: argparse.Namespace) -> Tuple[TargetState, GovernanceSnapshot]:
    target_repo = args.target_repo.resolve()
    runs_root = args.runs_root.resolve()
    if paths_overlap(target_repo, FRAMEWORK_ROOT):
        raise InvariantViolation(
            "target repository and framework repository must be independent, non-overlapping trees"
        )
    if paths_overlap(target_repo, runs_root):
        raise InvariantViolation(
            "runs root must be outside the target repository to preserve target cleanliness"
        )
    if not args.target_branch.strip():
        raise InvariantViolation("target branch must not be empty")
    target = capture_target_state(
        target_repo, args.target_branch, require_clean=True
    )

    governance_paths = {
        FRAMEWORK_STATIC: args.framework_static,
        FRAMEWORK_RUNTIME: args.framework_runtime,
        WORKLOAD_STATIC: args.workload_static,
        WORKLOAD_RUNTIME: args.workload_runtime,
    }
    governance = capture_governance(governance_paths)
    for label, home in (
        ("Reviewer CODEX_HOME", args.reviewer_home),
        ("Executor CODEX_HOME", args.executor_home),
    ):
        if not home.resolve().is_dir():
            raise InvariantViolation(f"{label} does not exist: {home.resolve()}")
    executable = shutil.which(args.codex_bin)
    if executable is None and not (
        Path(args.codex_bin).is_file() and os.access(args.codex_bin, os.X_OK)
    ):
        raise InvariantViolation(f"Codex executable is unavailable: {args.codex_bin}")
    return target, governance


def instruction_freshness_metadata(
    *,
    target: TargetState,
    governance: GovernanceSnapshot,
    state: ReviewerState,
) -> Dict[str, Any]:
    if state.reviewer_thread_id is None:
        raise InvariantViolation("instruction freshness requires a Reviewer thread")
    if state.known_hashes is None:
        raise InvariantViolation("instruction freshness requires known governance hashes")
    if state.known_target_head is None:
        raise InvariantViolation("instruction freshness requires a Reviewer-known target HEAD")
    current_hashes = governance.hashes()
    if set(state.known_hashes) != set(current_hashes):
        raise InvariantViolation("Reviewer known-hash field set is incomplete")
    governance_changes = [
        name
        for name in DOCUMENT_ORDER
        if state.known_hashes[f"{name}_sha256"]
        != current_hashes[f"{name}_sha256"]
    ]
    target_head_changed = state.known_target_head != target.head
    triggers = list(governance_changes)
    if target_head_changed:
        triggers.append("target_head")
    return {
        "current_target_head": target.head,
        "governance_changed_files": governance_changes,
        "refresh_required": bool(triggers),
        "reviewer_known_target_head": state.known_target_head,
        "target_head_changed": target_head_changed,
        "triggered_by": triggers,
    }


def ensure_instruction_fresh(
    *,
    run_root: Path,
    cycle_dir: Path,
    target: TargetState,
    governance_paths: Mapping[str, Path],
    state: ReviewerState,
    current_instruction: TurnResult,
    cycle_number: int,
    codex_bin: str,
    reviewer_home: Path,
    timeout_seconds: int,
) -> Tuple[
    TurnResult,
    GovernanceSnapshot,
    Optional[TurnResult],
    Dict[str, Any],
]:
    current = capture_governance(governance_paths)
    freshness = instruction_freshness_metadata(
        target=target,
        governance=current,
        state=state,
    )
    if not freshness["refresh_required"]:
        validate_snapshot_sources(current)
        freshness["refresh_performed"] = False
        return current_instruction, current, None, freshness
    refresh = invoke_reviewer(
        run_root=run_root,
        turn_dir=cycle_dir / "reviewer-pre-executor-refresh",
        target=target,
        governance=current,
        state=state,
        cycle_number=cycle_number,
        role_prompt=reviewer_refresh_prompt(target.repo, target.branch),
        peer_payload=None,
        peer_source=None,
        codex_bin=codex_bin,
        reviewer_home=reviewer_home,
        timeout_seconds=timeout_seconds,
    )
    freshness["refresh_performed"] = refresh.success
    freshness["replacement_instruction_path"] = (
        relative_evidence_path(refresh.turn_dir / "final.txt", run_root)
        if refresh.final_message
        else None
    )
    return refresh, current, refresh, freshness


def orchestrate(
    *,
    args: argparse.Namespace,
    target_initial: TargetState,
    governance_initial: GovernanceSnapshot,
) -> Tuple[int, Path]:
    run_id = P4.validate_run_id(args.run_id)
    run_root = args.runs_root.resolve() / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    started_at = P4.utc_now()
    cycles: List[Dict[str, Any]] = []
    processes: List[Dict[str, Any]] = []
    reviewer_state = ReviewerState(None, None, 0)
    status = "RUNNING"
    reason: Optional[str] = None
    governance_paths = {
        FRAMEWORK_STATIC: args.framework_static.resolve(),
        FRAMEWORK_RUNTIME: args.framework_runtime.resolve(),
        WORKLOAD_STATIC: args.workload_static.resolve(),
        WORKLOAD_RUNTIME: args.workload_runtime.resolve(),
    }
    run_configuration = {
        "approval_policy": "bypassed",
        "approvals_and_sandbox_bypassed": True,
        "codex_bin": str(Path(shutil.which(args.codex_bin) or args.codex_bin).resolve()),
        "executor_home": str(args.executor_home.resolve()),
        "executor_sandbox": NO_CODEX_SANDBOX,
        "executor_session_mode": FRESH_EPHEMERAL,
        "execution_policy": "prompt-defined-roles-with-post-turn-mechanical-audit",
        "framework_git_head": git_text(FRAMEWORK_ROOT, ["rev-parse", "HEAD"]),
        "max_cycles": args.max_cycles,
        "reviewer_home": str(args.reviewer_home.resolve()),
        "reviewer_session_mode": "persistent-with-explicit-resume",
        "reviewer_sandbox": NO_CODEX_SANDBOX,
        "runs_root": str(args.runs_root.resolve()),
        "timeout_seconds": args.timeout_seconds,
    }
    write_manifest(
        run_root=run_root,
        run_id=run_id,
        started_at=started_at,
        status=status,
        reason=reason,
        target_initial=target_initial,
        governance_initial=governance_initial,
        reviewer_state=reviewer_state,
        cycles=cycles,
        processes=processes,
        run_configuration=run_configuration,
    )

    try:
        cycle_one_dir = run_root / "cycle-01"
        cycle_one_dir.mkdir()
        initial_reviewer = invoke_reviewer(
            run_root=run_root,
            turn_dir=cycle_one_dir / "reviewer-instruction",
            target=target_initial,
            governance=governance_initial,
            state=reviewer_state,
            cycle_number=1,
            role_prompt=reviewer_initial_prompt(
                target_initial.repo, target_initial.branch
            ),
            peer_payload=None,
            peer_source=None,
            codex_bin=args.codex_bin,
            reviewer_home=args.reviewer_home.resolve(),
            timeout_seconds=args.timeout_seconds,
        )
        processes.append(initial_reviewer.process)
        if not initial_reviewer.success:
            raise InvariantViolation(
                f"initial Reviewer process failed: {initial_reviewer.process['failure']}"
            )
        instruction = initial_reviewer

        for cycle_number in range(1, args.max_cycles + 1):
            cycle_dir = run_root / f"cycle-{cycle_number:02d}"
            cycle_dir.mkdir(exist_ok=(cycle_number == 1))
            cycle: Dict[str, Any] = {
                "cycle_number": cycle_number,
                "executor": None,
                "governance_before_executor": None,
                "reviewer_instruction_source": relative_evidence_path(
                    instruction.turn_dir / "final.txt", run_root
                ),
                "reviewer_instruction_process": instruction.process,
                "instruction_freshness": None,
                "reviewer_pre_executor_refresh": None,
                "reviewer_review": None,
                "reviewer_state_before": copy.deepcopy(reviewer_state.metadata()),
                "target_triggered_instruction_refresh": False,
                "target_after": None,
                "target_before": None,
            }
            cycles.append(cycle)

            target_for_freshness = capture_target_state(
                target_initial.repo, target_initial.branch, require_clean=True
            )
            instruction, governance_before, refresh, instruction_freshness = (
                ensure_instruction_fresh(
                    run_root=run_root,
                    cycle_dir=cycle_dir,
                    target=target_for_freshness,
                    governance_paths=governance_paths,
                    state=reviewer_state,
                    current_instruction=instruction,
                    cycle_number=cycle_number,
                    codex_bin=args.codex_bin,
                    reviewer_home=args.reviewer_home.resolve(),
                    timeout_seconds=args.timeout_seconds,
                )
            )
            cycle["instruction_freshness"] = instruction_freshness
            cycle["target_triggered_instruction_refresh"] = bool(
                instruction_freshness["target_head_changed"]
            )
            if refresh is not None:
                processes.append(refresh.process)
                cycle["reviewer_pre_executor_refresh"] = refresh.process
                cycle["reviewer_instruction_source"] = relative_evidence_path(
                    refresh.turn_dir / "final.txt", run_root
                )
                cycle["reviewer_instruction_process"] = refresh.process
                if not refresh.success:
                    raise InvariantViolation(
                        f"Reviewer freshness process failed: {refresh.process['failure']}"
                    )
            validate_snapshot_sources(governance_before)
            if reviewer_state.known_hashes != governance_before.hashes():
                raise InvariantViolation(
                    "Reviewer known hashes do not match governance immediately before Executor"
                )
            target_before = capture_target_state(
                target_initial.repo, target_initial.branch, require_clean=True
            )
            if reviewer_state.known_target_head != target_before.head:
                raise InvariantViolation(
                    "current target HEAD does not match Reviewer-known target HEAD "
                    "immediately before Executor"
                )
            cycle["governance_before_executor"] = governance_before.metadata()
            cycle["reviewer_state_before"] = copy.deepcopy(reviewer_state.metadata())
            cycle["target_before"] = target_before.metadata()

            executor_prefix = executor_prompt(
                target_before.repo, target_before.branch, governance_before
            )
            executor_full_prompt, executor_peer_offset = make_peer_prompt(
                executor_prefix, instruction.final_message
            )
            launch_target = capture_target_state(
                target_initial.repo, target_initial.branch, require_clean=True
            )
            cycle["target_launch_check"] = launch_target.metadata()
            if launch_target.head != reviewer_state.known_target_head:
                raise InvariantViolation(
                    "target HEAD changed after instruction freshness check and before "
                    "Executor launch"
                )
            if launch_target.head != target_before.head:
                raise InvariantViolation(
                    "target HEAD changed while the Executor launch prompt was prepared"
                )
            validate_snapshot_sources(governance_before)
            target_before = launch_target
            cycle["target_before"] = target_before.metadata()
            executor = run_codex_turn(
                run_root=run_root,
                turn_dir=cycle_dir / "executor",
                codex_bin=args.codex_bin,
                codex_home=args.executor_home.resolve(),
                workspace=target_before.repo,
                timeout_seconds=args.timeout_seconds,
                role="executor",
                prompt=executor_full_prompt,
                session_mode=FRESH_EPHEMERAL,
                peer_payload=instruction.final_message,
                peer_payload_offset=executor_peer_offset,
                peer_source=relative_evidence_path(
                    instruction.turn_dir / "final.txt", run_root
                ),
            )
            processes.append(executor.process)
            cycle["executor"] = executor.process
            target_after = capture_target_state(
                target_initial.repo,
                target_initial.branch,
                require_clean=False,
                enforce_branch=False,
            )
            cycle["target_after"] = target_after.metadata()
            governance_after = capture_governance(governance_paths)
            governance_changes = compare_governance(
                governance_before, governance_after
            )
            cycle["governance_after_executor"] = governance_after.metadata()
            cycle["governance_changes_during_executor"] = governance_changes
            if governance_changes:
                raise InvariantViolation(
                    "protected governance changed during Executor cycle: "
                    + ", ".join(governance_changes)
                )
            if target_after.branch != target_before.branch:
                raise InvariantViolation("target branch changed during Executor cycle")
            if not target_after.clean:
                raise InvariantViolation(
                    "Executor left the target repository working tree dirty"
                )
            if not executor.success:
                raise InvariantViolation(
                    f"Executor process failed: {executor.process['failure']}"
                )
            if target_after.head != target_before.head and not is_ancestor(
                target_before.repo, target_before.head, target_after.head
            ):
                raise InvariantViolation(
                    "target history did not advance by a non-rewriting descendant commit"
                )
            history = new_history_evidence(
                target_before.repo,
                target_before.head,
                target_after.head,
                governance_after,
            )
            cycle["target_history"] = history
            if history["merge_commits"]:
                raise InvariantViolation("Executor introduced a merge commit")
            if history["protected_governance_touches"]:
                raise InvariantViolation(
                    "Executor commit history touched protected governance inputs"
                )
            cycle["head_changed"] = target_after.head != target_before.head

            current_governance = capture_governance(governance_paths)
            reviewer = invoke_reviewer(
                run_root=run_root,
                turn_dir=cycle_dir / "reviewer-review",
                target=target_after,
                governance=current_governance,
                state=reviewer_state,
                cycle_number=cycle_number,
                role_prompt=reviewer_review_prompt(
                    target_after.repo, target_after.branch
                ),
                peer_payload=executor.final_message,
                peer_source=relative_evidence_path(
                    executor.turn_dir / "final.txt", run_root
                ),
                codex_bin=args.codex_bin,
                reviewer_home=args.reviewer_home.resolve(),
                timeout_seconds=args.timeout_seconds,
            )
            processes.append(reviewer.process)
            cycle["reviewer_review"] = reviewer.process
            cycle["reviewer_state_after"] = reviewer_state.metadata()
            if not reviewer.success:
                raise InvariantViolation(
                    f"Reviewer review process failed: {reviewer.process['failure']}"
                )
            instruction = reviewer

            if target_after.head == target_before.head:
                status = "STOPPED_FOR_HUMAN_REVIEW"
                reason = "target_head_unchanged"
                write_manifest(
                    run_root=run_root,
                    run_id=run_id,
                    started_at=started_at,
                    status=status,
                    reason=reason,
                    target_initial=target_initial,
                    governance_initial=governance_initial,
                    reviewer_state=reviewer_state,
                    cycles=cycles,
                    processes=processes,
                    run_configuration=run_configuration,
                )
                return 0, run_root

            write_manifest(
                run_root=run_root,
                run_id=run_id,
                started_at=started_at,
                status="RUNNING",
                reason=None,
                target_initial=target_initial,
                governance_initial=governance_initial,
                reviewer_state=reviewer_state,
                cycles=cycles,
                processes=processes,
                run_configuration=run_configuration,
            )
            if cycle_number == args.max_cycles:
                status = "STOPPED_FOR_HUMAN_REVIEW"
                reason = "max_cycles_reached"
                break
    except (OSError, RuntimeError, ValueError) as exc:
        status = "FAILED_CLOSED"
        reason = str(exc)

    write_manifest(
        run_root=run_root,
        run_id=run_id,
        started_at=started_at,
        status=status,
        reason=reason,
        target_initial=target_initial,
        governance_initial=governance_initial,
        reviewer_state=reviewer_state,
        cycles=cycles,
        processes=processes,
        run_configuration=run_configuration,
    )
    return (1 if status == "FAILED_CLOSED" else 0), run_root


def preflight_report(
    target: TargetState, governance: GovernanceSnapshot, args: argparse.Namespace
) -> Dict[str, Any]:
    return {
        "codex_bin": str(Path(shutil.which(args.codex_bin) or args.codex_bin).resolve()),
        "execution_policy": {
            "approval_policy": "bypassed",
            "approvals_and_sandbox_bypassed": True,
            "role_separation": "prompt-defined-with-post-turn-mechanical-audit",
            "sandbox": NO_CODEX_SANDBOX,
        },
        "executor_home": str(args.executor_home.resolve()),
        "governance": governance.metadata(),
        "max_cycles": args.max_cycles,
        "preflight": "passed",
        "reviewer_home": str(args.reviewer_home.resolve()),
        "target": {
            "initial_target_head": target.head,
            "target_branch": target.branch,
            "target_repo": str(target.repo),
            "working_tree_clean": target.clean,
        },
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-repo", type=Path, required=True)
    parser.add_argument("--target-branch", required=True)
    parser.add_argument("--workload-static", type=Path, required=True)
    parser.add_argument("--workload-runtime", type=Path, required=True)
    parser.add_argument("--max-cycles", type=int, default=8)
    parser.add_argument(
        "--framework-static", type=Path, default=DEFAULT_FRAMEWORK_STATIC
    )
    parser.add_argument(
        "--framework-runtime", type=Path, default=DEFAULT_FRAMEWORK_RUNTIME
    )
    parser.add_argument("--reviewer-home", type=Path, default=DEFAULT_REVIEWER_HOME)
    parser.add_argument("--executor-home", type=Path, default=DEFAULT_EXECUTOR_HOME)
    parser.add_argument("--codex-bin", default=shutil.which("codex") or "codex")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--run-id", default=P4.default_run_id())
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="validate inputs without creating evidence or invoking Codex",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.max_cycles <= 0:
        raise SystemExit("--max-cycles must be positive")
    if args.timeout_seconds <= 0:
        raise SystemExit("--timeout-seconds must be positive")
    try:
        P4.validate_run_id(args.run_id)
        target, governance = validate_preflight(args)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"preflight failed: {exc}", file=sys.stderr)
        return 2

    if args.preflight_only:
        print(
            json.dumps(
                preflight_report(target, governance, args),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    try:
        exit_code, run_root = orchestrate(
            args=args,
            target_initial=target,
            governance_initial=governance,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"unable to start mutation loop: {exc}", file=sys.stderr)
        return 1
    print(run_root)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
