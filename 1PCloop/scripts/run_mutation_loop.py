#!/usr/bin/env python3
"""Run a fail-closed, recoverable Reviewer/Executor mutation loop.

P6 uses runtime-enforced role schemas and the overwrite-only checkpoint to apply
one explicitly authorized workload Runtime transition, retain raw evidence locally,
and publish one tracked evidence summary. Peer payload bytes are preserved;
embedded natural language is never interpreted by Python.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, replace
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple


SCRIPT_PATH = Path(__file__).resolve()
FRAMEWORK_ROOT = SCRIPT_PATH.parents[2]
ACTIVE_ROOT = FRAMEWORK_ROOT / "1PCloop"
DEFAULT_RUNS_ROOT = ACTIVE_ROOT / ".local" / "runs"
DEFAULT_STATE_ROOT = ACTIVE_ROOT / ".local" / "state"
DEFAULT_SUMMARY_ROOT = ACTIVE_ROOT / "evidence-summaries"
DEFAULT_FRAMEWORK_STATIC = ACTIVE_ROOT / "docs/miniloop_static.md"
DEFAULT_FRAMEWORK_RUNTIME = ACTIVE_ROOT / "docs/miniloop_runtime.md"
RUNTIME_STATE_BEGIN = b"<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->"
RUNTIME_STATE_END = b"<!-- 1PCLOOP_RUNTIME_STATE_END -->"

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

PREFLIGHT_PASSED = "PREFLIGHT_PASSED"
REVIEWER_INSTRUCTION_RUNNING = "REVIEWER_INSTRUCTION_RUNNING"
INSTRUCTION_READY = "INSTRUCTION_READY"
EXECUTOR_RUNNING = "EXECUTOR_RUNNING"
EXECUTOR_COMMITTED = "EXECUTOR_COMMITTED"
REVIEW_PENDING = "REVIEW_PENDING"
REVIEW_COMPLETED = "REVIEW_COMPLETED"
REVIEW_CORRECTION_PENDING = "REVIEW_CORRECTION_PENDING"
REVIEW_CORRECTION_RUNNING = "REVIEW_CORRECTION_RUNNING"
RUNTIME_TRANSITION_PENDING = "RUNTIME_TRANSITION_PENDING"
RUNTIME_TRANSITION_COMMITTED = "RUNTIME_TRANSITION_COMMITTED"
HUMAN_GATE = "HUMAN_GATE"
FAILED_CLOSED = "FAILED_CLOSED"
EVIDENCE_FINALIZATION_PENDING = "EVIDENCE_FINALIZATION_PENDING"
FRAMEWORK_EVIDENCE_COMMITTED = "FRAMEWORK_EVIDENCE_COMMITTED"
FRAMEWORK_EVIDENCE_PUSHED = "FRAMEWORK_EVIDENCE_PUSHED"
TERMINAL_CHECKPOINT_STATES = {
    FRAMEWORK_EVIDENCE_PUSHED,
}
MAX_REVIEW_CORRECTION_ATTEMPTS = 2


def load_contract_helpers() -> ModuleType:
    """Load pure mutation contracts without creating a runner dependency."""
    name = "mutation_contracts"
    path = SCRIPT_PATH.with_name("mutation_contracts.py")
    existing = sys.modules.get(name)
    existing_path = getattr(existing, "__file__", None)
    if existing_path is not None and Path(existing_path).resolve() == path.resolve():
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load mutation contracts: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CONTRACTS = load_contract_helpers()
DEFAULT_REVIEWER_HOME = CONTRACTS.DEFAULT_REVIEWER_HOME
DEFAULT_EXECUTOR_HOME = CONTRACTS.DEFAULT_EXECUTOR_HOME
SCHEMAS_ROOT = CONTRACTS.SCHEMAS_ROOT
REVIEWER_INSTRUCTION = CONTRACTS.REVIEWER_INSTRUCTION
EXECUTOR_RECEIPT = CONTRACTS.EXECUTOR_RECEIPT
REVIEWER_VERDICT = CONTRACTS.REVIEWER_VERDICT
TURN_SCHEMAS = CONTRACTS.TURN_SCHEMAS
InvariantViolation = CONTRACTS.InvariantViolation
ControlErrorCode = CONTRACTS.ControlErrorCode
CORRECTABLE_VERDICT_CODES = CONTRACTS.CORRECTABLE_VERDICT_CODES
ControlFailure = CONTRACTS.ControlFailure
correctable_failure = CONTRACTS.correctable_failure
control_error_code = CONTRACTS.control_error_code
MAX_PUBLIC_REASON_CHARS = CONTRACTS.MAX_PUBLIC_REASON_CHARS
PUBLIC_REASON_TRUNCATION_MARKER = CONTRACTS.PUBLIC_REASON_TRUNCATION_MARKER
UNCLASSIFIED_PUBLIC_REASON = CONTRACTS.UNCLASSIFIED_PUBLIC_REASON
FINAL_RESULT_FIELDS = CONTRACTS.FINAL_RESULT_FIELDS
escape_public_text = CONTRACTS.escape_public_text
bounded_public_reason = CONTRACTS.bounded_public_reason
public_final_result = CONTRACTS.public_final_result
terminal_scalar = CONTRACTS.terminal_scalar
strict_json = CONTRACTS.strict_json
validate_json_schema = CONTRACTS.validate_json_schema
schema_path = CONTRACTS.schema_path
validate_turn_payload = CONTRACTS.validate_turn_payload
validate_verdict_relationships = CONTRACTS.validate_verdict_relationships
validate_role_runtime_homes = CONTRACTS.validate_role_runtime_homes


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


def load_p63_helpers() -> ModuleType:
    path = SCRIPT_PATH.with_name("p63_evidence.py")
    spec = importlib.util.spec_from_file_location("_p63_evidence", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load P6.3 helpers: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


P63 = load_p63_helpers()


def load_progress_helpers() -> ModuleType:
    path = SCRIPT_PATH.with_name("progress_status.py")
    spec = importlib.util.spec_from_file_location("_f2_progress_status", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load F2 progress helpers: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PROGRESS = load_progress_helpers()
_ACTIVE_PROGRESS: Optional[Any] = None


def record_active_progress(method: str, *args: Any, **kwargs: Any) -> Optional[Any]:
    reporter = _ACTIVE_PROGRESS
    if reporter is None or not reporter.observation_available:
        return None
    try:
        return getattr(reporter, method)(*args, **kwargs)
    except PROGRESS.ProgressError:
        reporter.observation_available = False
        reporter.observation_error = "structured progress observation unavailable"
        return None


def emit_progress(message: str) -> None:
    """Legacy fallback outside an active F2 structured progress reporter."""
    if _ACTIVE_PROGRESS is not None:
        return
    print(f"[{P4.utc_now()}] {escape_public_text(str(message))}", flush=True)


def emit_machine_fallback(category: str, kind: str, count: int) -> None:
    """Bounded fallback used only after structured observation is unavailable."""
    print(
        f"[{P4.utc_now()}] CODEX_FALLBACK "
        f"category={terminal_scalar(category)} kind={terminal_scalar(kind)} "
        f"count={count}",
        flush=True,
    )


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Atomically replace one JSON file without creating checkpoint history."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}-{threading.get_ident()}")
    data = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    try:
        with temporary.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass
class CheckpointStore:
    path: Path
    observer: Optional[Callable[[str, Mapping[str, Any]], None]] = None

    def exists(self) -> bool:
        return self.path.is_file()

    def load(self) -> Dict[str, Any]:
        if not self.path.is_file():
            raise InvariantViolation(f"checkpoint does not exist: {self.path}")
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise InvariantViolation(f"checkpoint is unreadable: {exc}") from exc
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise InvariantViolation("checkpoint schema is unsupported")
        state = value.get("state")
        if not isinstance(state, str):
            raise InvariantViolation("checkpoint state is missing")
        return value

    def write(self, state: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        value = dict(payload)
        value["schema_version"] = 1
        value["state"] = state
        value["updated_at"] = P4.utc_now()
        atomic_write_json(self.path, value)
        emit_progress(f"checkpoint state={state} path={self.path}")
        if self.observer is not None:
            self.observer(state, value)
        return value


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


def reviewer_state_record(state: ReviewerState) -> Dict[str, Any]:
    return {
        "cycle_number": state.cycle_number,
        "known_hashes": copy.deepcopy(state.known_hashes),
        "known_target_head": state.known_target_head,
        "reviewer_thread_id": state.reviewer_thread_id,
    }


def reviewer_state_from_record(value: Mapping[str, Any]) -> ReviewerState:
    known_hashes = value.get("known_hashes")
    if known_hashes is not None and not isinstance(known_hashes, dict):
        raise InvariantViolation("checkpoint Reviewer hashes are invalid")
    cycle_number = value.get("cycle_number")
    if type(cycle_number) is not int or cycle_number < 0:
        raise InvariantViolation("checkpoint Reviewer cycle is invalid")
    return ReviewerState(
        reviewer_thread_id=value.get("reviewer_thread_id"),
        known_hashes=copy.deepcopy(known_hashes),
        cycle_number=cycle_number,
        known_target_head=value.get("known_target_head"),
    )


def turn_reference(turn: TurnResult, run_root: Path) -> Dict[str, str]:
    final_path = turn.turn_dir / "final.txt"
    process_path = turn.turn_dir / "process.json"
    return {
        "final_path": relative_evidence_path(final_path, run_root),
        "final_sha256": P4.sha256_bytes(turn.final_message),
        "process_path": relative_evidence_path(process_path, run_root),
        "process_sha256": P4.sha256_file(process_path),
    }


def load_turn_reference(reference: Mapping[str, Any], run_root: Path) -> TurnResult:
    final_relative = reference.get("final_path")
    process_relative = reference.get("process_path")
    expected_sha = reference.get("final_sha256")
    if not all(isinstance(value, str) for value in (final_relative, process_relative, expected_sha)):
        raise InvariantViolation("checkpoint turn reference is incomplete")
    final_path = (run_root / final_relative).resolve()
    process_path = (run_root / process_relative).resolve()
    try:
        final_path.relative_to(run_root.resolve())
        process_path.relative_to(run_root.resolve())
    except ValueError as exc:
        raise InvariantViolation("checkpoint turn reference escapes the run root") from exc
    if not final_path.is_file() or not process_path.is_file():
        raise InvariantViolation("checkpoint turn artifact is missing")
    if P4.sha256_file(process_path) != reference.get("process_sha256"):
        raise InvariantViolation("checkpoint turn process hash mismatch")
    final_message = final_path.read_bytes()
    if P4.sha256_bytes(final_message) != expected_sha:
        raise InvariantViolation("checkpoint turn final-message hash mismatch")
    try:
        process = json.loads(process_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvariantViolation(f"checkpoint turn process is unreadable: {exc}") from exc
    if not isinstance(process, dict) or not process.get("success"):
        raise InvariantViolation("checkpoint turn process is not successful")
    validate_turn_payload(final_message, process.get("output_schema"))
    return TurnResult(final_path.parent, final_message, process)


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
    return f"""# P6 persistent Reviewer initial turn

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
Return the runtime-enforced reviewer_instruction JSON wrapper: schema_version=1,
message_type=reviewer_instruction, evidence_summary (at most 2000 characters), and
peer_message containing your complete bounded natural-language instruction. You have
no verdict authority in this instruction turn. The full JSON bytes are routed unchanged.
""".encode("utf-8")


def reviewer_review_prompt(target_repo: Path, target_branch: str) -> bytes:
    return f"""# P6 persistent Reviewer review turn

You are the Reviewer in a multi-cycle Reviewer/Executor mutation loop. You are not
the Human Owner. The Executor's complete natural-language final response is appended
verbatim after the deterministic context envelope.

Independently inspect the actual target repository at `{target_repo}` on branch
`{target_branch}`, its current commit, diff/history, tests, and cited evidence. No
Codex filesystem sandbox is active for this experiment. Your role is inspection and
review only. You MUST NOT modify target code or other target files, alter target Git
state, modify framework Static/Runtime, or modify workload Static/Runtime. These
behavioral restrictions are audited mechanically after the turn.

Return the runtime-enforced reviewer_verdict JSON wrapper. Include your complete
natural-language review in peer_message and a concise evidence_summary (<=2000 chars).
Only this Reviewer review turn may set verdict: ACCEPT, REJECT, or HUMAN_GATE.
Bind reviewed_target.repo/branch/head and all four governance_hashes to the current
deterministic envelope; expected_runtime_sha256 is its workload Runtime SHA-256.
Read active_step_id from the workload Runtime machine block. If no block exists and
no step ID can be established, use "unavailable" and HUMAN_GATE; never invent ACCEPT.
ACCEPT requires nonempty evidence, next_instruction=null, and runtime_transition=
{{"new_status":"COMPLETED","next_active_step":null}}. Evidence includes at least one
full reachable commit ID and only mechanically valid evidence. Each evidence entry
has kind, locator, sha256: for commits hash raw `git cat-file commit <full-id>` bytes.
Every `file`, `artifact`, or `test` locator must be an absolute path to an existing
file inside the target repository or this run's evidence directory, hashed from its
actual bytes. A shell command, Git-status description, or prose is not a locator. If
no real test/artifact output file exists, do not invent `test`/`artifact` evidence.
Independently inspect every ACCEPT evidence entry before returning it.
REJECT requires one nonempty next_instruction of at most 8000 characters and
runtime_transition=null. HUMAN_GATE requires both fields null; explain the Human
blocker in peer_message. Empty evidence is permitted only for REJECT/HUMAN_GATE.
An ACCEPT requests exactly one current step completion; it does not authorize direct
Runtime writes. The orchestrator alone may write after CLI and Runtime opt-in checks.
The next Executor, when needed, receives the full final JSON payload unchanged.

Do not ask the Executor to push, merge, rewrite history, change branches, or modify
framework/workload governance. Follow the supplied runtime-enforced JSON Schema.
""".encode("utf-8")


def reviewer_correction_prompt(context: Mapping[str, Any]) -> bytes:
    """Build a bounded deterministic correction request without peer semantics."""
    encoded = json.dumps(
        context, ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8")
    return b"""# F1 Reviewer verdict control-output correction

You are the same Reviewer that produced the prior verdict. This is a correction of
your schema-valid control wrapper, not a new Executor task. Do not modify the target,
Git state, framework governance, or workload governance. Do not ask for or invoke an
Executor. Re-open and independently inspect the actual commit/files/test artifacts
inside the declared evidence boundaries before returning a new verdict.

Return one complete reviewer_verdict object under the same runtime-enforced schema.
You may return ACCEPT, REJECT, or HUMAN_GATE; you are not required to preserve the
prior verdict. Re-declare every field from your current inspection. Commit locators
must be full object IDs. file/artifact/test locators must be absolute paths to
existing files inside the target repository or current run root. A shell command,
Git-status description, or natural-language description is never a file locator.
If no actual test/artifact output file exists, do not invent test/artifact evidence.
Do not merely edit a string: re-check the actual evidence and its SHA-256 bytes.

The deterministic context below contains only control metadata. It does not contain
or interpret peer_message semantics.

--- BEGIN F1 VERDICT CORRECTION CONTROL CONTEXT ---
""" + encoded + b"""
--- END F1 VERDICT CORRECTION CONTROL CONTEXT ---
"""


def reviewer_refresh_prompt(target_repo: Path, target_branch: str) -> bytes:
    return f"""# P6 Reviewer pre-execution freshness turn

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
Return the runtime-enforced reviewer_instruction wrapper with schema_version=1,
message_type=reviewer_instruction, evidence_summary, and complete peer_message.
Do not emit a verdict in this instruction refresh. Python preserves the full JSON bytes.
""".encode("utf-8")


def executor_prompt(
    target_repo: Path, target_branch: str, governance: GovernanceSnapshot
) -> bytes:
    governance_paths = "\n".join(
        f"- {name}: {governance.documents[name].path}" for name in DOCUMENT_ORDER
    )
    return f"""# P6 fresh Executor mutation turn

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

