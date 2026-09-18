#!/usr/bin/env python3
"""Pure mutation control, message, and public-result contracts.

This module defines validation and projection primitives only. Importing it does
not load the mutation runner, inspect Git, create files, or start subprocesses.
"""

from __future__ import annotations

import json
import unicodedata
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple


SCRIPT_PATH = Path(__file__).resolve()
ACTIVE_ROOT = SCRIPT_PATH.parents[1]
SCHEMAS_ROOT = ACTIVE_ROOT / "schemas"
REVIEWER_INSTRUCTION = "reviewer_instruction"
EXECUTOR_RECEIPT = "executor_receipt"
REVIEWER_VERDICT = "reviewer_verdict"
TURN_SCHEMAS = (REVIEWER_INSTRUCTION, EXECUTOR_RECEIPT, REVIEWER_VERDICT)

MAX_PUBLIC_REASON_CHARS = 512
PUBLIC_REASON_TRUNCATION_MARKER = "...[truncated]"
UNCLASSIFIED_PUBLIC_REASON = (
    "mutation loop stopped; inspect checkpoint and local evidence"
)
FINAL_RESULT_FIELDS = (
    "run_id",
    "logical_outcome",
    "exit_code",
    "runtime_transition",
    "evidence_publication",
    "reason",
    "error_code",
    "run_root",
)

CANONICAL_CODEX_HOME = Path.home() / ".codex-mix"
ROLE_RUNTIME_ROOT = CANONICAL_CODEX_HOME / ".mix" / "runtimes"
DEFAULT_REVIEWER_HOME = ROLE_RUNTIME_ROOT / "1pcloop-reviewer"
DEFAULT_EXECUTOR_HOME = ROLE_RUNTIME_ROOT / "1pcloop-executor"
RETIRED_CODEX_HOMES = (
    Path.home() / ".codex-A",
    Path.home() / ".codex-B",
)


class InvariantViolation(RuntimeError):
    """A mechanical invariant failed and the loop must not continue."""


def _same_or_descendant(path: Path, boundary: Path) -> bool:
    return path == boundary or boundary in path.parents


def validate_role_runtime_homes(
    reviewer_home: Path,
    executor_home: Path,
    *,
    runtime_root: Optional[Path] = None,
) -> Tuple[Path, Path]:
    """Resolve role homes and reject retired account-identity directories."""
    reviewer = reviewer_home.resolve()
    executor = executor_home.resolve()
    for role, selected in (("Reviewer", reviewer), ("Executor", executor)):
        for retired in RETIRED_CODEX_HOMES:
            retired_resolved = retired.resolve()
            if _same_or_descendant(selected, retired_resolved):
                raise InvariantViolation(
                    f"{role} CODEX_HOME resolves inside a retired account home"
                )
    selected_root = (runtime_root or ROLE_RUNTIME_ROOT).resolve()
    for role, selected in (("Reviewer", reviewer), ("Executor", executor)):
        if selected == selected_root or selected_root not in selected.parents:
            raise InvariantViolation(
                f"{role} CODEX_HOME must resolve inside the dedicated runtime root"
            )
    if _same_or_descendant(reviewer, executor) or _same_or_descendant(
        executor, reviewer
    ):
        raise InvariantViolation(
            "Reviewer and Executor profiles must be distinct and non-nested"
        )
    return reviewer, executor


