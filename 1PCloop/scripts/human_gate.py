#!/usr/bin/env python3
"""Deterministic, read-only Human Gate projection.

The caller supplies already observed structured state and public artifact
locators. This module performs no I/O and never interprets natural language as
a control decision.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence

from mutation_contracts import bounded_public_reason, escape_public_text


SCHEMA_VERSION = 1
GATE_STATUSES = frozenset({
    "ACTIVE",
    "NOT_APPLICABLE",
    "UNAVAILABLE",
    "INVALID",
})
RECOVERY_MODES = frozenset({
    "FINALIZATION_ONLY",
    "HUMAN_REMEDIATION_REQUIRED",
    "NEW_RUN_AFTER_REVIEW",
    "NO_ACTION",
})
ALLOWED_ACTIONS = frozenset({
    "INSPECT_EVIDENCE",
    "FINALIZE_EVIDENCE",
    "REMEDIATE_EXTERNAL_STATE",
    "START_NEW_RUN_AFTER_HUMAN_REVIEW",
    "NO_AUTOMATIC_REPAIR",
})
PUBLIC_ARTIFACT_KEYS = (
    "config",
    "checkpoint",
    "run_root",
    "manifest",
    "control_events",
    "live_status",
    "tracked_summary",
)
FINALIZATION_STATES = frozenset({
    "EVIDENCE_FINALIZATION_PENDING",
    "FRAMEWORK_EVIDENCE_COMMITTED",
})
INCOMPLETE_PUBLICATION = frozenset({"PENDING", "FAILED", "COMMITTED"})
TRANSITION_INTERRUPTED_STATES = frozenset({
    "RUNTIME_TRANSITION_PENDING",
    "RUNTIME_TRANSITION_COMMITTED",
})
KNOWN_GATE_CODES = frozenset({
    "REVIEWER_HUMAN_GATE",
    "TARGET_HEAD_UNCHANGED",
    "MAX_CYCLES_REACHED",
    "EXECUTOR_OUTCOME_AMBIGUOUS_AFTER_RESTART",
    "RUNTIME_TRANSITION_INTERRUPTED",
    "VERDICT_CORRECTION_EXHAUSTED",
})
REASON_TEXT = {
    "NO_CHECKPOINT": "no checkpoint exists for this configured workload",
    "NOT_A_HUMAN_GATE": "checkpoint does not represent a Human Gate",
    "REVIEWER_HUMAN_GATE": "Reviewer explicitly requested Human review",
    "TARGET_HEAD_UNCHANGED": "target HEAD did not change after the Executor turn",
    "MAX_CYCLES_REACHED": "the configured mutation cycle limit was reached",
    "EXECUTOR_OUTCOME_AMBIGUOUS_AFTER_RESTART": (
        "Executor outcome is ambiguous after restart"
    ),
    "RUNTIME_TRANSITION_INTERRUPTED": (
        "Runtime transition state requires Human inspection"
    ),
    "VERDICT_CORRECTION_EXHAUSTED": (
        "Reviewer verdict correction attempts were exhausted"
    ),
    "HUMAN_GATE_REASON_UNAVAILABLE": (
        "Human Gate reason is unavailable; inspect authoritative evidence"
    ),
    "IDENTITY_CONFLICT": (
        "checkpoint, config, or evidence identity validation did not pass"
    ),
    "REQUIRED_EVIDENCE_UNAVAILABLE": (
        "required local evidence is unavailable"
    ),
}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _fixed_string(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and value else None


def _public_artifacts(locators: Optional[Mapping[str, Any]]) -> Dict[str, str]:
    source = _mapping(locators)
    result: Dict[str, str] = {}
    for name in PUBLIC_ARTIFACT_KEYS:
        value = source.get(name)
        if isinstance(value, str) and value:
            result[name] = escape_public_text(value)[:2048]
    return result


def _actions(*values: str) -> Sequence[str]:
    if any(value not in ALLOWED_ACTIONS for value in values):
        raise ValueError("unknown Human Gate action")
    return list(values)


def _reason_code(
    checkpoint_state: Optional[str],
    logical_outcome: Mapping[str, Any],
    final_result: Mapping[str, Any],
    *,
    gate_active: bool,
) -> str:
    logical_code = _fixed_string(logical_outcome.get("error_code"))
    final_code = _fixed_string(final_result.get("error_code"))
    candidate = logical_code or final_code
    if candidate in KNOWN_GATE_CODES:
        return candidate
    if checkpoint_state in TRANSITION_INTERRUPTED_STATES:
        return "RUNTIME_TRANSITION_INTERRUPTED"
    if gate_active:
        return "HUMAN_GATE_REASON_UNAVAILABLE"
    return "NOT_A_HUMAN_GATE"


def project_human_gate(
    checkpoint: Optional[Mapping[str, Any]],
    *,
    identity_status: str,
    evidence_availability: str,
    artifact_locators: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Project structured control state without reading or mutating artifacts.

    ``identity_status`` is ``VALID`` or ``INVALID``. Evidence availability is
    ``AVAILABLE``, ``UNAVAILABLE``, or ``INVALID``. Any unknown value is treated
    as invalid instead of enabling an action.
    """
    artifacts = _public_artifacts(artifact_locators)
    if identity_status not in {"VALID", "INVALID"}:
        identity_status = "INVALID"
    if evidence_availability not in {"AVAILABLE", "UNAVAILABLE", "INVALID"}:
        evidence_availability = "INVALID"

    checkpoint_value = _mapping(checkpoint)
    checkpoint_state = _fixed_string(checkpoint_value.get("state"))
    logical = _mapping(checkpoint_value.get("logical_outcome"))
    final = _mapping(checkpoint_value.get("final_result"))
    logical_state = _fixed_string(logical.get("state")) or _fixed_string(
        final.get("logical_outcome")
    )
    runtime_transition = _fixed_string(final.get("runtime_transition"))
    if runtime_transition is None:
        runtime_transition = (
            "APPLIED" if checkpoint_value.get("runtime_transition_applied") is True
            else "UNDETERMINED"
        )
    publication = _fixed_string(final.get("evidence_publication"))
    if publication is None:
        if checkpoint_state == "FRAMEWORK_EVIDENCE_PUSHED":
            publication = "PUSHED"
        elif checkpoint_state == "FRAMEWORK_EVIDENCE_COMMITTED":
            publication = "COMMITTED"
        elif checkpoint_state == "EVIDENCE_FINALIZATION_PENDING":
            publication = "PENDING"
        else:
            publication = "NOT_STARTED"

    gate_active = (
        checkpoint_state in {"HUMAN_GATE", "FAILED_CLOSED"}
        or logical_state in {"HUMAN_GATE", "FAILED_CLOSED"}
        or checkpoint_state in TRANSITION_INTERRUPTED_STATES
    )
    finalization_incomplete = (
        checkpoint_state in FINALIZATION_STATES
        or publication in INCOMPLETE_PUBLICATION
    )

    if identity_status == "INVALID" or evidence_availability == "INVALID":
        gate_status = "INVALID"
        reason_code = "IDENTITY_CONFLICT"
        recovery_mode = "HUMAN_REMEDIATION_REQUIRED"
        allowed_actions = _actions(
            "INSPECT_EVIDENCE",
            "REMEDIATE_EXTERNAL_STATE",
            "NO_AUTOMATIC_REPAIR",
        )
    elif checkpoint is None:
        gate_status = "NOT_APPLICABLE"
        reason_code = "NO_CHECKPOINT"
        recovery_mode = "NO_ACTION"
        allowed_actions = _actions("NO_AUTOMATIC_REPAIR")
    elif evidence_availability == "UNAVAILABLE" and (
        gate_active or finalization_incomplete
    ):
        gate_status = "UNAVAILABLE"
        reason_code = "REQUIRED_EVIDENCE_UNAVAILABLE"
        recovery_mode = "HUMAN_REMEDIATION_REQUIRED"
        allowed_actions = _actions(
            "INSPECT_EVIDENCE",
            "REMEDIATE_EXTERNAL_STATE",
            "NO_AUTOMATIC_REPAIR",
        )
    else:
        reason_code = _reason_code(
            checkpoint_state, logical, final, gate_active=gate_active
        )
        gate_status = "ACTIVE" if gate_active else "NOT_APPLICABLE"
        if finalization_incomplete:
            recovery_mode = "FINALIZATION_ONLY"
            allowed_actions = _actions(
                "INSPECT_EVIDENCE",
                "FINALIZE_EVIDENCE",
                "NO_AUTOMATIC_REPAIR",
            )
        elif (
            gate_active
            and publication == "PUSHED"
            and reason_code != "HUMAN_GATE_REASON_UNAVAILABLE"
        ):
            recovery_mode = "NEW_RUN_AFTER_REVIEW"
            allowed_actions = _actions(
                "INSPECT_EVIDENCE",
                "REMEDIATE_EXTERNAL_STATE",
                "START_NEW_RUN_AFTER_HUMAN_REVIEW",
                "NO_AUTOMATIC_REPAIR",
            )
        elif gate_active:
            recovery_mode = "HUMAN_REMEDIATION_REQUIRED"
            allowed_actions = _actions(
                "INSPECT_EVIDENCE",
                "REMEDIATE_EXTERNAL_STATE",
                "NO_AUTOMATIC_REPAIR",
            )
        else:
            recovery_mode = "NO_ACTION"
            allowed_actions = _actions("INSPECT_EVIDENCE", "NO_AUTOMATIC_REPAIR")

    reason = REASON_TEXT[reason_code]
    return {
        "schema_version": SCHEMA_VERSION,
        "gate_status": gate_status,
        "reason_code": reason_code,
        "public_reason": bounded_public_reason(reason, reason_code),
        "checkpoint_state": checkpoint_state,
        "logical_outcome": logical_state,
        "runtime_transition": runtime_transition,
        "evidence_publication": publication,
        "evidence_availability": evidence_availability,
        "recovery_mode": recovery_mode,
        "allowed_actions": allowed_actions,
        "artifacts": artifacts,
    }