Return the runtime-enforced executor_receipt wrapper with schema_version=1,
message_type=executor_receipt, evidence_summary (<=2000 characters), and peer_message
containing the complete natural-language execution receipt and evidence locators.
You cannot emit verdict, next_instruction, or runtime_transition. The complete JSON
is transported verbatim. When the peer payload is a Reviewer REJECT wrapper, follow
its bounded next_instruction within the same current step.
""".encode("utf-8")


def build_codex_command(
    *,
    codex_bin: str,
    workspace: Path,
    final_path: Path,
    session_mode: str,
    resume_target_thread_id: Optional[str],
    output_schema: Path = SCHEMAS_ROOT / "reviewer_instruction.schema.json",
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
            "--output-schema",
            str(output_schema),
        ]
    )
    if session_mode == RESUME:
        command.extend(["resume", str(resume_target_thread_id), "-"])
    else:
        command.append("-")
    return command


def relative_evidence_path(path: Path, run_root: Path) -> str:
    return path.resolve().relative_to(run_root.resolve()).as_posix()


def describe_progress_event(line: bytes) -> Optional[str]:
    classified = classify_progress_event(line)
    if classified is None:
        return None
    category, kind = classified
    return f"codex_event={kind}" if category == "codex" else (
        f"codex_event=tool_activity item={kind}"
    )


def classify_progress_event(line: bytes) -> Optional[Tuple[str, str]]:
    try:
        event = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(event, dict):
        return None
    event_type = event.get("type")
    if event_type in {"thread.started", "turn.started", "turn.completed", "error"}:
        return "codex", event_type
    if event_type in {"item.started", "item.completed"}:
        item = event.get("item")
        if isinstance(item, dict):
            item_type = item.get("type")
            if item_type in {"command_execution", "mcp_tool_call", "web_search"}:
                return "tool", item_type
    return None


def stream_subprocess(
    *,
    command: Sequence[str],
    workspace: Path,
    environment: Mapping[str, str],
    prompt: bytes,
    events_path: Path,
    stderr_path: Path,
    timeout_seconds: int,
    progress_interval_seconds: float,
    progress_label: str,
) -> Tuple[Optional[int], bytes, bytes, Optional[str]]:
    """Run Codex while teeing raw output and emitting bounded live progress."""
    process: Optional[subprocess.Popen[bytes]] = None
    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    failure: Optional[str] = None
    fallback_lock = threading.Lock()
    fallback_tool_count = 0
    fallback_last_tool_emit: Optional[float] = None
    fallback_last_reported_count = 0

    def record_machine_event(category: str, kind: str) -> None:
        nonlocal fallback_tool_count, fallback_last_tool_emit
        nonlocal fallback_last_reported_count
        reporter = _ACTIVE_PROGRESS
        if reporter is None:
            description = (
                f"codex_event={kind}" if category == "codex"
                else f"codex_event=tool_activity item={kind}"
            )
            emit_progress(f"{progress_label} {description}")
            return
        if reporter.observation_available:
            record_active_progress(
                "codex_activity" if category == "codex" else "tool_activity",
                kind,
            )
            return
        with fallback_lock:
            if category == "codex":
                emit_machine_fallback("codex", kind, 1)
                return
            fallback_tool_count += 1
            now = time.monotonic()
            if (
                fallback_last_tool_emit is None
                or now - fallback_last_tool_emit >= progress_interval_seconds
            ):
                fallback_last_tool_emit = now
                fallback_last_reported_count = fallback_tool_count
                emit_machine_fallback("tool_activity", kind, fallback_tool_count)
    try:
        process = subprocess.Popen(
            list(command),
            cwd=str(workspace),
            env=dict(environment),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        events_path.write_bytes(b"")
        stderr_path.write_bytes(b"")
        return None, b"", b"", f"unable to launch Codex: {exc}"

    emit_progress(f"{progress_label} process_started pid={process.pid}")

    def pump(
        pipe: Any,
        path: Path,
        destination: bytearray,
        *,
        report_events: bool,
    ) -> None:
        with path.open("wb") as handle:
            while True:
                chunk = pipe.readline()
                if not chunk:
                    break
                destination.extend(chunk)
                handle.write(chunk)
                handle.flush()
                if report_events:
                    classified = classify_progress_event(chunk)
                    if classified is not None:
                        category, kind = classified
                        record_machine_event(category, kind)

    stdout_thread = threading.Thread(
        target=pump,
        args=(process.stdout, events_path, stdout_buffer),
        kwargs={"report_events": True},
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=pump,
        args=(process.stderr, stderr_path, stderr_buffer),
        kwargs={"report_events": False},
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    try:
        assert process.stdin is not None
        process.stdin.write(prompt)
        process.stdin.close()
    except (BrokenPipeError, OSError) as exc:
        failure = f"unable to send prompt to Codex: {exc}"

    started = time.monotonic()
    heartbeat_interval = max(progress_interval_seconds, 0.05)
    next_heartbeat = started + heartbeat_interval
    timed_out = False
    try:
        while process.poll() is None:
            now = time.monotonic()
            if now - started >= timeout_seconds:
                timed_out = True
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                break
            if now >= next_heartbeat:
                record_active_progress("heartbeat")
                emit_progress(
                    f"{progress_label} running elapsed={round(now - started, 1)}s"
                )
                next_heartbeat = now + heartbeat_interval
            time.sleep(min(0.1, heartbeat_interval))
    except BaseException:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
        emit_progress(f"{progress_label} process_interrupted")
        raise

    exit_code = process.wait()
    stdout_thread.join(timeout=5)
    stderr_thread.join(timeout=5)
    if process.stdout is not None:
        process.stdout.close()
    if process.stderr is not None:
        process.stderr.close()
    if stdout_thread.is_alive() or stderr_thread.is_alive():
        failure = failure or "Codex output stream did not close cleanly"
    if (
        _ACTIVE_PROGRESS is not None
        and not _ACTIVE_PROGRESS.observation_available
        and fallback_tool_count > fallback_last_reported_count
    ):
        emit_machine_fallback(
            "tool_activity", "aggregated", fallback_tool_count
        )
    if timed_out:
        failure = f"timeout after {timeout_seconds} seconds"
    emit_progress(
        f"{progress_label} process_finished exit_code={exit_code} "
        f"elapsed={round(time.monotonic() - started, 1)}s"
    )
    return exit_code, bytes(stdout_buffer), bytes(stderr_buffer), failure


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
    progress_interval_seconds: float = 15.0,
    progress_label: Optional[str] = None,
    message_type: str = REVIEWER_INSTRUCTION,
) -> TurnResult:
    if (role == "executor" and message_type != EXECUTOR_RECEIPT) or (
        role == "reviewer" and message_type not in (REVIEWER_INSTRUCTION, REVIEWER_VERDICT)
    ):
        raise InvariantViolation("turn role cannot use the requested schema")
    output_schema = schema_path(message_type)
    output_schema_sha = P4.sha256_file(output_schema)
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
        output_schema=output_schema,
    )
    environment = os.environ.copy()
    environment["CODEX_HOME"] = str(codex_home)
    environment["CODEX_SQLITE_HOME"] = str(codex_home)
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
    progress_turn_started = False

    if validation_failure is None:
        record_active_progress(
            "turn_started", role=role, timeout_seconds=timeout_seconds
        )
        progress_turn_started = True
        exit_code, stdout, stderr, process_failure = stream_subprocess(
            command=command,
            workspace=workspace,
            environment=environment,
            prompt=prompt,
            events_path=events_path,
            stderr_path=stderr_path,
            timeout_seconds=timeout_seconds,
            progress_interval_seconds=progress_interval_seconds,
            progress_label=(
                progress_label or f"role={role} turn={turn_dir.name}"
            ),
        )
        if process_failure is not None:
            failure = process_failure

    duration = round(time.monotonic() - started_monotonic, 3)
    if validation_failure is not None:
        events_path.write_bytes(stdout)
        stderr_path.write_bytes(stderr)
    event_metadata = P4.extract_event_metadata(events_path.read_bytes())
    final_message = final_path.read_bytes() if final_path.is_file() else b""
    success = (
        exit_code == 0
        and bool(final_message)
        and validation_failure is None
        and failure is None
    )
    if not success and failure is None:
        failure = "Codex exited unsuccessfully or did not write a final message"

    observed_thread_id = event_metadata["thread_id"]
    created_thread_id = observed_thread_id if session_mode == NEW_PERSISTENT else None
    observed_resume_thread_id = observed_thread_id if session_mode == RESUME else None
    resume_verified: Optional[bool] = None
    if session_mode == NEW_PERSISTENT and created_thread_id is None:
        success = False
        thread_failure = (
            "persistent Reviewer did not provide a machine-readable thread id"
        )
        failure = f"{failure}; {thread_failure}" if failure else thread_failure
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

    try:
        if P4.sha256_file(output_schema) != output_schema_sha:
            raise InvariantViolation("output schema changed during turn")
        validate_turn_payload(final_message, message_type)
        if (event_metadata["event_parse"]["thread_started_events"] != 1
                or event_metadata["event_parse"]["turn_completed_events"] != 1):
            raise InvariantViolation("turn completion/thread events are missing or ambiguous")
    except (OSError, RuntimeError, ValueError) as exc:
        success = False
        failure = f"{failure}; {exc}" if failure else str(exc)

    process = {
        "authoritative_context": authoritative_evidence,
        "approval_policy": "bypassed",
        "approvals_and_sandbox_bypassed": True,
        "cache_hit_ratio": event_metadata["cache_hit_ratio"],
        "cache_write_input_tokens": event_metadata["cache_write_input_tokens"],
        "cached_input_tokens": event_metadata["cached_input_tokens"],
        "codex_home": str(codex_home),
        "codex_sqlite_home": str(codex_home),
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
        "output_schema": message_type,
        "output_schema_sha256": output_schema_sha,
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
    if progress_turn_started:
        record_active_progress("turn_finished", success=success)
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
    progress_interval_seconds: float = 15.0,
    review: bool = False,
) -> TurnResult:
    policy = choose_freshness_policy(governance, state)
    authoritative = build_authoritative_prompt(
        role_prompt=role_prompt + f"\nRun evidence boundary: {run_root.resolve()}\n".encode("utf-8"),
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
        message_type=REVIEWER_VERDICT if review else REVIEWER_INSTRUCTION,
        prompt=authoritative.prompt,
        session_mode=policy.session_mode,
        resume_target_thread_id=policy.resume_target_thread_id,
        authoritative=authoritative,
        peer_payload=peer_payload,
        peer_payload_offset=authoritative.peer_payload_offset,
        peer_source=peer_source,
        progress_interval_seconds=progress_interval_seconds,
        progress_label=(
            f"run={run_root.name} cycle={cycle_number} role=reviewer "
            f"state=running target_head={target.head} turn={turn_dir.name}"
        ),
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
    evidence_finalization: Optional[Mapping[str, Any]] = None,
    logical_outcome: Optional[Mapping[str, Any]] = None,
    final_result: Optional[Mapping[str, Any]] = None,
    progress: Optional[Mapping[str, Any]] = None,
) -> None:
    manifest = {
        "cycles": list(cycles),
        "evidence_finalization": dict(evidence_finalization or {}),
        "final_result": dict(final_result) if final_result is not None else None,
        "finished_at": P4.utc_now() if status != "RUNNING" else None,
        "governance_initial": governance_initial.metadata(),
        "logical_outcome": dict(logical_outcome) if logical_outcome is not None else None,
        "progress": dict(progress) if progress is not None else None,
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


def emit_final_result(result: Mapping[str, Any]) -> None:
    """Print one bounded F1 terminal summary; never include raw peer content."""
    public = public_final_result(result)
    print("FINAL_RESULT", flush=True)
    for name in FINAL_RESULT_FIELDS:
        print(f"{name}={terminal_scalar(public[name])}", flush=True)


def failure_result_for_main(
    args: argparse.Namespace, exc: BaseException, *, exit_code: int = 1
) -> Dict[str, Any]:
    """Recover bounded status for failures raised before orchestrate can return."""
    run_id = getattr(args, "run_id", "unavailable")
    run_root = args.runs_root.resolve() / run_id
    checkpoint: Dict[str, Any] = {}
    try:
        store = CheckpointStore(checkpoint_path_for_args(args))
        if store.exists():
            checkpoint = store.load()
            if isinstance(checkpoint.get("run_id"), str):
                run_id = checkpoint["run_id"]
            if isinstance(checkpoint.get("run_root"), str):
                run_root = Path(checkpoint["run_root"]).resolve()
    except (OSError, RuntimeError, ValueError):
        checkpoint = {}
    logical = checkpoint.get("logical_outcome")
    outcome = logical if isinstance(logical, dict) else {}
    if checkpoint.get("runtime_transition_applied") is True:
        runtime_status = "APPLIED"
    elif checkpoint.get("state") in {
        RUNTIME_TRANSITION_PENDING, RUNTIME_TRANSITION_COMMITTED
    }:
        runtime_status = "PENDING"
    else:
        runtime_status = "NOT_APPLIED"
    if checkpoint.get("framework_evidence_pushed") is True:
        publication = "PUSHED"
    elif checkpoint.get("framework_evidence_committed") is True:
        publication = "COMMITTED"
    elif p63_enabled(args) and isinstance(logical, dict):
        publication = "PENDING"
    else:
        publication = "NOT_STARTED" if p63_enabled(args) else "NOT_ENABLED"
    return public_final_result({
        "error_code": control_error_code(exc),
        "evidence_publication": publication,
        "exit_code": exit_code,
        "logical_outcome": outcome.get("state", "PREFLIGHT_FAILED"),
        "reason": (
            exc.public_reason
            if isinstance(exc, ControlFailure)
            else "mutation loop could not complete; inspect checkpoint and local evidence"
        ),
        "run_id": run_id,
        "run_root": str(run_root),
        "runtime_transition": runtime_status,
    })


def workload_id_for_args(args: argparse.Namespace) -> str:
    requested = getattr(args, "workload_id", None)
    candidate = requested or args.workload_static.resolve().parent.name
    return P4.validate_run_id(candidate)


def p63_enabled(args: argparse.Namespace) -> bool:
    """CLI namespaces always opt in; older programmatic P6 fixtures remain valid."""
    return getattr(args, "framework_repo", None) is not None


def framework_repo_for_args(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "framework_repo", FRAMEWORK_ROOT)).resolve()


def summary_path_for_args(args: argparse.Namespace, run_id: str) -> Path:
    root = Path(getattr(args, "summary_root", DEFAULT_SUMMARY_ROOT)).resolve()
    return root / f"{P4.validate_run_id(run_id)}.md"


def framework_settings(args: argparse.Namespace) -> Dict[str, str]:
    repo = framework_repo_for_args(args)
    branch = getattr(args, "framework_branch", "main")
    remote = getattr(args, "framework_remote", "origin")
    push_ref = getattr(args, "framework_push_ref", f"refs/heads/{branch}")
    return {
        "branch": branch,
        "push_ref": push_ref,
        "remote": remote,
        "repo": str(repo),
    }


def checkpoint_path_for_args(args: argparse.Namespace) -> Path:
    state_root = getattr(args, "state_root", DEFAULT_STATE_ROOT)
    return state_root.resolve() / workload_id_for_args(args) / "checkpoint.json"


def checkpoint_configuration(args: argparse.Namespace) -> Dict[str, Any]:
    state_root = getattr(args, "state_root", DEFAULT_STATE_ROOT)
    configuration = {
        "codex_bin": str(Path(shutil.which(args.codex_bin) or args.codex_bin).resolve()),
        "executor_home": str(args.executor_home.resolve()),
        "enable_runtime_transition": bool(getattr(args, "enable_runtime_transition", False)),
        "turn_schema_hashes": {name: P4.sha256_file(schema_path(name)) for name in TURN_SCHEMAS},
        "framework_runtime": str(args.framework_runtime.resolve()),
        "framework_static": str(args.framework_static.resolve()),
        "max_cycles": args.max_cycles,
        "max_review_correction_attempts": MAX_REVIEW_CORRECTION_ATTEMPTS,
        "operator_config_identity": copy.deepcopy(
            getattr(args, "operator_config_identity", None)
        ),
        "progress_contract_version": PROGRESS.SCHEMA_VERSION,
        "progress_events_filename": PROGRESS.EVENTS_FILENAME,
        "progress_status_filename": PROGRESS.STATUS_FILENAME,
        "reviewer_home": str(args.reviewer_home.resolve()),
        "runs_root": str(args.runs_root.resolve()),
        "state_root": str(state_root.resolve()),
        "target_branch": args.target_branch,
        "target_repo": str(args.target_repo.resolve()),
        "timeout_seconds": args.timeout_seconds,
        "workload_id": workload_id_for_args(args),
        "workload_runtime": str(args.workload_runtime.resolve()),
        "workload_static": str(args.workload_static.resolve()),
    }
    if p63_enabled(args):
        settings = framework_settings(args)
        configuration.update({
            "evidence_summary": str(summary_path_for_args(args, args.run_id)),
            "framework_branch": settings["branch"],
            "framework_push_ref": settings["push_ref"],
            "framework_remote": settings["remote"],
            "framework_repo": settings["repo"],
        })
    return configuration


def checkpoint_configuration_matches(
    saved: Any, current: Mapping[str, Any]
) -> bool:
    """Compare config exactly, treating a pre-F3 legacy omission as legacy null.

    This compatibility is only available when the current invocation is also a
    legacy long-argument invocation.  A config-backed invocation never upgrades
    or adopts an old checkpoint.
    """
    if not isinstance(saved, dict):
        return False
    normalized = dict(saved)
    if (
        "operator_config_identity" not in normalized
        and current.get("operator_config_identity") is None
    ):
        normalized["operator_config_identity"] = None
    return normalized == current


def target_state_from_metadata(value: Mapping[str, Any]) -> TargetState:
    required = ("repo", "branch", "head", "clean", "status_porcelain")
    if any(name not in value for name in required):
        raise InvariantViolation("checkpoint target metadata is incomplete")
    if not isinstance(value["repo"], str) or not isinstance(value["branch"], str):
        raise InvariantViolation("checkpoint target path/branch is invalid")
    if not isinstance(value["head"], str) or type(value["clean"]) is not bool:
        raise InvariantViolation("checkpoint target HEAD/cleanliness is invalid")
    if not isinstance(value["status_porcelain"], str):
        raise InvariantViolation("checkpoint target porcelain is invalid")
    return TargetState(
        repo=Path(value["repo"]),
        branch=value["branch"],
        head=value["head"],
        clean=value["clean"],
        porcelain=value["status_porcelain"],
    )


def next_turn_attempt(base: Path) -> Path:
    if not base.exists():
        return base
    attempt = 2
    while True:
        candidate = base.with_name(f"{base.name}-attempt-{attempt:02d}")
        if not candidate.exists():
            return candidate
        attempt += 1


def completed_turn_from_dir(turn_dir: Path, run_root: Path) -> Optional[TurnResult]:
    final_path = turn_dir / "final.txt"
    process_path = turn_dir / "process.json"
    if not final_path.is_file() or not process_path.is_file():
        return None
    try:
        process = json.loads(process_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(process, dict) or not process.get("success"):
        return None
    final_message = final_path.read_bytes()
    expected = process.get("final_message_sha256")
    if not final_message or expected != P4.sha256_bytes(final_message):
        return None
    validate_turn_payload(final_message, process.get("output_schema"))
    try:
        relative_evidence_path(final_path, run_root)
    except ValueError:
        return None
    return TurnResult(turn_dir, final_message, process)


def recover_reviewer_state_from_turn(turn: TurnResult) -> ReviewerState:
    context = turn.process.get("authoritative_context")
    state_after = turn.process.get("reviewer_state_after")
    if not isinstance(context, dict) or not isinstance(state_after, dict):
        raise InvariantViolation("completed Reviewer artifact lacks recovery metadata")
    known_hashes = context.get("current_hashes")
    if not isinstance(known_hashes, dict):
        raise InvariantViolation("completed Reviewer artifact lacks governance hashes")
    return ReviewerState(
        reviewer_thread_id=state_after.get("reviewer_thread_id"),
        known_hashes=copy.deepcopy(known_hashes),
        cycle_number=state_after.get("cycle_number"),
        known_target_head=state_after.get("reviewer_known_target_head"),
    )


def load_correction_turn_reference(
    reference: Mapping[str, Any], run_root: Path
) -> TurnResult:
    try:
        return load_turn_reference(reference, run_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction references missing or changed turn evidence",
        ) from exc


def validate_verdict_correction_record(
    record: Mapping[str, Any], run_root: Path
) -> None:
    """Reject incomplete/tampered correction bookkeeping without guessing."""
    if (
        record.get("schema_version") != 1
        or record.get("maximum_attempts") != MAX_REVIEW_CORRECTION_ATTEMPTS
        or type(record.get("attempts_completed")) is not int
        or type(record.get("attempts_started")) is not int
        or not isinstance(record.get("attempts"), list)
        or not isinstance(record.get("evidence_guards"), list)
    ):
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction checkpoint metadata is incomplete",
        )
    attempts = record["attempts"]
    if record["attempts_completed"] != len(attempts):
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction attempt count differs from recorded turns",
        )
    if not (
        record["attempts_completed"]
        <= record["attempts_started"]
        <= min(record["attempts_completed"] + 1, MAX_REVIEW_CORRECTION_ATTEMPTS)
    ):
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction started-attempt count is inconsistent",
        )
    if not 0 <= len(attempts) <= MAX_REVIEW_CORRECTION_ATTEMPTS:
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction attempt count is outside its fixed bound",
        )
    guards = record["evidence_guards"]
    if len(guards) not in {len(attempts), len(attempts) + 1}:
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction evidence-guard sequence is invalid",
        )
    if any(
        not isinstance(guard, dict)
        or not isinstance(guard.get("source_verdict_sha256"), str)
        or not isinstance(guard.get("entries"), list)
        for guard in guards
    ):
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction evidence-guard content is invalid",
        )
    original = record.get("original_verdict_reference")
    source = record.get("source_verdict_reference")
    if not isinstance(original, dict) or not isinstance(source, dict):
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction verdict identity is incomplete",
        )
    original_turn = load_correction_turn_reference(original, run_root)
    reviewer_thread_id = record.get("reviewer_thread_id")
    if (
        not isinstance(reviewer_thread_id, str)
        or original_turn.process.get("output_schema") != REVIEWER_VERDICT
        or original_turn.process.get("thread_id") != reviewer_thread_id
    ):
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction original verdict identity is invalid",
        )
    expected_source = original
    expected_guard_sources = [original["final_sha256"]]
    for index, attempt in enumerate(attempts, start=1):
        if not isinstance(attempt, dict) or attempt.get("attempt") != index:
            raise ControlFailure(
                ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                "Reviewer correction turn sequence is invalid",
            )
        reference = attempt.get("turn_reference")
        if not isinstance(reference, dict):
            raise ControlFailure(
                ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                "Reviewer correction turn reference is incomplete",
            )
        turn = load_correction_turn_reference(reference, run_root)
        if (
            turn.process.get("output_schema") != REVIEWER_VERDICT
            or turn.process.get("thread_id") != reviewer_thread_id
            or turn.process.get("resume_target_thread_id") != reviewer_thread_id
            or turn.process.get("resume_relationship_verified") is not True
        ):
            raise ControlFailure(
                ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                "Reviewer correction turn schema identity is invalid",
            )
        expected_source = reference
        expected_guard_sources.append(reference["final_sha256"])
    if source != expected_source:
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction source verdict is not the latest completed turn",
        )
    if [guard.get("source_verdict_sha256") for guard in guards] != expected_guard_sources[:len(guards)]:
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction evidence guard is not bound to its verdict sequence",
        )
    pending = record.get("pending")
    if pending is not None:
        if (
            not isinstance(pending, dict)
            or pending.get("attempt") != len(attempts) + 1
            or pending.get("attempt") > MAX_REVIEW_CORRECTION_ATTEMPTS
            or pending.get("source_verdict_reference") != source
            or pending.get("error_code") not in {
                code.value for code in CORRECTABLE_VERDICT_CODES
            }
            or not isinstance(pending.get("reason"), str)
        ):
            raise ControlFailure(
                ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                "Reviewer correction pending plan is inconsistent",
            )


def validate_executor_for_correction(
    *,
    executor: Optional[TurnResult],
    executor_reference: Any,
    args: argparse.Namespace,
    target: TargetState,
    target_after_metadata: Any,
    governance: GovernanceSnapshot,
    run_root: Path,
) -> None:
    if executor is None or not isinstance(executor_reference, dict):
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction lacks a checkpointed Executor receipt",
        )
    checkpointed = load_correction_turn_reference(executor_reference, run_root)
    process = checkpointed.process
    if (
        process.get("role") != "executor"
        or process.get("output_schema") != EXECUTOR_RECEIPT
        or process.get("codex_home") != str(args.executor_home.resolve())
        or process.get("session_mode") != FRESH_EPHEMERAL
        or process.get("target_after") != target.metadata()
        or process.get("governance_hashes") != governance.hashes()
        or not isinstance(target_after_metadata, dict)
        or target_after_metadata != target.metadata()
        or checkpointed.final_message != executor.final_message
    ):
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "checkpointed Executor receipt does not match current authoritative state",
        )


def validate_framework_for_correction(
    *,
    args: argparse.Namespace,
    framework_initial: Optional[Mapping[str, Any]],
    summary_path: Optional[Path],
) -> None:
    if not p63_enabled(args):
        return
    if not isinstance(framework_initial, Mapping) or summary_path is None:
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction lacks framework preimage metadata",
        )
    settings = framework_settings(args)
    try:
        current = P63.capture_framework(
            repo=Path(settings["repo"]),
            branch=settings["branch"],
            remote=settings["remote"],
            push_ref=settings["push_ref"],
            require_clean=False,
        )
    except P63.EvidenceError as exc:
        raise InvariantViolation(str(exc)) from exc
    identity_fields = ("branch", "head", "push_ref", "remote", "remote_head", "remote_url", "repo")
    if any(current.get(name) != framework_initial.get(name) for name in identity_fields):
        raise InvariantViolation("framework identity changed before Reviewer correction")
    permitted = []
    relative = P63.relative_repo_path(Path(settings["repo"]), summary_path)
    if summary_path.exists() and relative is not None:
        permitted.append(relative)
    if current.get("changes") != sorted(permitted):
        raise InvariantViolation("framework changes exceed the in-progress evidence summary")


def validate_framework_preflight(args: argparse.Namespace) -> Dict[str, Any]:
    settings = framework_settings(args)
    repo = Path(settings["repo"])
    summary_path = summary_path_for_args(args, args.run_id)
    runs_root = args.runs_root.resolve()
    state_root = getattr(args, "state_root", DEFAULT_STATE_ROOT).resolve()
    if paths_overlap(repo, args.target_repo):
        raise InvariantViolation(
            "target repository and framework repository must be independent, non-overlapping trees"
        )
    for label, path in (
        ("framework Static", args.framework_static.resolve()),
        ("framework Runtime", args.framework_runtime.resolve()),
        ("tracked summary", summary_path),
    ):
        if not P4.path_is_within(path, repo):
            raise InvariantViolation(f"{label} must be inside the configured framework repository")
    if not P4.path_is_within(summary_path, Path(getattr(args, "summary_root")).resolve()):
        raise InvariantViolation("summary path escapes the configured summary root")
    if paths_overlap(summary_path, runs_root) or paths_overlap(summary_path, state_root):
        raise InvariantViolation("tracked summary overlaps local raw/state storage")
    if paths_overlap(runs_root, state_root):
        raise InvariantViolation("runs root and checkpoint state root must be distinct")
    for governance_path in (
        args.framework_static, args.framework_runtime,
        args.workload_static, args.workload_runtime,
    ):
        if summary_path == governance_path.resolve():
            raise InvariantViolation("tracked summary must be distinct from governance inputs")
    for label, local_root in (("runs root", runs_root), ("state root", state_root)):
        if P4.path_is_within(local_root, repo):
            relative = local_root.relative_to(repo)
            probe = relative / ".1pcloop-ignore-probe"
            completed = subprocess.run(
                ["git", "check-ignore", "-q", "--no-index", "--", probe.as_posix()],
                cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            if completed.returncode != 0:
                raise InvariantViolation(f"{label} inside framework repository must be Git-ignored")
    if summary_path.is_symlink() or summary_path.parent.is_symlink():
        raise InvariantViolation("tracked summary path must not use a symlink")
    try:
        state = P63.capture_framework(
            repo=repo,
            branch=settings["branch"],
            remote=settings["remote"],
            push_ref=settings["push_ref"],
            require_clean=not bool(getattr(args, "resume", False)),
        )
    except P63.EvidenceError as exc:
        raise InvariantViolation(str(exc)) from exc
    if not getattr(args, "resume", False):
        if state["remote_head"] != state["head"]:
            raise InvariantViolation(
                "framework remote ref must equal the local framework HEAD before a new run"
            )
        if summary_path.exists():
            raise InvariantViolation("tracked evidence summary already exists for this run ID")
    return state


def validate_preflight(args: argparse.Namespace) -> Tuple[TargetState, GovernanceSnapshot]:
    target_repo = args.target_repo.resolve()
    runs_root = args.runs_root.resolve()
    state_root = getattr(args, "state_root", DEFAULT_STATE_ROOT).resolve()
    framework_repo = framework_repo_for_args(args)
    if paths_overlap(target_repo, framework_repo):
        raise InvariantViolation(
            "target repository and framework repository must be independent, non-overlapping trees"
        )
    if paths_overlap(target_repo, runs_root):
        raise InvariantViolation(
            "runs root must be outside the target repository to preserve target cleanliness"
        )
    if paths_overlap(target_repo, state_root):
        raise InvariantViolation(
            "checkpoint state root must be outside the target repository"
        )
    workload_id_for_args(args)
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
    if p63_enabled(args):
        validate_framework_preflight(args)
    validate_json_schema({}, {"type": "object"})
    for name in TURN_SCHEMAS:
        strict_json(schema_path(name).read_bytes())
    validate_role_runtime_homes(args.reviewer_home, args.executor_home)
    if getattr(args, "enable_runtime_transition", False):
        validate_runtime_destination(args)
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
    progress_interval_seconds: float = 15.0,
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
        progress_interval_seconds=progress_interval_seconds,
    )
    freshness["refresh_performed"] = refresh.success
    freshness["replacement_instruction_path"] = (
        relative_evidence_path(refresh.turn_dir / "final.txt", run_root)
        if refresh.final_message
        else None
    )
    return refresh, current, refresh, freshness


def runtime_state(content: bytes) -> Tuple[Dict[str, Any], int, int]:
    if content.count(RUNTIME_STATE_BEGIN) != 1 or content.count(RUNTIME_STATE_END) != 1:
        raise InvariantViolation("Runtime requires exactly one begin/end machine block")
    start = content.index(RUNTIME_STATE_BEGIN) + len(RUNTIME_STATE_BEGIN)
    end = content.index(RUNTIME_STATE_END)
    if start >= end:
        raise InvariantViolation("Runtime machine markers are out of order")
    value = strict_json(content[start:end])
    validate_json_schema(value, {
        "type": "object", "additionalProperties": False,
        "required": ["schema_version", "workload_id", "transition_mode", "active_step", "last_transition_id"],
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "workload_id": {"type": "string", "minLength": 1},
            "transition_mode": {"enum": ["reviewer_accept_once", "disabled"]},
            "active_step": {
                "type": "object", "additionalProperties": False,
                "required": ["id", "status"],
                "properties": {
                    "id": {"type": "string", "minLength": 1, "maxLength": 128},
                    "status": {"enum": ["ACTIVE", "COMPLETED"]},
                },
            },
            "last_transition_id": {"type": ["string", "null"]},
        },
    })
    return value, start, end


def plan_verdict_correction(
    *,
    current_reference: Mapping[str, Any],
    error: ControlFailure,
    evidence_guard: Sequence[Mapping[str, Any]],
    existing: Optional[Mapping[str, Any]],
    run_root: Path,
) -> Dict[str, Any]:
    if not error.correctable or error.code not in CORRECTABLE_VERDICT_CODES:
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "non-correctable failure cannot create a Reviewer correction plan",
        )
    current_turn = load_correction_turn_reference(current_reference, run_root)
    current_thread_id = current_turn.process.get("thread_id")
    if not isinstance(current_thread_id, str) or not current_thread_id:
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction source has no verified thread identity",
        )
    if existing is None:
        record: Dict[str, Any] = {
            "attempts": [],
            "attempts_completed": 0,
            "attempts_started": 0,
            "evidence_guards": [{
                "entries": copy.deepcopy(list(evidence_guard)),
                "source_verdict_sha256": current_reference["final_sha256"],
            }],
            "maximum_attempts": MAX_REVIEW_CORRECTION_ATTEMPTS,
            "original_verdict_reference": copy.deepcopy(dict(current_reference)),
            "pending": None,
            "reviewer_thread_id": current_thread_id,
            "schema_version": 1,
            "source_verdict_reference": copy.deepcopy(dict(current_reference)),
        }
    else:
        record = copy.deepcopy(dict(existing))
        validate_verdict_correction_record(record, run_root)
        if record.get("source_verdict_reference") != dict(current_reference):
            raise ControlFailure(
                ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                "Reviewer correction source differs from the routed verdict",
            )
        if record.get("reviewer_thread_id") != current_thread_id:
            raise ControlFailure(
                ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                "Reviewer correction source thread differs from the original Reviewer",
            )
        record["evidence_guards"].append({
            "entries": copy.deepcopy(list(evidence_guard)),
            "source_verdict_sha256": current_reference["final_sha256"],
        })
    attempt = record["attempts_completed"] + 1
    if attempt > MAX_REVIEW_CORRECTION_ATTEMPTS:
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_EXHAUSTED,
            "Reviewer verdict correction exhausted after 2 completed attempts",
        )
    record["pending"] = {
        "attempt": attempt,
        "error_code": error.code.value,
        "reason": error.public_reason,
        "source_verdict_reference": copy.deepcopy(dict(current_reference)),
    }
    validate_verdict_correction_record(record, run_root)
    return record


def correction_control_context(
    *,
    correction: Mapping[str, Any],
    executor_reference: Mapping[str, Any],
    target: TargetState,
    governance: GovernanceSnapshot,
    run_root: Path,
) -> Dict[str, Any]:
    validate_verdict_correction_record(correction, run_root)
    pending = correction.get("pending")
    if not isinstance(pending, dict):
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction has no pending attempt",
        )
    machine, _, _ = runtime_state(governance.documents[WORKLOAD_RUNTIME].content)

    def absolute_final(reference: Mapping[str, Any]) -> str:
        relative = reference.get("final_path")
        if not isinstance(relative, str):
            raise ControlFailure(
                ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                "Reviewer correction evidence reference is incomplete",
            )
        path = (run_root / relative).resolve()
        try:
            path.relative_to(run_root.resolve())
        except ValueError as exc:
            raise ControlFailure(
                ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                "Reviewer correction evidence reference escapes the run root",
            ) from exc
        return str(path)

    original = correction["original_verdict_reference"]
    source = correction["source_verdict_reference"]
    return {
        "active_step": copy.deepcopy(machine["active_step"]),
        "attempt": pending["attempt"],
        "commit_locator_rule": "full commit object ID reachable from target HEAD",
        "current_invalid_verdict": {
            "locator": absolute_final(source),
            "sha256": source["final_sha256"],
        },
        "error": {
            "code": pending["error_code"],
            "reason": pending["reason"],
        },
        "evidence_boundary": {
            "run_root": str(run_root.resolve()),
            "target_repo": str(target.repo.resolve()),
        },
        "executor_receipt": {
            "locator": absolute_final(executor_reference),
            "sha256": executor_reference["final_sha256"],
        },
        "file_locator_rule": (
            "file/artifact/test must name an existing absolute file inside "
            "target_repo or run_root; commands, Git status, and prose are invalid"
        ),
        "governance_hashes": governance.hashes(),
        "maximum_attempts": correction["maximum_attempts"],
        "original_verdict": {
            "locator": absolute_final(original),
            "sha256": original["final_sha256"],
        },
        "reviewer_thread_id": correction["reviewer_thread_id"],
        "run_root": str(run_root.resolve()),
        "schema_version": 1,
        "target": target.metadata(),
    }


def validate_runtime_destination(args: argparse.Namespace) -> Path:
    """No output path ever comes from an Agent. Forbid protected-file aliases."""
    requested = args.workload_runtime
    path = requested.resolve()
    protected = [args.framework_static, args.framework_runtime, args.workload_static,
                 DEFAULT_FRAMEWORK_STATIC, DEFAULT_FRAMEWORK_RUNTIME]
    closed = ACTIVE_ROOT / "workloads/multiLanguage_v1"
    protected.extend([closed / "workload_static.md", closed / "workload_runtime.md"])
    if requested.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
        raise InvariantViolation("Runtime destination must be a regular, unaliased file")
    for other in protected:
        if path == other.resolve() or (other.exists() and path.samefile(other)):
            raise InvariantViolation("Runtime destination aliases protected governance")
    for boundary in (args.target_repo, args.runs_root,
                     getattr(args, "state_root", DEFAULT_STATE_ROOT),
                     args.reviewer_home, args.executor_home):
        if paths_overlap(path, boundary):
            raise InvariantViolation("Runtime destination overlaps target/run/state/profile boundary")
    return path


def validate_review_process_authority(
    turn: TurnResult,
    args: argparse.Namespace,
    state: ReviewerState,
    target: TargetState,
    governance: GovernanceSnapshot,
) -> Dict[str, Any]:
    """Verify immutable Reviewer/process authority before wrapper declarations."""
    value = validate_turn_payload(turn.final_message, REVIEWER_VERDICT)
    process = turn.process
    if (process.get("role") != "reviewer" or process.get("success") is not True
            or process.get("exit_code") != 0 or process.get("failure") is not None
            or process.get("codex_home") != str(args.reviewer_home.resolve())
            or process.get("reviewer_target_read_only_verified") is not True
            or process.get("output_schema") != REVIEWER_VERDICT
            or process.get("output_schema_sha256") != P4.sha256_file(schema_path(REVIEWER_VERDICT))
            or process.get("final_message_sha256") != P4.sha256_bytes(turn.final_message)):
        raise ControlFailure(
            ControlErrorCode.REVIEW_PROCESS_AUTHORITY_INVALID,
            "verdict lacks successful Reviewer profile/schema authority",
        )
    thread = process.get("thread_id")
    if not thread or thread != state.reviewer_thread_id:
        raise ControlFailure(
            ControlErrorCode.REVIEW_THREAD_MISMATCH,
            "verdict Reviewer thread does not match checkpoint",
        )
    context = process.get("authoritative_context") or {}
    validation = context.get("validation") or {}
    if (validation.get("source_bytes_verified") is not True
            or validation.get("prompt_bytes_verified") is not True
            or context.get("current_hashes") != governance.hashes()
            or state.known_hashes != governance.hashes()
            or state.known_target_head != target.head):
        raise ControlFailure(
            ControlErrorCode.REVIEW_CONTEXT_STALE,
            "verdict Reviewer governance/target context is stale",
        )
    mode = process.get("session_mode")
    if mode == RESUME:
        if (process.get("resume_relationship_verified") is not True
                or process.get("observed_resume_thread_id") != thread
                or process.get("resume_target_thread_id") != thread
                or context.get("session_known_thread_id") != thread):
            raise ControlFailure(
                ControlErrorCode.REVIEW_RESUME_RELATIONSHIP_INVALID,
                "verdict Reviewer resume relationship is unverified",
            )
    elif mode == NEW_PERSISTENT:
        policy = context.get("freshness_policy") or {}
        if (process.get("created_thread_id") != thread
                or policy.get("injected_files") != list(DOCUMENT_ORDER)
                or process.get("resume_target_thread_id") is not None):
            raise ControlFailure(
                ControlErrorCode.REVIEW_BOOTSTRAP_INVALID,
                "fresh Reviewer verdict lacks complete persistent bootstrap",
            )
    else:
        raise ControlFailure(
            ControlErrorCode.REVIEW_PROCESS_AUTHORITY_INVALID,
            "verdict requires a persistent/resumed Reviewer",
        )
    if (process.get("reviewer_target_before") != target.metadata()
            or process.get("reviewer_target_after") != target.metadata()):
        raise ControlFailure(
            ControlErrorCode.REVIEW_TARGET_STATE_INVALID,
            "Reviewer process target audit differs from current target state",
        )
    return value


def validate_review_authority(
    turn: TurnResult, args: argparse.Namespace, state: ReviewerState,
    target: TargetState, governance: GovernanceSnapshot,
) -> Dict[str, Any]:
    value = validate_review_process_authority(turn, args, state, target, governance)
    validate_verdict_relationships(value)
    if value["reviewed_target"] != {
        "repo": str(target.repo), "branch": target.branch, "head": target.head,
    }:
        raise correctable_failure(
            ControlErrorCode.VERDICT_REVIEWED_TARGET_MISMATCH,
            "Reviewer verdict target declaration differs from authoritative target state",
        )
    if value["governance_hashes"] != governance.hashes():
        raise correctable_failure(
            ControlErrorCode.VERDICT_GOVERNANCE_HASH_MISMATCH,
            "Reviewer verdict governance declaration differs from authoritative hashes",
        )
    if value["expected_runtime_sha256"] != governance.documents[WORKLOAD_RUNTIME].sha256:
        raise correctable_failure(
            ControlErrorCode.VERDICT_RUNTIME_HASH_MISMATCH,
            "Reviewer verdict Runtime declaration differs from authoritative preimage",
        )
    return value


def validate_accept_evidence(
    value: Mapping[str, Any], target: TargetState, run_root: Path,
) -> None:
    commits = 0
    for item in value["evidence"]:
        locator = item["locator"]
        if item["kind"] == "commit":
            if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", locator) is None:
                raise correctable_failure(
                    ControlErrorCode.EVIDENCE_COMMIT_LOCATOR_INVALID,
                    "commit evidence must use a full object ID",
                )
            try:
                object_type = git_text(target.repo, ["cat-file", "-t", locator])
            except InvariantViolation as exc:
                raise correctable_failure(
                    ControlErrorCode.EVIDENCE_COMMIT_UNRESOLVABLE,
                    "commit evidence object cannot be resolved",
                ) from exc
            if object_type != "commit":
                raise correctable_failure(
                    ControlErrorCode.EVIDENCE_COMMIT_NOT_COMMIT,
                    "commit evidence object is not a commit",
                )
            if not is_ancestor(target.repo, locator, target.head):
                raise correctable_failure(
                    ControlErrorCode.EVIDENCE_COMMIT_UNREACHABLE,
                    "commit evidence is not reachable from target HEAD",
                )
            content = git_bytes(target.repo, ["cat-file", "commit", locator])
            commits += 1
        else:
            path = Path(locator)
            if not path.is_absolute():
                raise correctable_failure(
                    ControlErrorCode.EVIDENCE_LOCATOR_NOT_ABSOLUTE,
                    "file, artifact, and test evidence require an absolute file locator",
                )
            resolved = path.resolve()
            if not (P4.path_is_within(resolved, target.repo)
                    or P4.path_is_within(resolved, run_root)):
                raise correctable_failure(
                    ControlErrorCode.EVIDENCE_LOCATOR_OUTSIDE_BOUNDARY,
                    "file, artifact, or test evidence is outside the target/run boundary",
                )
            if not resolved.is_file():
                raise correctable_failure(
                    ControlErrorCode.EVIDENCE_LOCATOR_MISSING,
                    "file, artifact, or test evidence locator is not an existing file",
                )
            content = resolved.read_bytes()
        if P4.sha256_bytes(content) != item["sha256"]:
            raise correctable_failure(
                ControlErrorCode.EVIDENCE_HASH_MISMATCH,
                "Reviewer evidence SHA-256 differs from the actual object bytes",
            )
    if commits == 0:
        raise correctable_failure(
            ControlErrorCode.EVIDENCE_COMMIT_REQUIRED,
            "ACCEPT requires at least one reachable commit evidence",
        )


def capture_correction_evidence_guard(
    value: Mapping[str, Any], target: TargetState, run_root: Path
) -> List[Dict[str, Any]]:
    """Snapshot resolvable declared objects without repairing their declarations."""
    guarded: List[Dict[str, Any]] = []
    for item in value.get("evidence", []):
        kind = item.get("kind")
        locator = item.get("locator")
        record: Dict[str, Any] = {
            "kind": kind,
            "locator": locator,
            "observed_sha256": None,
            "status": "unresolved",
        }
        if not isinstance(locator, str):
            guarded.append(record)
            continue
        if kind == "commit" and re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", locator):
            completed = subprocess.run(
                ["git", "cat-file", "commit", locator],
                cwd=str(target.repo),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if completed.returncode == 0:
                record["observed_sha256"] = P4.sha256_bytes(completed.stdout)
                record["status"] = "observed"
        elif kind in {"file", "artifact", "test"}:
            path = Path(locator)
            if path.is_absolute():
                resolved = path.resolve()
                if (
                    (P4.path_is_within(resolved, target.repo)
                     or P4.path_is_within(resolved, run_root))
                    and resolved.is_file()
                ):
                    record["resolved_locator"] = str(resolved)
                    record["observed_sha256"] = P4.sha256_file(resolved)
                    record["status"] = "observed"
        guarded.append(record)
    return guarded


def validate_correction_evidence_guards(
    correction: Mapping[str, Any], target: TargetState, run_root: Path
) -> None:
    guards = correction.get("evidence_guards")
    if not isinstance(guards, list):
        raise ControlFailure(
            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
            "Reviewer correction evidence guard is missing",
        )
    for guarded_turn in guards:
        if not isinstance(guarded_turn, dict) or not isinstance(
            guarded_turn.get("entries"), list
        ):
            raise ControlFailure(
                ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                "Reviewer correction evidence guard is invalid",
            )
        for entry in guarded_turn["entries"]:
            if not isinstance(entry, dict):
                raise ControlFailure(
                    ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                    "Reviewer correction evidence-guard entry is invalid",
                )
            if entry.get("status") not in {"observed", "unresolved"}:
                raise ControlFailure(
                    ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                    "Reviewer correction evidence-guard status is invalid",
                )
            if entry.get("status") != "observed":
                continue
            expected = entry.get("observed_sha256")
            if entry.get("kind") == "commit":
                completed = subprocess.run(
                    ["git", "cat-file", "commit", entry.get("locator", "")],
                    cwd=str(target.repo),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                actual = (
                    P4.sha256_bytes(completed.stdout)
                    if completed.returncode == 0 else None
                )
            else:
                locator = entry.get("resolved_locator")
                path = Path(locator) if isinstance(locator, str) else Path("")
                if not (
                    path.is_absolute()
                    and (P4.path_is_within(path, target.repo)
                         or P4.path_is_within(path, run_root))
                    and path.is_file()
                ):
                    actual = None
                else:
                    actual = P4.sha256_file(path)
            if actual != expected:
                raise InvariantViolation(
                    "actual evidence bytes changed after Reviewer correction planning"
                )


def validate_accept(
    *, args: argparse.Namespace, turn: TurnResult, state: ReviewerState,
    target: TargetState, governance: GovernanceSnapshot, run_root: Path,
) -> Dict[str, Any]:
    if not getattr(args, "enable_runtime_transition", False):
        raise ControlFailure(
            ControlErrorCode.RUNTIME_CAPABILITY_DISABLED,
            "Runtime transition CLI capability is disabled",
        )
    path = validate_runtime_destination(args)
    value = validate_review_authority(turn, args, state, target, governance)
    if value["verdict"] != "ACCEPT":
        raise InvariantViolation("Runtime transition requires Reviewer ACCEPT")
    document = governance.documents[WORKLOAD_RUNTIME]
    if path != document.path:
        raise ControlFailure(
            ControlErrorCode.RUNTIME_DESTINATION_MISMATCH,
            "Runtime destination differs from governance input",
        )
    machine, _, _ = runtime_state(document.content)
    if (machine["workload_id"] != workload_id_for_args(args)
            or machine["transition_mode"] != "reviewer_accept_once"
            or machine["last_transition_id"] is not None
            or machine["active_step"]["status"] != "ACTIVE"):
        raise ControlFailure(
            ControlErrorCode.RUNTIME_MACHINE_UNAUTHORIZED,
            "Runtime machine block does not authorize one unused transition",
        )
    if machine["active_step"]["id"] != value["active_step_id"]:
        raise correctable_failure(
            ControlErrorCode.VERDICT_ACTIVE_STEP_MISMATCH,
            "Reviewer active_step_id differs from the authoritative Runtime machine block",
        )
    validate_accept_evidence(value, target, run_root)
    return value


def build_runtime_transition(
    *, preimage: bytes, value: Mapping[str, Any], verdict_path: Path,
    verdict_sha256: str, runtime_path: Path, timestamp: str,
) -> Tuple[Dict[str, Any], bytes]:
    old, start, end = runtime_state(preimage)
    preimage_sha = P4.sha256_bytes(preimage)
    identity = json.dumps([str(runtime_path), preimage_sha, verdict_sha256],
                          ensure_ascii=True, separators=(",", ":")).encode("ascii")
    transition_id = P4.sha256_bytes(identity)
    new = copy.deepcopy(old)
    new["active_step"]["status"] = value["runtime_transition"]["new_status"]
    new["transition_mode"] = "disabled"
    new["last_transition_id"] = transition_id
    record = {
        "schema_version": 1, "transition_id": transition_id,
        "accepted_preimage_sha256": preimage_sha,
        "old_state": old, "new_state": new,
        "reviewer_verdict_locator": str(verdict_path),
        "reviewer_verdict_sha256": verdict_sha256,
        "target_head": value["reviewed_target"]["head"],
        "evidence": value["evidence"], "timestamp": timestamp,
    }
    # ASCII JSON escapes angle brackets so arbitrary identifiers/locators cannot
    # inject another Markdown marker or alter the historical record boundary.
    def encoded(obj: Any) -> bytes:
        return json.dumps(obj, ensure_ascii=True, sort_keys=True, indent=2).replace(
            "<", "\\u003c").replace(">", "\\u003e").encode("ascii")
    result = (preimage[:start] + b"\n" + encoded(new) + b"\n" + preimage[end:]
              + b"\n\n<!-- 1PCLOOP_RUNTIME_TRANSITION_RECORD -->\n```json\n"
              + encoded(record) + b"\n```\n")
    plan = {
        "transition_id": transition_id, "preimage_sha256": preimage_sha,
        "postimage_sha256": P4.sha256_bytes(result),
        "preimage_hex": preimage.hex(), "record": record,
    }
    return plan, result


def atomic_replace_runtime(path: Path, preimage: bytes, postimage: bytes) -> None:
    """Same-directory durable replace; never expose a partly written Runtime."""
    temporary: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(prefix=f".{path.name}.tmp-", dir=path.parent,
                                         delete=False) as handle:
            temporary = Path(handle.name)
            os.fchmod(handle.fileno(), path.stat().st_mode & 0o777)
            handle.write(postimage)
            handle.flush()
            os.fsync(handle.fileno())
        if path.read_bytes() != preimage:
            raise InvariantViolation("Runtime preimage changed immediately before atomic replace")
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def snapshot_with_runtime_preimage(
    snapshot: GovernanceSnapshot, preimage: bytes,
) -> GovernanceSnapshot:
    documents = dict(snapshot.documents)
    documents[WORKLOAD_RUNTIME] = replace(
        documents[WORKLOAD_RUNTIME], content=preimage,
        sha256=P4.sha256_bytes(preimage), byte_length=len(preimage),
        line_count=P4.count_lines(preimage),
    )
    return GovernanceSnapshot(documents)


def reconcile_runtime_transition(
    *, plan: Mapping[str, Any], args: argparse.Namespace, turn: TurnResult,
    state: ReviewerState, run_root: Path, governance_paths: Mapping[str, Path],
    committed: bool = False,
) -> None:
    """Revalidate one checkpointed plan; accept only its exact pre/postimage."""
    try:
        preimage = bytes.fromhex(plan["preimage_hex"])
        timestamp = plan["record"]["timestamp"]
    except (KeyError, TypeError, ValueError) as exc:
        raise InvariantViolation("Runtime transition checkpoint is incomplete") from exc
    current = capture_governance(governance_paths)
    document = current.documents[WORKLOAD_RUNTIME]
    target = capture_target_state(args.target_repo, args.target_branch, require_clean=True)
    value = validate_accept(args=args, turn=turn, state=state, target=target,
                            governance=snapshot_with_runtime_preimage(current, preimage),
                            run_root=run_root)
    expected_plan, postimage = build_runtime_transition(
        preimage=preimage, value=value, verdict_path=turn.turn_dir / "final.txt",
        verdict_sha256=P4.sha256_bytes(turn.final_message), runtime_path=document.path,
        timestamp=timestamp,
    )
    if plan != expected_plan:
        raise InvariantViolation("Runtime transition plan does not match authoritative evidence")
    validate_snapshot_sources(current)
    if document.content == postimage:
        machine, _, _ = runtime_state(document.content)
        if machine["last_transition_id"] != plan["transition_id"]:
            raise InvariantViolation("Runtime postimage transition ID mismatch")
        emit_progress(f"transition={plan['transition_id']} already_applied=true")
        return
    if committed or document.content != preimage:
        raise InvariantViolation("Runtime is neither the permitted preimage nor committed postimage")
    atomic_replace_runtime(document.path, preimage, postimage)
    if document.path.read_bytes() != postimage:
        raise InvariantViolation("Runtime post-write verification failed")
    machine, _, _ = runtime_state(postimage)
    if machine["last_transition_id"] != plan["transition_id"]:
        raise InvariantViolation("Runtime post-write state verification failed")
    emit_progress(f"transition={plan['transition_id']} runtime_write_verified=true")


def framework_commit_allowlist(
    args: argparse.Namespace,
    summary_path: Path,
    *,
    include_runtime_transition: bool,
) -> List[Path]:
    repo = framework_repo_for_args(args)
    allowed = [summary_path.resolve()]
    runtime = args.workload_runtime.resolve()
    if include_runtime_transition and P4.path_is_within(runtime, repo):
        allowed.append(runtime)
    return allowed


def turn_summary_context(
    turn: TurnResult,
    *,
    fallback_before: Optional[Mapping[str, Any]],
    fallback_after: Optional[Mapping[str, Any]],
    fallback_hashes: Optional[Mapping[str, str]],
) -> Tuple[Optional[Mapping[str, Any]], Optional[Mapping[str, Any]], Dict[str, str]]:
    process = turn.process
    before = process.get("reviewer_target_before") or process.get("target_before") or fallback_before
    after = process.get("reviewer_target_after") or process.get("target_after") or fallback_after
    context = process.get("authoritative_context")
    hashes = context.get("current_hashes") if isinstance(context, dict) else None
    if not isinstance(hashes, dict):
        hashes = fallback_hashes or {}
    return before, after, dict(hashes)


def orchestrate(
    *,
    args: argparse.Namespace,
    target_initial: TargetState,
    governance_initial: GovernanceSnapshot,
    checkpoint_observer: Optional[
        Callable[[str, Mapping[str, Any]], None]
    ] = None,
) -> Tuple[int, Path]:
    checkpoint_store = CheckpointStore(checkpoint_path_for_args(args))
    resume_requested = bool(getattr(args, "resume", False))
    evidence_finalization_enabled = p63_enabled(args)
    configuration = checkpoint_configuration(args)
    progress_interval = float(getattr(args, "progress_interval_seconds", 15.0))
    summary_path = (
        summary_path_for_args(args, args.run_id)
        if evidence_finalization_enabled else None
    )
    governance_paths = {
        FRAMEWORK_STATIC: args.framework_static.resolve(),
        FRAMEWORK_RUNTIME: args.framework_runtime.resolve(),
        WORKLOAD_STATIC: args.workload_static.resolve(),
        WORKLOAD_RUNTIME: args.workload_runtime.resolve(),
    }
    if resume_requested:
        checkpoint = checkpoint_store.load()
        if (not evidence_finalization_enabled
                and checkpoint["state"] in {HUMAN_GATE, FAILED_CLOSED}):
            raise InvariantViolation("terminal checkpoint has no incomplete work to resume")
        if not checkpoint_configuration_matches(
            checkpoint.get("configuration"), configuration
        ):
            raise InvariantViolation("resume configuration does not match checkpoint")
        run_id = P4.validate_run_id(checkpoint.get("run_id"))
        run_root = Path(checkpoint.get("run_root", "")).resolve()
        if run_root != args.runs_root.resolve() / run_id or not run_root.is_dir():
            raise InvariantViolation("checkpoint run root is missing or inconsistent")
        started_at = checkpoint.get("started_at")
        if not isinstance(started_at, str):
            raise InvariantViolation("checkpoint start time is invalid")
        target_initial = target_state_from_metadata(checkpoint.get("target_initial", {}))
        transition_plan = checkpoint.get("runtime_transition")
        initial_hashes = checkpoint.get("governance_initial_hashes")
        transition_recovery = checkpoint["state"] in {
            RUNTIME_TRANSITION_PENDING, RUNTIME_TRANSITION_COMMITTED
        } or (
            checkpoint["state"] in {
                EVIDENCE_FINALIZATION_PENDING,
                FRAMEWORK_EVIDENCE_COMMITTED,
                FRAMEWORK_EVIDENCE_PUSHED,
            }
            and bool(checkpoint.get("runtime_transition_applied", False))
        )
        if transition_recovery:
            if not isinstance(transition_plan, dict) or not isinstance(initial_hashes, dict):
                raise InvariantViolation("Runtime transition recovery metadata is missing")
            if checkpoint["state"] in {
                RUNTIME_TRANSITION_PENDING, RUNTIME_TRANSITION_COMMITTED
            }:
                last = checkpoint.get("last_state_transition", {})
                allowed_from = ({REVIEW_COMPLETED, RUNTIME_TRANSITION_PENDING}
                                if checkpoint["state"] == RUNTIME_TRANSITION_PENDING
                                else {RUNTIME_TRANSITION_PENDING, RUNTIME_TRANSITION_COMMITTED})
                if last.get("to") != checkpoint["state"] or last.get("from") not in allowed_from:
                    raise InvariantViolation("checkpoint does not permit this Runtime transition state")
            for name, sha in governance_initial.hashes().items():
                allowed = {initial_hashes.get(name)}
                if name == f"{WORKLOAD_RUNTIME}_sha256":
                    allowed.add(transition_plan.get("postimage_sha256"))
                if sha not in allowed:
                    raise InvariantViolation("governance changed outside checkpointed Runtime transition")
            try:
                preimage = bytes.fromhex(transition_plan["preimage_hex"])
            except (KeyError, TypeError, ValueError) as exc:
                raise InvariantViolation("Runtime checkpoint preimage is invalid") from exc
            governance_initial = snapshot_with_runtime_preimage(governance_initial, preimage)
            if governance_initial.hashes() != initial_hashes:
                raise InvariantViolation("Runtime checkpoint preimage does not match initial hashes")
        elif initial_hashes != governance_initial.hashes():
            raise InvariantViolation("governance changed since the checkpointed run began")
        cycles = checkpoint.get("cycles")
        processes = checkpoint.get("processes")
        if not isinstance(cycles, list) or not isinstance(processes, list):
            raise InvariantViolation("checkpoint cycle/process state is invalid")
        reviewer_state = reviewer_state_from_record(
            checkpoint.get("reviewer_state", {})
        )
        run_configuration = checkpoint.get("run_configuration")
        if not isinstance(run_configuration, dict):
            raise InvariantViolation("checkpoint run configuration is invalid")
        state = checkpoint["state"]
        cycle_number = checkpoint.get("cycle_number", 1)
        if type(cycle_number) is not int or cycle_number < 1:
            raise InvariantViolation("checkpoint cycle number is invalid")
        instruction_reference = checkpoint.get("instruction_reference")
        executor_reference = checkpoint.get("executor_reference")
        active_turn_relative = checkpoint.get("active_turn_relative")
        target_before_metadata = checkpoint.get("target_before")
        target_after_metadata = checkpoint.get("target_after")
        summary_progress = checkpoint.get("summary_progress", [])
        summary_pending = checkpoint.get("summary_pending")
        logical_outcome = checkpoint.get("logical_outcome")
        verdict_correction = checkpoint.get("verdict_correction")
        framework_initial = checkpoint.get("framework_initial")
        framework_commit_plan = checkpoint.get("framework_commit_plan")
        framework_commit_id = checkpoint.get("framework_commit_id")
        framework_push_result = checkpoint.get("framework_push_result")
        evidence_finalization_error = checkpoint.get("evidence_finalization_error")
        checkpoint_progress = checkpoint.get("progress")
        runtime_transition_applied = bool(
            checkpoint.get("runtime_transition_applied", False)
        )
        framework_evidence_committed = bool(
            checkpoint.get("framework_evidence_committed", False)
        )
        framework_evidence_pushed = bool(
            checkpoint.get("framework_evidence_pushed", False)
        )
        if not isinstance(summary_progress, list):
            raise InvariantViolation("checkpoint summary progress is invalid")
        if evidence_finalization_enabled:
            if not isinstance(framework_initial, dict):
                raise InvariantViolation("checkpoint framework preimage is missing")
            if summary_path != Path(configuration["evidence_summary"]).resolve():
                raise InvariantViolation("checkpoint summary path is inconsistent")
    else:
        if checkpoint_store.exists():
            previous = checkpoint_store.load()
            completed_states = (
                TERMINAL_CHECKPOINT_STATES
                if evidence_finalization_enabled
                else {RUNTIME_TRANSITION_COMMITTED, HUMAN_GATE, FAILED_CLOSED}
            )
            if previous["state"] not in completed_states:
                raise InvariantViolation(
                    "an incomplete checkpoint exists; use --resume or explicitly remove "
                    "the local checkpoint after Human review"
                )
            previous_plan = previous.get("runtime_transition")
            if isinstance(previous_plan, dict):
                if previous_plan.get("preimage_sha256") == governance_initial.documents[WORKLOAD_RUNTIME].sha256:
                    raise InvariantViolation("an already accepted/planned Runtime preimage cannot start a new run")
        run_id = P4.validate_run_id(args.run_id)
        run_root = args.runs_root.resolve() / run_id
        run_root.mkdir(parents=True, exist_ok=False)
        started_at = P4.utc_now()
        cycles = []
        processes = []
        reviewer_state = ReviewerState(None, None, 0)
        state = PREFLIGHT_PASSED
        cycle_number = 1
        instruction_reference = None
        executor_reference = None
        active_turn_relative = None
        target_before_metadata = None
        target_after_metadata = None
        summary_progress: List[Dict[str, Any]] = []
        summary_pending = None
        logical_outcome = None
        verdict_correction = None
        runtime_transition_applied = False
        transition_plan = None
        initial_hashes = governance_initial.hashes()
        framework_evidence_committed = False
        framework_evidence_pushed = False
        framework_commit_plan = None
        framework_commit_id = None
        framework_push_result = None
        evidence_finalization_error = None
        checkpoint_progress = None
        framework_initial = (
            validate_framework_preflight(args)
            if evidence_finalization_enabled else None
        )
        run_configuration = {
            "approval_policy": "bypassed",
            "approvals_and_sandbox_bypassed": True,
            "checkpoint_path": str(checkpoint_store.path.resolve()),
            "codex_bin": configuration["codex_bin"],
            "executor_home": str(args.executor_home.resolve()),
            "executor_sandbox": NO_CODEX_SANDBOX,
            "executor_session_mode": FRESH_EPHEMERAL,
            "execution_policy": "prompt-defined-roles-with-post-turn-mechanical-audit",
            "framework_git_head": (
                framework_initial["head"] if framework_initial is not None
                else git_text(FRAMEWORK_ROOT, ["rev-parse", "HEAD"])
            ),
            "max_cycles": args.max_cycles,
            "max_review_correction_attempts": MAX_REVIEW_CORRECTION_ATTEMPTS,
            "operator_config_identity": copy.deepcopy(
                configuration.get("operator_config_identity")
            ),
            "reviewer_home": str(args.reviewer_home.resolve()),
            "reviewer_session_mode": "persistent-with-explicit-resume",
            "reviewer_sandbox": NO_CODEX_SANDBOX,
            "runs_root": str(args.runs_root.resolve()),
            "timeout_seconds": args.timeout_seconds,
            "workload_id": workload_id_for_args(args),
        }
        if evidence_finalization_enabled:
            run_configuration["evidence_finalization"] = {
                **framework_settings(args),
                "summary_path": str(summary_path),
            }

    progress_options: Dict[str, Any] = {}
    if getattr(args, "progress_status_writer", None) is not None:
        progress_options["status_writer"] = args.progress_status_writer
    if getattr(args, "progress_append_hook", None) is not None:
        progress_options["append_hook"] = args.progress_append_hook
    progress = PROGRESS.ProgressStatus(
        run_root=run_root,
        run_id=run_id,
        public_text=escape_public_text,
        terminal_scalar=terminal_scalar,
        clock=getattr(args, "progress_clock", None),
        output=getattr(args, "progress_output", sys.stdout),
        is_tty=getattr(args, "progress_is_tty", None),
        tool_throttle_seconds=progress_interval,
        resume=resume_requested,
        checkpoint_progress=checkpoint_progress,
        checkpoint_state=state if resume_requested else None,
        **progress_options,
    )
    global _ACTIVE_PROGRESS
    _ACTIVE_PROGRESS = progress
    run_configuration["progress"] = {
        "contract_version": PROGRESS.SCHEMA_VERSION,
        "events_path": str(progress.events_path),
        "live_status_path": str(progress.status_path),
        "run_elapsed_excludes_stopped_wall_time": True,
        "terminal_mode": "line" if not progress.is_tty else "tty-line",
    }

    def progress_role(checkpoint_state: str) -> str:
        if checkpoint_state in {
            REVIEWER_INSTRUCTION_RUNNING,
            REVIEW_PENDING,
            REVIEW_CORRECTION_PENDING,
            REVIEW_CORRECTION_RUNNING,
        }:
            return "reviewer"
        if checkpoint_state == EXECUTOR_RUNNING:
            return "executor"
        return "orchestrator"

    def progress_target_head() -> Optional[str]:
        for metadata in (target_after_metadata, target_before_metadata):
            if isinstance(metadata, dict) and isinstance(metadata.get("head"), str):
                return metadata["head"]
        if isinstance(reviewer_state.known_target_head, str):
            return reviewer_state.known_target_head
        return target_initial.head

    def progress_projection() -> Tuple[Optional[str], Optional[str], Optional[str]]:
        outcome = (
            logical_outcome.get("state")
            if isinstance(logical_outcome, dict) else None
        )
        if runtime_transition_applied:
            runtime_status: Optional[str] = "APPLIED"
        elif state in {RUNTIME_TRANSITION_PENDING, RUNTIME_TRANSITION_COMMITTED}:
            runtime_status = "PENDING"
        elif outcome is not None:
            runtime_status = "NOT_APPLIED"
        else:
            runtime_status = None
        if framework_evidence_pushed:
            publication: Optional[str] = "PUSHED"
        elif evidence_finalization_error is not None:
            publication = "FAILED"
        elif framework_evidence_committed:
            publication = "COMMITTED"
        elif evidence_finalization_enabled and outcome is not None:
            publication = "PENDING"
        elif not evidence_finalization_enabled:
            publication = "NOT_ENABLED"
        else:
            publication = None
        return outcome, runtime_status, publication

    def structured_final_result(
        *, exit_code_override: Optional[int] = None
    ) -> Dict[str, Any]:
        if runtime_transition_applied:
            runtime_status = "APPLIED"
        elif state in {RUNTIME_TRANSITION_PENDING, RUNTIME_TRANSITION_COMMITTED}:
            runtime_status = "PENDING"
        else:
            runtime_status = "NOT_APPLIED"
        if framework_evidence_pushed:
            publication = "PUSHED"
        elif evidence_finalization_error is not None:
            publication = "FAILED"
        elif framework_evidence_committed:
            publication = "COMMITTED"
        elif evidence_finalization_enabled and isinstance(logical_outcome, dict):
            publication = "PENDING"
        else:
            publication = "NOT_ENABLED" if not evidence_finalization_enabled else "NOT_STARTED"
        outcome = logical_outcome if isinstance(logical_outcome, dict) else {}
        exit_code = outcome.get("exit_code")
        result_reason = outcome.get("reason")
        result_error_code = outcome.get("error_code")
        if evidence_finalization_error is not None:
            exit_code = 1
            result_reason = "evidence publication failed; resume retries finalization only"
            result_error_code = "EVIDENCE_PUBLICATION_FAILED"
        if exit_code_override is not None:
            exit_code = exit_code_override
        return public_final_result({
            "error_code": result_error_code,
            "evidence_publication": publication,
            "exit_code": exit_code,
            "logical_outcome": outcome.get("state", "UNDETERMINED"),
            "reason": result_reason,
            "run_id": run_id,
            "run_root": str(run_root.resolve()),
            "runtime_transition": runtime_status,
        })

    def persist(
        checkpoint_state: str,
        *,
        manifest_status: str = "RUNNING",
        manifest_reason: Optional[str] = None,
    ) -> None:
        nonlocal state
        prior_state = state
        state = checkpoint_state
        projected_outcome, projected_runtime, projected_publication = (
            progress_projection()
        )
        progress_checkpoint = progress.prepare_state(
            control_state=checkpoint_state,
            cycle=cycle_number,
            role=progress_role(checkpoint_state),
            target_head=progress_target_head(),
            logical_outcome=projected_outcome,
            runtime_transition=projected_runtime,
            evidence_publication=projected_publication,
        )
        payload = {
            "active_turn_relative": active_turn_relative,
            "configuration": configuration,
            "cycle_number": cycle_number,
            "cycles": cycles,
            "executor_reference": executor_reference,
            "final_result": structured_final_result(),
            "governance_initial_hashes": initial_hashes,
            "framework_evidence_committed": framework_evidence_committed,
            "framework_evidence_pushed": framework_evidence_pushed,
            "evidence_finalization_error": evidence_finalization_error,
            "framework_commit_id": framework_commit_id,
            "framework_commit_plan": framework_commit_plan,
            "framework_initial": framework_initial,
            "framework_push_result": framework_push_result,
            "instruction_reference": instruction_reference,
            "last_state_transition": {
                "from": prior_state,
                "to": checkpoint_state,
            },
            "logical_outcome": logical_outcome,
            "manifest_reason": manifest_reason,
            "manifest_status": manifest_status,
            "processes": processes,
            "progress": progress_checkpoint,
            "reviewer_state": reviewer_state_record(reviewer_state),
            "runtime_transition_applied": runtime_transition_applied,
            "runtime_transition": transition_plan,
            "run_configuration": run_configuration,
            "run_id": run_id,
            "run_root": str(run_root),
            "started_at": started_at,
            "summary_progress": summary_progress,
            "summary_pending": summary_pending,
            "target_after": target_after_metadata,
            "target_before": target_before_metadata,
            "target_initial": target_initial.metadata(),
            "verdict_correction": verdict_correction,
        }
        written = checkpoint_store.write(checkpoint_state, payload)
        record_active_progress("commit_state")
        write_manifest(
            run_root=run_root,
            run_id=run_id,
            started_at=started_at,
            status=manifest_status,
            reason=manifest_reason,
            target_initial=target_initial,
            governance_initial=governance_initial,
            reviewer_state=reviewer_state,
            cycles=cycles,
            processes=processes,
            run_configuration=run_configuration,
            evidence_finalization={
                "commit_id": framework_commit_id,
                "committed": framework_evidence_committed,
                "error": evidence_finalization_error,
                "pushed": framework_evidence_pushed,
                "push_result": framework_push_result,
                "summary_entries": [
                    item.get("entry_id") for item in summary_progress
                ],
                "summary_path": str(summary_path) if summary_path is not None else None,
            },
            logical_outcome=logical_outcome,
            final_result=structured_final_result(),
            progress=progress.checkpoint_record(),
        )
        if checkpoint_observer is not None:
            checkpoint_observer(checkpoint_state, written)

    def logical_manifest() -> Tuple[str, Optional[str]]:
        if isinstance(logical_outcome, dict):
            return (
                str(logical_outcome.get("manifest_status", "RUNNING")),
                logical_outcome.get("reason"),
            )
        return "RUNNING", None

    def reconcile_pending_summary() -> None:
        nonlocal summary_pending
        if not evidence_finalization_enabled or summary_pending is None:
            return
        assert summary_path is not None
        emit_progress(
            f"run={run_id} summary_entry={summary_pending.get('entry_id')} "
            "state=reconciling"
        )
        record = P63.reconcile_summary_plan(
            plan=summary_pending,
            summary_path=summary_path,
            run_id=run_id,
            run_root=run_root,
            progress=summary_progress,
        )
        if any(item.get("entry_id") == record["entry_id"] for item in summary_progress):
            raise InvariantViolation("pending summary entry is already checkpointed")
        summary_progress.append(record)
        summary_pending = None
        status, reason = logical_manifest()
        persist(state, manifest_status=status, manifest_reason=reason)
        emit_progress(
            f"run={run_id} summary_entry={record['entry_id']} state=reconciled"
        )

    def record_turn_summary(
        turn: TurnResult,
        *,
        fallback_before: Optional[Mapping[str, Any]] = None,
        fallback_after: Optional[Mapping[str, Any]] = None,
        fallback_hashes: Optional[Mapping[str, str]] = None,
    ) -> None:
        nonlocal summary_pending
        if not evidence_finalization_enabled:
            return
        assert summary_path is not None
        structured: Optional[Dict[str, Any]] = None
        if turn.success:
            try:
                structured = validate_turn_payload(
                    turn.final_message, turn.process.get("output_schema")
                )
            except (OSError, RuntimeError, ValueError):
                structured = None
        before, after, hashes = turn_summary_context(
            turn,
            fallback_before=fallback_before,
            fallback_after=fallback_after,
            fallback_hashes=fallback_hashes,
        )
        entry = P63.build_turn_entry(
            run_id=run_id,
            run_root=run_root,
            cycle_number=cycle_number,
            turn_dir=turn.turn_dir,
            process=turn.process,
            structured_payload=structured,
            target_before=before,
            target_after=after,
            governance_hashes=hashes,
        )
        existing = [
            item for item in summary_progress
            if item.get("entry_id") == entry["entry_id"]
        ]
        if existing:
            P63.validate_summary_file(
                summary_path=summary_path,
                run_id=run_id,
                run_root=run_root,
                progress=summary_progress,
            )
            if len(existing) != 1:
                raise InvariantViolation("summary entry ID is not unique")
            emit_progress(
                f"run={run_id} summary_entry={entry['entry_id']} state=already-recorded"
            )
            return
        plan = P63.build_summary_plan(
            summary_path=summary_path,
            run_id=run_id,
            run_root=run_root,
            progress=summary_progress,
            entry=entry,
        )
        summary_pending = plan
        emit_progress(
            f"run={run_id} summary_entry={plan['entry_id']} state=pending"
        )
        status, reason = logical_manifest()
        persist(state, manifest_status=status, manifest_reason=reason)
        P63.reconcile_summary_plan(
            plan=plan,
            summary_path=summary_path,
            run_id=run_id,
            run_root=run_root,
            progress=summary_progress,
        )
        summary_progress.append(plan)
        summary_pending = None
        persist(state, manifest_status=status, manifest_reason=reason)
        emit_progress(
            f"run={run_id} summary_entry={plan['entry_id']} state=written"
        )

    final_result_emitted = False

    def finish_return(exit_code: int) -> Tuple[int, Path]:
        nonlocal final_result_emitted
        global _ACTIVE_PROGRESS
        if not final_result_emitted:
            projected_outcome, projected_runtime, projected_publication = (
                progress_projection()
            )
            progress.prepare_state(
                control_state=state,
                cycle=cycle_number,
                role="orchestrator",
                target_head=progress_target_head(),
                logical_outcome=projected_outcome,
                runtime_transition=projected_runtime,
                evidence_publication=projected_publication,
            )
            record_active_progress(
                "record", "run_finished", activity_kind="run_finished"
            )
            emit_final_result(structured_final_result(exit_code_override=exit_code))
            final_result_emitted = True
            _ACTIVE_PROGRESS = None
        return exit_code, run_root

    def finish_evidence() -> Tuple[int, Path]:
        nonlocal framework_commit_plan, framework_commit_id
        nonlocal framework_evidence_committed, framework_evidence_pushed
        nonlocal framework_push_result, evidence_finalization_error
        if not evidence_finalization_enabled:
            if not isinstance(logical_outcome, dict):
                raise InvariantViolation("logical outcome is missing")
            return finish_return(int(logical_outcome["exit_code"]))
        if not isinstance(logical_outcome, dict) or not isinstance(framework_initial, dict):
            raise InvariantViolation("evidence finalization metadata is incomplete")
        evidence_finalization_error = None
        assert summary_path is not None
        status, reason = logical_manifest()
        P63.validate_summary_file(
            summary_path=summary_path,
            run_id=run_id,
            run_root=run_root,
            progress=summary_progress,
        )
        if state not in {
            EVIDENCE_FINALIZATION_PENDING,
            FRAMEWORK_EVIDENCE_COMMITTED,
            FRAMEWORK_EVIDENCE_PUSHED,
        }:
            emit_progress(
                f"run={run_id} logical_outcome={logical_outcome['state']} "
                "evidence_finalization=pending"
            )
            persist(
                EVIDENCE_FINALIZATION_PENDING,
                manifest_status=status,
                manifest_reason=reason,
            )
            record_active_progress(
                "record", "evidence_finalization",
                activity_kind="evidence_finalization_pending",
            )
        if state == EVIDENCE_FINALIZATION_PENDING:
            settings = framework_settings(args)
            if framework_commit_plan is None:
                framework_commit_plan = P63.build_framework_commit_plan(
                    repo=Path(settings["repo"]),
                    branch=settings["branch"],
                    remote=settings["remote"],
                    push_ref=settings["push_ref"],
                    expected_parent=framework_initial["head"],
                    expected_remote_head=framework_initial["remote_head"],
                    expected_remote_url=framework_initial["remote_url"],
                    run_id=run_id,
                    allowed_paths=framework_commit_allowlist(
                        args,
                        summary_path,
                        include_runtime_transition=runtime_transition_applied,
                    ),
                    required_summary=summary_path,
                )
                emit_progress(f"run={run_id} framework_commit=pending")
                persist(
                    EVIDENCE_FINALIZATION_PENDING,
                    manifest_status=status,
                    manifest_reason=reason,
                )
            framework_commit_id, commit_result = P63.commit_or_reconcile(
                framework_commit_plan
            )
            framework_evidence_committed = True
            emit_progress(
                f"run={run_id} framework_commit={commit_result} "
                f"commit={framework_commit_id}"
            )
            persist(
                FRAMEWORK_EVIDENCE_COMMITTED,
                manifest_status=status,
                manifest_reason=reason,
            )
            record_active_progress(
                "record", "evidence_finalization",
                activity_kind="framework_evidence_committed",
            )
        if state == FRAMEWORK_EVIDENCE_COMMITTED:
            if not isinstance(framework_commit_plan, dict) or not isinstance(
                framework_commit_id, str
            ):
                raise InvariantViolation("framework evidence commit checkpoint is incomplete")
            emit_progress(
                f"run={run_id} framework_push=pending commit={framework_commit_id}"
            )
            framework_push_result = P63.push_or_reconcile(
                framework_commit_plan, framework_commit_id
            )
            framework_evidence_pushed = True
            emit_progress(
                f"run={run_id} framework_push={framework_push_result} "
                f"commit={framework_commit_id}"
            )
            persist(
                FRAMEWORK_EVIDENCE_PUSHED,
                manifest_status=status,
                manifest_reason=reason,
            )
            record_active_progress(
                "record", "evidence_finalization",
                activity_kind="framework_evidence_pushed",
            )
        if state == FRAMEWORK_EVIDENCE_PUSHED:
            if not framework_evidence_committed or not framework_evidence_pushed:
                raise InvariantViolation("final evidence checkpoint flags are incomplete")
            if P63.push_or_reconcile(framework_commit_plan, framework_commit_id) != "already-present":
                raise InvariantViolation("final framework remote verification was not idempotent")
            return finish_return(int(logical_outcome["exit_code"]))
        raise InvariantViolation("unsupported evidence finalization state")

    def reach_logical_outcome(
        outcome_state: str,
        *,
        manifest_status: str,
        reason: str,
        exit_code: int,
        error_code: str,
        diagnostic: Optional[BaseException] = None,
    ) -> Tuple[int, Path]:
        nonlocal logical_outcome
        public_reason = bounded_public_reason(reason, error_code)
        logical_outcome = {
            "exit_code": exit_code,
            "manifest_status": manifest_status,
            "reason": public_reason,
            "state": outcome_state,
            "error_code": error_code,
            "internal_diagnostic": (
                {
                    "exception_type": type(diagnostic).__name__,
                    "reason": str(diagnostic),
                }
                if diagnostic is not None else None
            ),
        }
        persist(
            outcome_state,
            manifest_status=manifest_status,
            manifest_reason=public_reason,
        )
        record_active_progress(
            "record", "logical_outcome", activity_kind="logical_outcome"
        )
        return finish_evidence()

    def active_turn_path(default: Path) -> Path:
        if isinstance(active_turn_relative, str):
            candidate = (run_root / active_turn_relative).resolve()
            try:
                candidate.relative_to(run_root.resolve())
            except ValueError as exc:
                raise InvariantViolation("checkpoint active turn escapes run root") from exc
            return candidate
        return default

    def cycle_for(number: int, instruction: TurnResult) -> Dict[str, Any]:
        for existing in cycles:
            if existing.get("cycle_number") == number:
                return existing
        created: Dict[str, Any] = {
            "cycle_number": number,
            "executor": None,
            "governance_before_executor": None,
            "reviewer_instruction_source": relative_evidence_path(
                instruction.turn_dir / "final.txt", run_root
            ),
            "reviewer_instruction_process": instruction.process,
            "instruction_freshness": None,
            "reviewer_pre_executor_refresh": None,
            "reviewer_corrections": [],
            "reviewer_review": None,
            "verdict_correction": None,
            "reviewer_state_before": copy.deepcopy(reviewer_state.metadata()),
            "target_triggered_instruction_refresh": False,
            "target_after": None,
            "target_before": None,
        }
        cycles.append(created)
        return created

    if not resume_requested:
        persist(PREFLIGHT_PASSED)
    elif evidence_finalization_enabled:
        if summary_pending is not None:
            reconcile_pending_summary()
        else:
            assert summary_path is not None
            P63.validate_summary_file(
                summary_path=summary_path,
                run_id=run_id,
                run_root=run_root,
                progress=summary_progress,
            )
        if state in {
            HUMAN_GATE,
            FAILED_CLOSED,
            EVIDENCE_FINALIZATION_PENDING,
            FRAMEWORK_EVIDENCE_COMMITTED,
            FRAMEWORK_EVIDENCE_PUSHED,
        }:
            return finish_evidence()

    instruction: Optional[TurnResult] = (
        load_turn_reference(instruction_reference, run_root)
        if isinstance(instruction_reference, dict)
        else None
    )
    executor: Optional[TurnResult] = (
        load_turn_reference(executor_reference, run_root)
        if isinstance(executor_reference, dict)
        else None
    )

    try:
        while True:
            cycle_dir = run_root / f"cycle-{cycle_number:02d}"
            cycle_dir.mkdir(exist_ok=True)

            if state in {PREFLIGHT_PASSED, REVIEWER_INSTRUCTION_RUNNING}:
                base = cycle_dir / "reviewer-instruction"
                turn_dir = active_turn_path(base)
                recovered = completed_turn_from_dir(turn_dir, run_root)
                if recovered is not None:
                    try:
                        reviewer_state = recover_reviewer_state_from_turn(recovered)
                    except InvariantViolation:
                        recovered = None
                if recovered is None:
                    if turn_dir.exists():
                        reviewer_state = ReviewerState(None, None, 0)
                        turn_dir = next_turn_attempt(base)
                    active_turn_relative = relative_evidence_path(turn_dir, run_root)
                    persist(REVIEWER_INSTRUCTION_RUNNING)
                    emit_progress(
                        f"run={run_id} cycle={cycle_number} role=reviewer "
                        f"state=instruction_running target_head={target_initial.head}"
                    )
                    recovered = invoke_reviewer(
                        run_root=run_root,
                        turn_dir=turn_dir,
                        target=capture_target_state(
                            target_initial.repo,
                            target_initial.branch,
                            require_clean=True,
                        ),
                        governance=capture_governance(governance_paths),
                        state=reviewer_state,
                        cycle_number=cycle_number,
                        role_prompt=reviewer_initial_prompt(
                            target_initial.repo, target_initial.branch
                        ),
                        peer_payload=None,
                        peer_source=None,
                        codex_bin=args.codex_bin,
                        reviewer_home=args.reviewer_home.resolve(),
                        timeout_seconds=args.timeout_seconds,
                        progress_interval_seconds=progress_interval,
                    )
                if not recovered.success:
                    record_turn_summary(
                        recovered,
                        fallback_before=target_initial.metadata(),
                        fallback_after=target_initial.metadata(),
                        fallback_hashes=initial_hashes,
                    )
                    raise InvariantViolation(
                        f"initial Reviewer process failed: {recovered.process['failure']}"
                    )
                record_turn_summary(
                    recovered,
                    fallback_before=target_initial.metadata(),
                    fallback_after=target_initial.metadata(),
                    fallback_hashes=initial_hashes,
                )
                instruction = recovered
                processes.append(instruction.process)
                instruction_reference = turn_reference(instruction, run_root)
                active_turn_relative = None
                persist(INSTRUCTION_READY)
                continue

            if state == INSTRUCTION_READY:
                if instruction is None:
                    raise InvariantViolation("instruction checkpoint reference is missing")
                cycle = cycle_for(cycle_number, instruction)
                target_for_freshness = capture_target_state(
                    target_initial.repo, target_initial.branch, require_clean=True
                )
                instruction, governance_before, refresh, freshness = (
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
                        progress_interval_seconds=progress_interval,
                    )
                )
                instruction_reference = turn_reference(instruction, run_root)
                cycle["instruction_freshness"] = freshness
                cycle["target_triggered_instruction_refresh"] = bool(
                    freshness["target_head_changed"]
                )
                if refresh is not None:
                    record_turn_summary(
                        refresh,
                        fallback_before=target_for_freshness.metadata(),
                        fallback_after=target_for_freshness.metadata(),
                        fallback_hashes=governance_before.hashes(),
                    )
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
                launch_target = capture_target_state(
                    target_initial.repo, target_initial.branch, require_clean=True
                )
                cycle["target_launch_check"] = launch_target.metadata()
                if launch_target.head != reviewer_state.known_target_head:
                    raise InvariantViolation(
                        "target HEAD changed after instruction freshness check and before "
                        "Executor launch"
                    )
                validate_snapshot_sources(governance_before)
                target_before_metadata = launch_target.metadata()
                target_after_metadata = None
                executor_reference = None
                active_turn_relative = relative_evidence_path(
                    next_turn_attempt(cycle_dir / "executor"), run_root
                )
                persist(EXECUTOR_RUNNING)
                continue

            if state == EXECUTOR_RUNNING:
                if instruction is None or not isinstance(target_before_metadata, dict):
                    raise InvariantViolation("Executor checkpoint context is incomplete")
                cycle = cycle_for(cycle_number, instruction)
                target_before = target_state_from_metadata(target_before_metadata)
                turn_dir = active_turn_path(cycle_dir / "executor")
                recovered = completed_turn_from_dir(turn_dir, run_root)
                current_target = capture_target_state(
                    target_initial.repo,
                    target_initial.branch,
                    require_clean=False,
                    enforce_branch=False,
                )
                if recovered is None:
                    if current_target.branch != target_before.branch or not current_target.clean:
                        raise InvariantViolation(
                            "Executor running-state recovery found an unexpected branch or dirty tree"
                        )
                    if current_target.head != target_before.head:
                        active_turn_relative = None
                        target_after_metadata = current_target.metadata()
                        return reach_logical_outcome(
                            HUMAN_GATE,
                            manifest_status="STOPPED_FOR_HUMAN_REVIEW",
                            reason="executor_outcome_ambiguous_after_restart",
                            exit_code=0,
                            error_code="EXECUTOR_OUTCOME_AMBIGUOUS_AFTER_RESTART",
                        )
                    if turn_dir.exists():
                        turn_dir = next_turn_attempt(cycle_dir / "executor")
                        active_turn_relative = relative_evidence_path(turn_dir, run_root)
                        persist(EXECUTOR_RUNNING)
                    governance_before = capture_governance(governance_paths)
                    if reviewer_state.known_hashes != governance_before.hashes():
                        raise InvariantViolation(
                            "governance does not match the checkpointed Executor instruction"
                        )
                    executor_prefix = executor_prompt(
                        target_before.repo, target_before.branch, governance_before
                    )
                    executor_full_prompt, executor_peer_offset = make_peer_prompt(
                        executor_prefix, instruction.final_message
                    )
                    emit_progress(
                        f"run={run_id} cycle={cycle_number} role=executor "
                        f"state=running target_head={target_before.head}"
                    )
                    recovered = run_codex_turn(
                        run_root=run_root,
                        turn_dir=turn_dir,
                        codex_bin=args.codex_bin,
                        codex_home=args.executor_home.resolve(),
                        workspace=target_before.repo,
                        timeout_seconds=args.timeout_seconds,
                        role="executor",
                        message_type=EXECUTOR_RECEIPT,
                        prompt=executor_full_prompt,
                        session_mode=FRESH_EPHEMERAL,
                        peer_payload=instruction.final_message,
                        peer_payload_offset=executor_peer_offset,
                        peer_source=relative_evidence_path(
                            instruction.turn_dir / "final.txt", run_root
                        ),
                        progress_interval_seconds=progress_interval,
                        progress_label=(
                            f"run={run_id} cycle={cycle_number} role=executor "
                            f"state=running target_head={target_before.head} "
                            f"turn={turn_dir.name}"
                        ),
                    )
                executor = recovered
                target_after = capture_target_state(
                    target_initial.repo,
                    target_initial.branch,
                    require_clean=False,
                    enforce_branch=False,
                )
                governance_after = capture_governance(governance_paths)
                governance_changes = [
                    name
                    for name in DOCUMENT_ORDER
                    if reviewer_state.known_hashes is None
                    or reviewer_state.known_hashes.get(f"{name}_sha256")
                    != governance_after.hashes()[f"{name}_sha256"]
                ]
                executor.process["target_before"] = target_before.metadata()
                executor.process["target_after"] = target_after.metadata()
                executor.process["governance_hashes"] = governance_after.hashes()
                P4.write_json(executor.turn_dir / "process.json", executor.process)
                record_turn_summary(
                    executor,
                    fallback_before=target_before.metadata(),
                    fallback_after=target_after.metadata(),
                    fallback_hashes=governance_after.hashes(),
                )
                cycle["governance_after_executor"] = governance_after.metadata()
                cycle["governance_changes_during_executor"] = governance_changes
                if reviewer_state.known_hashes != governance_after.hashes():
                    raise InvariantViolation("protected governance changed during Executor cycle")
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
                cycle["executor"] = executor.process
                cycle["target_after"] = target_after.metadata()
                processes.append(executor.process)
                executor_reference = turn_reference(executor, run_root)
                target_after_metadata = target_after.metadata()
                active_turn_relative = None
                persist(EXECUTOR_COMMITTED)
                continue

            if state == EXECUTOR_COMMITTED:
                if executor is None or not isinstance(target_after_metadata, dict):
                    raise InvariantViolation("committed Executor checkpoint is incomplete")
                expected = target_state_from_metadata(target_after_metadata)
                observed = capture_target_state(
                    target_initial.repo, target_initial.branch, require_clean=True
                )
                if observed.head != expected.head or observed.branch != expected.branch:
                    raise InvariantViolation(
                        "target state changed after the checkpointed Executor commit"
                    )
                if reviewer_state.known_hashes != capture_governance(
                    governance_paths
                ).hashes():
                    raise InvariantViolation(
                        "governance changed after the checkpointed Executor commit"
                    )
                active_turn_relative = relative_evidence_path(
                    next_turn_attempt(cycle_dir / "reviewer-review"), run_root
                )
                persist(REVIEW_PENDING)
                continue

            if state == REVIEW_PENDING:
                if (
                    instruction is None
                    or executor is None
                    or not isinstance(target_after_metadata, dict)
                ):
                    raise InvariantViolation("Reviewer checkpoint context is incomplete")
                cycle = cycle_for(cycle_number, instruction)
                target_after = target_state_from_metadata(target_after_metadata)
                turn_dir = active_turn_path(cycle_dir / "reviewer-review")
                recovered = completed_turn_from_dir(turn_dir, run_root)
                if recovered is not None:
                    try:
                        reviewer_state = recover_reviewer_state_from_turn(recovered)
                    except InvariantViolation:
                        recovered = None
                if recovered is None:
                    if turn_dir.exists():
                        reviewer_state = ReviewerState(None, None, 0)
                        turn_dir = next_turn_attempt(cycle_dir / "reviewer-review")
                        active_turn_relative = relative_evidence_path(turn_dir, run_root)
                        persist(REVIEW_PENDING)
                    current_target = capture_target_state(
                        target_initial.repo, target_initial.branch, require_clean=True
                    )
                    if current_target.head != target_after.head:
                        raise InvariantViolation(
                            "target changed before checkpointed Reviewer review"
                        )
                    emit_progress(
                        f"run={run_id} cycle={cycle_number} role=reviewer "
                        f"state=review_pending target_head={target_after.head}"
                    )
                    recovered = invoke_reviewer(
                        run_root=run_root,
                        turn_dir=turn_dir,
                        target=target_after,
                        governance=capture_governance(governance_paths),
                        state=reviewer_state,
                        cycle_number=cycle_number,
                        role_prompt=reviewer_review_prompt(
                            target_after.repo, target_after.branch
                        ),
                        review=True,
                        peer_payload=executor.final_message,
                        peer_source=relative_evidence_path(
                            executor.turn_dir / "final.txt", run_root
                        ),
                        codex_bin=args.codex_bin,
                        reviewer_home=args.reviewer_home.resolve(),
                        timeout_seconds=args.timeout_seconds,
                        progress_interval_seconds=progress_interval,
                    )
                if not recovered.success:
                    record_turn_summary(
                        recovered,
                        fallback_before=target_after.metadata(),
                        fallback_after=target_after.metadata(),
                        fallback_hashes=capture_governance(governance_paths).hashes(),
                    )
                    raise InvariantViolation(
                        f"Reviewer review process failed: {recovered.process['failure']}"
                    )
                record_turn_summary(
                    recovered,
                    fallback_before=target_after.metadata(),
                    fallback_after=target_after.metadata(),
                    fallback_hashes=capture_governance(governance_paths).hashes(),
                )
                instruction = recovered
                processes.append(instruction.process)
                cycle["reviewer_review"] = instruction.process
                cycle["reviewer_state_after"] = reviewer_state.metadata()
                instruction_reference = turn_reference(instruction, run_root)
                verdict_correction = None
                active_turn_relative = None
                persist(REVIEW_COMPLETED)
                continue

            if state == REVIEW_CORRECTION_PENDING:
                if instruction is None or not isinstance(verdict_correction, dict):
                    raise ControlFailure(
                        ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                        "Reviewer correction pending state lacks its verdict context",
                    )
                validate_verdict_correction_record(verdict_correction, run_root)
                pending = verdict_correction.get("pending")
                if not isinstance(pending, dict):
                    raise ControlFailure(
                        ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                        "Reviewer correction pending attempt is missing",
                    )
                current_target = capture_target_state(
                    target_initial.repo, target_initial.branch, require_clean=True
                )
                current_governance = capture_governance(governance_paths)
                validate_framework_for_correction(
                    args=args,
                    framework_initial=framework_initial,
                    summary_path=summary_path,
                )
                validate_correction_evidence_guards(
                    verdict_correction, current_target, run_root
                )
                validate_review_process_authority(
                    instruction, args, reviewer_state, current_target, current_governance
                )
                validate_executor_for_correction(
                    executor=executor,
                    executor_reference=executor_reference,
                    args=args,
                    target=current_target,
                    target_after_metadata=target_after_metadata,
                    governance=current_governance,
                    run_root=run_root,
                )
                base = cycle_dir / (
                    f"reviewer-verdict-correction-{pending['attempt']:02d}"
                )
                if active_turn_relative is None:
                    active_turn_relative = relative_evidence_path(base, run_root)
                pending["turn_relative"] = active_turn_relative
                verdict_correction["attempts_started"] = pending["attempt"]
                persist(REVIEW_CORRECTION_RUNNING)
                continue

            if state == REVIEW_CORRECTION_RUNNING:
                if instruction is None or not isinstance(verdict_correction, dict):
                    raise ControlFailure(
                        ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                        "Reviewer correction running state lacks its verdict context",
                    )
                validate_verdict_correction_record(verdict_correction, run_root)
                pending = verdict_correction.get("pending")
                if not isinstance(pending, dict):
                    raise ControlFailure(
                        ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                        "Reviewer correction running attempt is missing",
                    )
                turn_dir = active_turn_path(
                    cycle_dir / f"reviewer-verdict-correction-{pending['attempt']:02d}"
                )
                if pending.get("turn_relative") != relative_evidence_path(turn_dir, run_root):
                    raise ControlFailure(
                        ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                        "Reviewer correction turn locator differs from its checkpoint plan",
                    )
                current_target = capture_target_state(
                    target_initial.repo, target_initial.branch, require_clean=True
                )
                current_governance = capture_governance(governance_paths)
                validate_framework_for_correction(
                    args=args,
                    framework_initial=framework_initial,
                    summary_path=summary_path,
                )
                validate_correction_evidence_guards(
                    verdict_correction, current_target, run_root
                )
                validate_review_process_authority(
                    instruction, args, reviewer_state, current_target, current_governance
                )
                validate_executor_for_correction(
                    executor=executor,
                    executor_reference=executor_reference,
                    args=args,
                    target=current_target,
                    target_after_metadata=target_after_metadata,
                    governance=current_governance,
                    run_root=run_root,
                )
                recovered = completed_turn_from_dir(turn_dir, run_root)
                reviewer_thread_before = reviewer_state.reviewer_thread_id
                if recovered is None:
                    if turn_dir.exists():
                        raise ControlFailure(
                            ControlErrorCode.VERDICT_CORRECTION_PROCESS_FAILED,
                            "Reviewer correction process did not leave a complete recoverable turn",
                        )
                    context = correction_control_context(
                        correction=verdict_correction,
                        executor_reference=executor_reference,
                        target=current_target,
                        governance=current_governance,
                        run_root=run_root,
                    )
                    emit_progress(
                        f"run={run_id} cycle={cycle_number} role=reviewer "
                        f"state=verdict_correction_running attempt={pending['attempt']} "
                        f"error_code={pending['error_code']} target_head={current_target.head}"
                    )
                    recovered = invoke_reviewer(
                        run_root=run_root,
                        turn_dir=turn_dir,
                        target=current_target,
                        governance=current_governance,
                        state=reviewer_state,
                        cycle_number=cycle_number,
                        role_prompt=reviewer_correction_prompt(context),
                        peer_payload=None,
                        peer_source=None,
                        codex_bin=args.codex_bin,
                        reviewer_home=args.reviewer_home.resolve(),
                        timeout_seconds=args.timeout_seconds,
                        progress_interval_seconds=progress_interval,
                        review=True,
                    )
                else:
                    reviewer_state = recover_reviewer_state_from_turn(recovered)
                recovered.process["verdict_correction"] = {
                    "attempt": pending["attempt"],
                    "error_code": pending["error_code"],
                    "maximum_attempts": verdict_correction["maximum_attempts"],
                    "original_verdict_sha256": verdict_correction[
                        "original_verdict_reference"
                    ]["final_sha256"],
                    "source_verdict_sha256": verdict_correction[
                        "source_verdict_reference"
                    ]["final_sha256"],
                }
                P4.write_json(recovered.turn_dir / "process.json", recovered.process)
                record_turn_summary(
                    recovered,
                    fallback_before=current_target.metadata(),
                    fallback_after=current_target.metadata(),
                    fallback_hashes=current_governance.hashes(),
                )
                if not recovered.success:
                    raise ControlFailure(
                        ControlErrorCode.VERDICT_CORRECTION_PROCESS_FAILED,
                        "Reviewer correction process/schema/relationship validation failed",
                    )
                if (
                    recovered.process.get("session_mode") != RESUME
                    or reviewer_thread_before is None
                    or reviewer_state.reviewer_thread_id != reviewer_thread_before
                ):
                    raise ControlFailure(
                        ControlErrorCode.REVIEW_RESUME_RELATIONSHIP_INVALID,
                        "Reviewer correction did not resume the original Reviewer thread",
                    )
                correction_reference = turn_reference(recovered, run_root)
                verdict_correction["attempts"].append({
                    "attempt": pending["attempt"],
                    "turn_reference": correction_reference,
                })
                verdict_correction["attempts_completed"] = len(
                    verdict_correction["attempts"]
                )
                verdict_correction["source_verdict_reference"] = correction_reference
                verdict_correction["pending"] = None
                validate_verdict_correction_record(verdict_correction, run_root)
                cycle = cycle_for(cycle_number, instruction)
                cycle["reviewer_corrections"].append(recovered.process)
                cycle["reviewer_state_after"] = reviewer_state.metadata()
                instruction = recovered
                processes.append(recovered.process)
                instruction_reference = correction_reference
                active_turn_relative = None
                persist(REVIEW_COMPLETED)
                continue

            if state == REVIEW_COMPLETED:
                if instruction is None:
                    raise InvariantViolation("Reviewer verdict checkpoint reference is missing")
                current_target = capture_target_state(
                    target_initial.repo, target_initial.branch, require_clean=True
                )
                current_governance = capture_governance(governance_paths)
                if isinstance(verdict_correction, dict):
                    validate_correction_evidence_guards(
                        verdict_correction, current_target, run_root
                    )
                try:
                    value = validate_review_authority(
                        instruction, args, reviewer_state, current_target, current_governance
                    )
                    if value["verdict"] == "ACCEPT":
                        validate_accept(
                            args=args,
                            turn=instruction,
                            state=reviewer_state,
                            target=current_target,
                            governance=current_governance,
                            run_root=run_root,
                        )
                except ControlFailure as exc:
                    if not exc.correctable or exc.code not in CORRECTABLE_VERDICT_CODES:
                        raise
                    validate_executor_for_correction(
                        executor=executor,
                        executor_reference=executor_reference,
                        args=args,
                        target=current_target,
                        target_after_metadata=target_after_metadata,
                        governance=current_governance,
                        run_root=run_root,
                    )
                    validate_framework_for_correction(
                        args=args,
                        framework_initial=framework_initial,
                        summary_path=summary_path,
                    )
                    validate_review_process_authority(
                        instruction,
                        args,
                        reviewer_state,
                        current_target,
                        current_governance,
                    )
                    if isinstance(verdict_correction, dict):
                        validate_verdict_correction_record(verdict_correction, run_root)
                        if verdict_correction["attempts"]:
                            verdict_correction["attempts"][-1]["validation_error"] = {
                                "code": exc.code.value,
                                "reason": exc.public_reason,
                            }
                        if (
                            verdict_correction["attempts_completed"]
                            >= MAX_REVIEW_CORRECTION_ATTEMPTS
                        ):
                            raise ControlFailure(
                                ControlErrorCode.VERDICT_CORRECTION_EXHAUSTED,
                                "Reviewer verdict correction exhausted after 2 completed attempts",
                            ) from exc
                    if not isinstance(instruction_reference, dict):
                        raise ControlFailure(
                            ControlErrorCode.VERDICT_CORRECTION_CHECKPOINT_INVALID,
                            "Reviewer verdict checkpoint reference is incomplete",
                        )
                    verdict_correction = plan_verdict_correction(
                        current_reference=instruction_reference,
                        error=exc,
                        evidence_guard=capture_correction_evidence_guard(
                            validate_turn_payload(
                                instruction.final_message, REVIEWER_VERDICT
                            ),
                            current_target,
                            run_root,
                        ),
                        existing=verdict_correction,
                        run_root=run_root,
                    )
                    emit_progress(
                        f"run={run_id} cycle={cycle_number} verdict_correction=pending "
                        f"attempt={verdict_correction['pending']['attempt']} "
                        f"error_code={exc.code.value}"
                    )
                    persist(REVIEW_CORRECTION_PENDING)
                    record_active_progress(
                        "record", "correction", activity_kind="correction_planned"
                    )
                    continue
                emit_progress(f"run={run_id} cycle={cycle_number} verdict={value['verdict']}")
                if isinstance(verdict_correction, dict):
                    verdict_correction["resolution"] = {
                        "attempts_completed": verdict_correction["attempts_completed"],
                        "verdict": value["verdict"],
                        "verdict_reference": copy.deepcopy(instruction_reference),
                    }
                    cycle_for(cycle_number, instruction)["verdict_correction"] = copy.deepcopy(
                        verdict_correction
                    )
                if value["verdict"] == "HUMAN_GATE":
                    emit_progress(
                        "waiting_for_human: reason recorded in the tracked evidence summary"
                    )
                    return reach_logical_outcome(
                        HUMAN_GATE,
                        manifest_status="STOPPED_FOR_HUMAN_REVIEW",
                        reason="reviewer_human_gate",
                        exit_code=0,
                        error_code="REVIEWER_HUMAN_GATE",
                    )
                if value["verdict"] == "ACCEPT":
                    transition_plan, _ = build_runtime_transition(
                        preimage=current_governance.documents[WORKLOAD_RUNTIME].content,
                        value=value, verdict_path=instruction.turn_dir / "final.txt",
                        verdict_sha256=P4.sha256_bytes(instruction.final_message),
                        runtime_path=args.workload_runtime.resolve(), timestamp=P4.utc_now(),
                    )
                    persist(RUNTIME_TRANSITION_PENDING)
                    continue
                # Only a schema-valid REJECT can reach another bounded repair cycle.
                if not isinstance(target_before_metadata, dict) or not isinstance(
                    target_after_metadata, dict
                ):
                    raise InvariantViolation("review completion target state is incomplete")
                before = target_state_from_metadata(target_before_metadata)
                after = target_state_from_metadata(target_after_metadata)
                if after.head == before.head:
                    return reach_logical_outcome(
                        HUMAN_GATE,
                        manifest_status="STOPPED_FOR_HUMAN_REVIEW",
                        reason="target_head_unchanged",
                        exit_code=0,
                        error_code="TARGET_HEAD_UNCHANGED",
                    )
                if cycle_number == args.max_cycles:
                    return reach_logical_outcome(
                        HUMAN_GATE,
                        manifest_status="STOPPED_FOR_HUMAN_REVIEW",
                        reason="max_cycles_reached",
                        exit_code=0,
                        error_code="MAX_CYCLES_REACHED",
                    )
                cycle_number += 1
                verdict_correction = None
                executor = None
                executor_reference = None
                target_before_metadata = None
                target_after_metadata = None
                active_turn_relative = None
                persist(INSTRUCTION_READY)
                continue

            if state in {RUNTIME_TRANSITION_PENDING, RUNTIME_TRANSITION_COMMITTED}:
                if not isinstance(transition_plan, dict) or instruction is None:
                    raise InvariantViolation("Runtime transition checkpoint is incomplete")
                was_committed = state == RUNTIME_TRANSITION_COMMITTED
                reconcile_runtime_transition(
                    plan=transition_plan, args=args, turn=instruction, state=reviewer_state,
                    run_root=run_root, governance_paths=governance_paths,
                    committed=was_committed,
                )
                runtime_transition_applied = True
                return reach_logical_outcome(
                    RUNTIME_TRANSITION_COMMITTED,
                    manifest_status=RUNTIME_TRANSITION_COMMITTED,
                    reason="one_reviewer_accept_transition_completed",
                    exit_code=0,
                    error_code="RUNTIME_TRANSITION_COMMITTED",
                )

            raise InvariantViolation(f"unsupported checkpoint state: {state}")
    except (OSError, RuntimeError, ValueError) as exc:
        reason = str(exc)
        error_code = control_error_code(exc)
        public_reason = bounded_public_reason(reason, error_code)
        emit_progress(
            f"run={run_id} stopped error_code={error_code} reason={public_reason}"
        )
        record_active_progress("record", "error", activity_kind="error")
        active_turn_relative = None
        transition_interrupted = state in {RUNTIME_TRANSITION_PENDING, RUNTIME_TRANSITION_COMMITTED}
        # An I/O failure can happen after os.replace (including checkpoint fsync).
        # Preserve the pending plan so --resume can compare exact bytes. Unknown
        # state/evidence is a Human Gate, never a guessed repair.
        failure_state = (
            state if transition_interrupted and isinstance(exc, OSError)
            else HUMAN_GATE if transition_interrupted else FAILED_CLOSED
        )
        if evidence_finalization_enabled:
            if state in {
                EVIDENCE_FINALIZATION_PENDING,
                FRAMEWORK_EVIDENCE_COMMITTED,
                FRAMEWORK_EVIDENCE_PUSHED,
            }:
                evidence_finalization_error = reason
                emit_progress(
                    f"run={run_id} evidence_finalization=failed state={state}"
                )
                try:
                    status, original_reason = logical_manifest()
                    persist(
                        state,
                        manifest_status=status,
                        manifest_reason=original_reason,
                    )
                except (OSError, RuntimeError, ValueError) as checkpoint_exc:
                    emit_progress(
                        f"run={run_id} state={state} "
                        f"checkpoint_error_code={control_error_code(checkpoint_exc)}"
                    )
                return finish_return(1)
            if transition_interrupted and isinstance(exc, OSError):
                logical_outcome = {
                    "error_code": error_code,
                    "exit_code": 1,
                    "internal_diagnostic": {
                        "exception_type": type(exc).__name__,
                        "reason": reason,
                    },
                    "manifest_status": "STOPPED_FOR_HUMAN_REVIEW",
                    "reason": public_reason,
                    "state": "UNDETERMINED",
                }
                try:
                    persist(
                        state,
                        manifest_status="STOPPED_FOR_HUMAN_REVIEW",
                        manifest_reason=public_reason,
                    )
                except (OSError, RuntimeError, ValueError) as checkpoint_exc:
                    emit_progress(
                        f"run={run_id} state={state} "
                        f"checkpoint_error_code={control_error_code(checkpoint_exc)}"
                    )
                return finish_return(1)
            try:
                return reach_logical_outcome(
                    failure_state,
                    manifest_status=(
                        "STOPPED_FOR_HUMAN_REVIEW"
                        if transition_interrupted else "FAILED_CLOSED"
                    ),
                    reason=reason,
                    exit_code=1,
                    error_code=error_code,
                    diagnostic=exc,
                )
            except (OSError, RuntimeError, ValueError) as finalization_exc:
                evidence_finalization_error = str(finalization_exc)
                emit_progress(
                    f"run={run_id} evidence_finalization=failed "
                    f"state={state}"
                )
                try:
                    status, original_reason = logical_manifest()
                    persist(
                        state,
                        manifest_status=status,
                        manifest_reason=original_reason,
                    )
                except (OSError, RuntimeError, ValueError) as checkpoint_exc:
                    emit_progress(
                        f"run={run_id} state={state} "
                        f"checkpoint_error_code={control_error_code(checkpoint_exc)}"
                    )
                return finish_return(1)
        try:
            return reach_logical_outcome(
                failure_state,
                manifest_status=(
                    "STOPPED_FOR_HUMAN_REVIEW"
                    if transition_interrupted else "FAILED_CLOSED"
                ),
                reason=reason,
                exit_code=1,
                error_code=error_code,
                diagnostic=exc,
            )
        except (OSError, RuntimeError, ValueError) as checkpoint_exc:
            emit_progress(
                f"run={run_id} state=FAILED_CLOSED "
                f"checkpoint_error_code={control_error_code(checkpoint_exc)}"
            )
        return finish_return(1)


def preflight_report(
    target: TargetState, governance: GovernanceSnapshot, args: argparse.Namespace
) -> Dict[str, Any]:
    report = {
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
        "operator_config_identity": copy.deepcopy(
            getattr(args, "operator_config_identity", None)
        ),
        "runtime_transition_cli_enabled": bool(getattr(args, "enable_runtime_transition", False)),
        "preflight": "passed",
        "reviewer_home": str(args.reviewer_home.resolve()),
        "target": {
            "initial_target_head": target.head,
            "target_branch": target.branch,
            "target_repo": str(target.repo),
            "working_tree_clean": target.clean,
        },
    }
    if p63_enabled(args):
        report["evidence_finalization"] = {
            **framework_settings(args),
            "summary_path": str(summary_path_for_args(args, args.run_id)),
        }
    return report


def normalize_cli_args(args: argparse.Namespace) -> argparse.Namespace:
    args.framework_repo = args.framework_repo.resolve()
    active_root = args.framework_repo / "1PCloop"
    if args.framework_static is None:
        args.framework_static = active_root / "docs/miniloop_static.md"
    if args.framework_runtime is None:
        args.framework_runtime = active_root / "docs/miniloop_runtime.md"
    if args.runs_root is None:
        args.runs_root = active_root / ".local/runs"
    if args.state_root is None:
        args.state_root = active_root / ".local/state"
    if args.summary_root is None:
        args.summary_root = active_root / "evidence-summaries"
    if args.framework_push_ref is None:
        args.framework_push_ref = f"refs/heads/{args.framework_branch}"
    return args


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-repo", type=Path, required=True)
    parser.add_argument("--target-branch", required=True)
    parser.add_argument("--workload-static", type=Path, required=True)
    parser.add_argument("--workload-runtime", type=Path, required=True)
    parser.add_argument("--enable-runtime-transition", action="store_true",
                        help="allow one Reviewer ACCEPT transition if workload Runtime also opts in")
    parser.add_argument("--max-cycles", type=int, default=8)
    parser.add_argument("--framework-repo", type=Path, default=FRAMEWORK_ROOT)
    parser.add_argument("--framework-branch", default="main")
    parser.add_argument("--framework-remote", default="origin")
    parser.add_argument("--framework-push-ref")
    parser.add_argument("--framework-static", type=Path)
    parser.add_argument("--framework-runtime", type=Path)
    parser.add_argument("--reviewer-home", type=Path, default=DEFAULT_REVIEWER_HOME)
    parser.add_argument("--executor-home", type=Path, default=DEFAULT_EXECUTOR_HOME)
    parser.add_argument("--codex-bin", default=shutil.which("codex") or "codex")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--run-id", default=P4.default_run_id())
    parser.add_argument("--runs-root", type=Path)
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--summary-root", type=Path)
    parser.add_argument(
        "--workload-id",
        help="stable checkpoint key; defaults to the workload Static parent directory",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="resume pending work, or verify a committed Runtime transition without replay",
    )
    parser.add_argument(
        "--progress-interval-seconds",
        type=float,
        default=15.0,
        help="terminal heartbeat interval while a Codex turn is running",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="validate inputs without creating evidence or invoking Codex",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    global _ACTIVE_PROGRESS
    args = normalize_cli_args(parse_args(argv))
    if args.max_cycles <= 0:
        raise SystemExit("--max-cycles must be positive")
    if args.timeout_seconds <= 0:
        raise SystemExit("--timeout-seconds must be positive")
    if args.progress_interval_seconds <= 0:
        raise SystemExit("--progress-interval-seconds must be positive")
    try:
        P4.validate_run_id(args.run_id)
        target, governance = validate_preflight(args)
    except (OSError, RuntimeError, ValueError) as exc:
        _ACTIVE_PROGRESS = None
        print(
            "preflight failed; inspect checkpoint and local evidence",
            file=sys.stderr,
        )
        emit_final_result(failure_result_for_main(args, exc, exit_code=2))
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
        exit_code, _run_root = orchestrate(
            args=args,
            target_initial=target,
            governance_initial=governance,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        _ACTIVE_PROGRESS = None
        print(
            "unable to start mutation loop; inspect checkpoint and local evidence",
            file=sys.stderr,
        )
        emit_final_result(failure_result_for_main(args, exc))
        return 1
    # The bounded FINAL_RESULT emitted by orchestrate already includes run_root.
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