class ControlErrorCode(str, Enum):
    """Stable public codes for F1 control decisions."""

    VERDICT_REJECT_CONTRACT = "VERDICT_REJECT_CONTRACT"
    VERDICT_HUMAN_GATE_CONTRACT = "VERDICT_HUMAN_GATE_CONTRACT"
    VERDICT_ACCEPT_CONTRACT = "VERDICT_ACCEPT_CONTRACT"
    VERDICT_REVIEWED_TARGET_MISMATCH = "VERDICT_REVIEWED_TARGET_MISMATCH"
    VERDICT_GOVERNANCE_HASH_MISMATCH = "VERDICT_GOVERNANCE_HASH_MISMATCH"
    VERDICT_RUNTIME_HASH_MISMATCH = "VERDICT_RUNTIME_HASH_MISMATCH"
    VERDICT_ACTIVE_STEP_MISMATCH = "VERDICT_ACTIVE_STEP_MISMATCH"
    EVIDENCE_COMMIT_LOCATOR_INVALID = "EVIDENCE_COMMIT_LOCATOR_INVALID"
    EVIDENCE_COMMIT_UNRESOLVABLE = "EVIDENCE_COMMIT_UNRESOLVABLE"
    EVIDENCE_COMMIT_NOT_COMMIT = "EVIDENCE_COMMIT_NOT_COMMIT"
    EVIDENCE_COMMIT_UNREACHABLE = "EVIDENCE_COMMIT_UNREACHABLE"
    EVIDENCE_LOCATOR_NOT_ABSOLUTE = "EVIDENCE_LOCATOR_NOT_ABSOLUTE"
    EVIDENCE_LOCATOR_OUTSIDE_BOUNDARY = "EVIDENCE_LOCATOR_OUTSIDE_BOUNDARY"
    EVIDENCE_LOCATOR_MISSING = "EVIDENCE_LOCATOR_MISSING"
    EVIDENCE_HASH_MISMATCH = "EVIDENCE_HASH_MISMATCH"
    EVIDENCE_COMMIT_REQUIRED = "EVIDENCE_COMMIT_REQUIRED"
    REVIEW_PROCESS_AUTHORITY_INVALID = "REVIEW_PROCESS_AUTHORITY_INVALID"
    REVIEW_THREAD_MISMATCH = "REVIEW_THREAD_MISMATCH"
    REVIEW_CONTEXT_STALE = "REVIEW_CONTEXT_STALE"
    REVIEW_RESUME_RELATIONSHIP_INVALID = "REVIEW_RESUME_RELATIONSHIP_INVALID"
    REVIEW_BOOTSTRAP_INVALID = "REVIEW_BOOTSTRAP_INVALID"
    REVIEW_TARGET_STATE_INVALID = "REVIEW_TARGET_STATE_INVALID"
    RUNTIME_CAPABILITY_DISABLED = "RUNTIME_CAPABILITY_DISABLED"
    RUNTIME_DESTINATION_MISMATCH = "RUNTIME_DESTINATION_MISMATCH"
    RUNTIME_MACHINE_UNAUTHORIZED = "RUNTIME_MACHINE_UNAUTHORIZED"
    VERDICT_CORRECTION_CHECKPOINT_INVALID = "VERDICT_CORRECTION_CHECKPOINT_INVALID"
    VERDICT_CORRECTION_PROCESS_FAILED = "VERDICT_CORRECTION_PROCESS_FAILED"
    VERDICT_CORRECTION_EXHAUSTED = "VERDICT_CORRECTION_EXHAUSTED"
    UNCLASSIFIED_CONTROL_FAILURE = "UNCLASSIFIED_CONTROL_FAILURE"


CORRECTABLE_VERDICT_CODES = frozenset({
    ControlErrorCode.VERDICT_REJECT_CONTRACT,
    ControlErrorCode.VERDICT_HUMAN_GATE_CONTRACT,
    ControlErrorCode.VERDICT_ACCEPT_CONTRACT,
    ControlErrorCode.VERDICT_REVIEWED_TARGET_MISMATCH,
    ControlErrorCode.VERDICT_GOVERNANCE_HASH_MISMATCH,
    ControlErrorCode.VERDICT_RUNTIME_HASH_MISMATCH,
    ControlErrorCode.VERDICT_ACTIVE_STEP_MISMATCH,
    ControlErrorCode.EVIDENCE_COMMIT_LOCATOR_INVALID,
    ControlErrorCode.EVIDENCE_COMMIT_UNRESOLVABLE,
    ControlErrorCode.EVIDENCE_COMMIT_NOT_COMMIT,
    ControlErrorCode.EVIDENCE_COMMIT_UNREACHABLE,
    ControlErrorCode.EVIDENCE_LOCATOR_NOT_ABSOLUTE,
    ControlErrorCode.EVIDENCE_LOCATOR_OUTSIDE_BOUNDARY,
    ControlErrorCode.EVIDENCE_LOCATOR_MISSING,
    ControlErrorCode.EVIDENCE_HASH_MISMATCH,
    ControlErrorCode.EVIDENCE_COMMIT_REQUIRED,
})


class ControlFailure(InvariantViolation):
    """A typed control-plane failure with a bounded public reason."""

    def __init__(
        self, code: ControlErrorCode, reason: str, *, correctable: bool = False
    ) -> None:
        super().__init__(reason)
        self.code = code
        self.public_reason = reason
        self.correctable = correctable


def correctable_failure(code: ControlErrorCode, reason: str) -> ControlFailure:
    if code not in CORRECTABLE_VERDICT_CODES:
        raise ValueError("control error code is not correction-eligible")
    return ControlFailure(code, reason, correctable=True)


def control_error_code(exc: BaseException) -> str:
    if isinstance(exc, ControlFailure):
        return exc.code.value
    return ControlErrorCode.UNCLASSIFIED_CONTROL_FAILURE.value


def escape_public_text(value: str) -> str:
    """Make a public string physically single-line and terminal inert."""
    escaped: List[str] = []
    for character in value:
        category = unicodedata.category(character)
        if category in {"Cc", "Cf", "Zl", "Zp"}:
            codepoint = ord(character)
            escaped.append(
                f"\\u{codepoint:04x}"
                if codepoint <= 0xFFFF
                else f"\\U{codepoint:08x}"
            )
        else:
            escaped.append(character)
    return "".join(escaped)


def bounded_public_reason(reason: Any, error_code: Any) -> Optional[str]:
    if reason is None:
        return None
    if error_code == ControlErrorCode.UNCLASSIFIED_CONTROL_FAILURE.value:
        rendered = UNCLASSIFIED_PUBLIC_REASON
    else:
        rendered = escape_public_text(str(reason))
    if len(rendered) > MAX_PUBLIC_REASON_CHARS:
        keep = MAX_PUBLIC_REASON_CHARS - len(PUBLIC_REASON_TRUNCATION_MARKER)
        rendered = rendered[:keep] + PUBLIC_REASON_TRUNCATION_MARKER
    return rendered


def public_final_result(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Central checkpoint/manifest/terminal boundary for F1 public fields."""
    error_code = result.get("error_code")
    public: Dict[str, Any] = {}
    for name in FINAL_RESULT_FIELDS:
        value = result.get(name)
        if name == "exit_code":
            public[name] = value if type(value) is int else None
        elif name == "reason":
            public[name] = bounded_public_reason(value, error_code)
        elif value is None:
            public[name] = None
        else:
            public[name] = escape_public_text(str(value))
    return public


def terminal_scalar(value: Any) -> str:
    """Encode one public value as a deterministic single-line JSON scalar."""
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def strict_json(data: bytes) -> Any:
    """Reject duplicate keys and non-JSON numbers, without touching peer bytes."""
    def pairs(items: Any) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(value: str) -> None:
        raise ValueError(f"invalid JSON constant: {value}")

    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=invalid_constant,
        )
    except (ValueError, UnicodeError) as exc:
        raise InvariantViolation(f"invalid JSON: {exc}") from exc


def validate_json_schema(value: Any, schema: Mapping[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise InvariantViolation(
            "P6 requires jsonschema; install 1PCloop/requirements.txt"
        ) from exc
    Draft202012Validator.check_schema(schema)
    error = next(Draft202012Validator(schema).iter_errors(value), None)
    if error is not None:
        # Do not echo a potentially huge or sensitive peer payload in the terminal.
        raise InvariantViolation(
            f"schema validation failed at {list(error.absolute_path)}: {error.validator}"
        )


def schema_path(message_type: str) -> Path:
    if message_type not in TURN_SCHEMAS:
        raise InvariantViolation("unknown turn schema")
    return SCHEMAS_ROOT / f"{message_type}.schema.json"


def validate_turn_payload(payload: bytes, message_type: str) -> Dict[str, Any]:
    """Validate only the runtime-enforced/local JSON Schema contract.

    Reviewer verdict cross-field and authoritative-state relationships are checked
    later, after process/profile/thread/read-only authority is established. This
    separation is what makes a narrow class of schema-valid control declarations
    eligible for F1 correction without treating schema failure as correctable.
    """
    schema = strict_json(schema_path(message_type).read_bytes())
    value = strict_json(payload)
    validate_json_schema(value, schema)
    return value


def validate_verdict_relationships(value: Mapping[str, Any]) -> None:
    """Enforce schema-subset cross-field rules with explicit correction codes."""
    verdict = value["verdict"]
    if verdict == "REJECT":
        if value["next_instruction"] is None or value["runtime_transition"] is not None:
            raise correctable_failure(
                ControlErrorCode.VERDICT_REJECT_CONTRACT,
                "REJECT requires one bounded next_instruction and no transition",
            )
    elif verdict == "HUMAN_GATE":
        if value["next_instruction"] is not None or value["runtime_transition"] is not None:
            raise correctable_failure(
                ControlErrorCode.VERDICT_HUMAN_GATE_CONTRACT,
                "HUMAN_GATE must not request repair or transition",
            )
    elif (
        value["next_instruction"] is not None
        or value["runtime_transition"] is None
        or not value["evidence"]
    ):
        raise correctable_failure(
            ControlErrorCode.VERDICT_ACCEPT_CONTRACT,
            "ACCEPT requires evidence and transition, and forbids repair instruction",
        )
