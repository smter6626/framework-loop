#!/usr/bin/env python3
"""F3 workload configuration and read-only operator command helpers.

The mutation runner remains the only control-plane state machine.  This module
strictly compiles a versioned JSON config into its existing argparse namespace
and projects checkpoint/F2 evidence for operator-only commands.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple


SCRIPT_PATH = Path(__file__).resolve()
CONFIG_SCHEMA_VERSION = 1
OUTPUT_SCHEMA_VERSION = 1
MAX_PUBLIC_STRING_CHARS = 1024
SAFE_ACTIONS = frozenset({
    "RESUME_ALLOWED",
    "HUMAN_REVIEW_REQUIRED",
    "TERMINAL_SUCCESS",
    "TERMINAL_FAILURE",
    "START_NEW_RUN_ALLOWED",
    "STATE_UNAVAILABLE",
})
PROHIBITED_KEY = re.compile(
    r"(?:auth|credential|password|secret|token|prompt|peer|reasoning)", re.IGNORECASE
)
OBJECT_ID = re.compile(r"^[0-9a-f]{40}$")
SHA256_ID = re.compile(r"^[0-9a-f]{64}$")


class OperatorError(RuntimeError):
    """A stable operator/configuration invariant failed."""


def _load_runner() -> ModuleType:
    path = SCRIPT_PATH.with_name("run_mutation_loop.py")
    spec = importlib.util.spec_from_file_location("_f3_run_mutation_loop", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("mutation runner is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNNER = _load_runner()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")


def strict_json_bytes(data: bytes) -> Any:
    """Strict JSON without reflecting an untrusted duplicate key."""
    def pairs(items: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise OperatorError("duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(_value: str) -> None:
        raise OperatorError("invalid JSON constant")

    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=invalid_constant,
        )
    except OperatorError:
        raise
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise OperatorError("invalid JSON document") from exc


def _require_object(value: Any, fields: Sequence[str], label: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise OperatorError(f"{label} must be an object")
    for key in value:
        if not isinstance(key, str) or PROHIBITED_KEY.search(key):
            raise OperatorError("config contains a prohibited field")
    expected = set(fields)
    if set(value) != expected:
        raise OperatorError(f"{label} field set is invalid")
    return value


def _require_string(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise OperatorError(f"{label} must be a non-empty string")
    if "\x00" in value:
        raise OperatorError(f"{label} contains an invalid character")
    return value


def _require_positive_int(value: Any, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise OperatorError(f"{label} must be a positive integer")
    return value


def _require_positive_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise OperatorError(f"{label} must be a positive number")
    result = float(value)
    if result == float("inf") or result != result:
        raise OperatorError(f"{label} must be finite")
    return result


def _resolved_path(base: Path, value: Any, label: str) -> Path:
    text = _require_string(value, label)
    if text.startswith("~"):
        raise OperatorError(f"{label} must not use home-directory expansion")
    candidate = Path(text)
    if not candidate.is_absolute():
        candidate = base / candidate
    return candidate.resolve()


@dataclass(frozen=True)
class WorkloadConfig:
    path: Path
    raw_sha256: str
    resolved: Mapping[str, Any]
    resolved_sha256: str

    @property
    def workload_id(self) -> str:
        return str(self.resolved["workload_id"])

    def identity(self) -> Dict[str, Any]:
        return {
            "schema_version": CONFIG_SCHEMA_VERSION,
            "config_path": str(self.path),
            "raw_sha256": self.raw_sha256,
            "resolved_sha256": self.resolved_sha256,
            "workload_id": self.workload_id,
        }


def load_config(path: Path) -> WorkloadConfig:
    source = path.resolve()
    if not source.is_file() or source.is_symlink():
        raise OperatorError("workload config is missing or aliased")
    raw = source.read_bytes()
    value = strict_json_bytes(raw)
    top = _require_object(
        value,
        (
            "schema_version", "workload_id", "target", "governance",
            "profiles", "execution", "evidence", "framework_git",
        ),
        "config",
    )
    if top["schema_version"] != CONFIG_SCHEMA_VERSION:
        raise OperatorError("workload config schema version is unsupported")
    workload_id = RUNNER.P4.validate_run_id(
        _require_string(top["workload_id"], "workload_id")
    )
    target = _require_object(top["target"], ("repo", "branch"), "target")
    governance = _require_object(
        top["governance"],
        (
            "workload_static", "workload_runtime", "framework_repo",
            "framework_static", "framework_runtime",
        ),
        "governance",
    )
    profiles = _require_object(
        top["profiles"], ("reviewer_home", "executor_home"), "profiles"
    )
    execution = _require_object(
        top["execution"],
        (
            "codex_bin", "max_cycles", "timeout_seconds",
            "progress_interval_seconds", "enable_runtime_transition",
        ),
        "execution",
    )
    evidence = _require_object(
        top["evidence"], ("runs_root", "state_root", "summary_root"), "evidence"
    )
    framework_git = _require_object(
        top["framework_git"], ("branch", "remote", "push_ref"), "framework_git"
    )
    base = source.parent
    resolved: Dict[str, Any] = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "workload_id": workload_id,
        "target": {
            "repo": str(_resolved_path(base, target["repo"], "target.repo")),
            "branch": _require_string(target["branch"], "target.branch"),
        },
        "governance": {
            name: str(_resolved_path(base, governance[name], f"governance.{name}"))
            for name in (
                "workload_static", "workload_runtime", "framework_repo",
                "framework_static", "framework_runtime",
            )
        },
        "profiles": {
            name: str(_resolved_path(base, profiles[name], f"profiles.{name}"))
            for name in ("reviewer_home", "executor_home")
        },
        "execution": {
            "codex_bin": str(_resolved_path(base, execution["codex_bin"], "execution.codex_bin"))
            if os.sep in _require_string(execution["codex_bin"], "execution.codex_bin")
            else _require_string(execution["codex_bin"], "execution.codex_bin"),
            "max_cycles": _require_positive_int(execution["max_cycles"], "execution.max_cycles"),
            "timeout_seconds": _require_positive_int(
                execution["timeout_seconds"], "execution.timeout_seconds"
            ),
            "progress_interval_seconds": _require_positive_number(
                execution["progress_interval_seconds"],
                "execution.progress_interval_seconds",
            ),
            "enable_runtime_transition": execution["enable_runtime_transition"],
        },
        "evidence": {
            name: str(_resolved_path(base, evidence[name], f"evidence.{name}"))
            for name in ("runs_root", "state_root", "summary_root")
        },
        "framework_git": {
            name: _require_string(framework_git[name], f"framework_git.{name}")
            for name in ("branch", "remote", "push_ref")
        },
    }
    if type(resolved["execution"]["enable_runtime_transition"]) is not bool:
        raise OperatorError("execution.enable_runtime_transition must be boolean")
    if Path(resolved["profiles"]["reviewer_home"]) == Path(
        resolved["profiles"]["executor_home"]
    ):
        raise OperatorError("Reviewer and Executor profiles must be distinct")
    push_ref = resolved["framework_git"]["push_ref"]
    if not push_ref.startswith("refs/heads/"):
        raise OperatorError("framework_git.push_ref must name refs/heads")
    resolved_sha = sha256_bytes(canonical_json(resolved))
    return WorkloadConfig(source, sha256_bytes(raw), resolved, resolved_sha)


def build_runner_args(
    config: WorkloadConfig, *, run_id: Optional[str] = None, resume: bool = False
) -> argparse.Namespace:
    value = config.resolved
    execution = value["execution"]
    governance = value["governance"]
    profiles = value["profiles"]
    evidence = value["evidence"]
    framework_git = value["framework_git"]
    selected_run_id = run_id or RUNNER.P4.default_run_id()
    RUNNER.P4.validate_run_id(selected_run_id)
    return argparse.Namespace(
        codex_bin=execution["codex_bin"],
        enable_runtime_transition=execution["enable_runtime_transition"],
        executor_home=Path(profiles["executor_home"]),
        framework_branch=framework_git["branch"],
        framework_push_ref=framework_git["push_ref"],
        framework_remote=framework_git["remote"],
        framework_repo=Path(governance["framework_repo"]),
        framework_runtime=Path(governance["framework_runtime"]),
        framework_static=Path(governance["framework_static"]),
        max_cycles=execution["max_cycles"],
        operator_config_identity=config.identity(),
        progress_interval_seconds=execution["progress_interval_seconds"],
        resume=resume,
        reviewer_home=Path(profiles["reviewer_home"]),
        run_id=selected_run_id,
        runs_root=Path(evidence["runs_root"]),
        state_root=Path(evidence["state_root"]),
        summary_root=Path(evidence["summary_root"]),
        target_branch=value["target"]["branch"],
        target_repo=Path(value["target"]["repo"]),
        timeout_seconds=execution["timeout_seconds"],
        workload_id=value["workload_id"],
        workload_runtime=Path(governance["workload_runtime"]),
        workload_static=Path(governance["workload_static"]),
    )


def checkpoint_path(config: WorkloadConfig) -> Path:
    return (
        Path(config.resolved["evidence"]["state_root"])
        / config.workload_id
        / "checkpoint.json"
    ).resolve()


def _read_object(path: Path, label: str) -> Dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise OperatorError(f"{label} is unavailable")
    value = strict_json_bytes(path.read_bytes())
    if not isinstance(value, dict):
        raise OperatorError(f"{label} is invalid")
    return value


def load_bound_checkpoint(config: WorkloadConfig) -> Dict[str, Any]:
    checkpoint = _read_object(checkpoint_path(config), "checkpoint")
    if checkpoint.get("schema_version") != 1 or not isinstance(checkpoint.get("state"), str):
        raise OperatorError("checkpoint schema is unsupported")
    configuration = checkpoint.get("configuration")
    if not isinstance(configuration, dict):
        raise OperatorError("checkpoint configuration is missing")
    saved = configuration.get("operator_config_identity")
    if saved is None:
        raise OperatorError("legacy checkpoint has no operator config identity")
    if saved != config.identity():
        raise OperatorError("workload config identity differs from checkpoint")
    if configuration.get("workload_id") != config.workload_id:
        raise OperatorError("checkpoint workload identity is inconsistent")
    run_id = checkpoint.get("run_id")
    if not isinstance(run_id, str) or RUNNER.P4.validate_run_id(run_id) != run_id:
        raise OperatorError("checkpoint run identity is invalid")
    expected_run_root = (
        Path(config.resolved["evidence"]["runs_root"]) / run_id
    ).resolve()
    if checkpoint.get("run_root") != str(expected_run_root):
        raise OperatorError("checkpoint run root is inconsistent")
    return checkpoint


def resume_runner_args(config: WorkloadConfig) -> argparse.Namespace:
    checkpoint = load_bound_checkpoint(config)
    return build_runner_args(config, run_id=checkpoint["run_id"], resume=True)


def _public_text(value: Any) -> str:
    text = RUNNER.escape_public_text(str(value))
    if len(text) <= MAX_PUBLIC_STRING_CHARS:
        return text
    return text[: MAX_PUBLIC_STRING_CHARS - 14] + "...[truncated]"


def _check(name: str, function: Callable[[], Any]) -> Dict[str, Any]:
    try:
        value = function()
    except (OSError, RuntimeError, ValueError, OperatorError):
        return {
            "name": name,
            "status": "FAIL",
            "code": f"{name.upper()}_FAILED",
            "detail": _public_text(f"{name} check failed"),
        }
    return {
        "name": name,
        "status": "PASS",
        "code": f"{name.upper()}_PASSED",
        "detail": value if isinstance(value, (dict, list, bool, int, float)) else _public_text(value),
    }


def _overall(checks: Sequence[Mapping[str, Any]]) -> str:
    if any(item.get("status") == "FAIL" for item in checks):
        return "FAIL"
    if any(item.get("status") == "UNAVAILABLE" for item in checks):
        return "UNAVAILABLE"
    return "PASS"


def envelope(
    command: str,
    config: Optional[WorkloadConfig],
    *,
    overall: str,
    checks: Optional[Sequence[Mapping[str, Any]]] = None,
    result: Optional[Mapping[str, Any]] = None,
    artifacts: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "command": command,
        "config_identity": config.identity() if config is not None else None,
        "overall_status": overall,
        "checks": list(checks or []),
        "result": dict(result or {}),
        "artifacts": dict(artifacts or {}),
    }


def doctor(config: WorkloadConfig) -> Dict[str, Any]:
    args = build_runner_args(config)

    def python_check() -> str:
        if sys.version_info < (3, 9):
            raise OperatorError("unsupported Python")
        RUNNER.validate_json_schema({}, {"type": "object"})
        return f"python-{sys.version_info.major}.{sys.version_info.minor}"

    def codex_check() -> str:
        executable = shutil.which(args.codex_bin) or (
            args.codex_bin if Path(args.codex_bin).is_file() and os.access(args.codex_bin, os.X_OK) else None
        )
        if executable is None:
            raise OperatorError("Codex unavailable")
        completed = subprocess.run(
            [str(executable), "--version"], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False, timeout=10,
        )
        if completed.returncode != 0 or not completed.stdout.strip():
            raise OperatorError("Codex version unavailable")
        return "codex-version-readable"

    def profiles_check() -> str:
        if args.reviewer_home.resolve() == args.executor_home.resolve():
            raise OperatorError("profiles overlap")
        if not args.reviewer_home.is_dir() or not args.executor_home.is_dir():
            raise OperatorError("profile missing")
        return "distinct-profile-directories"

    def git_check() -> str:
        completed = subprocess.run(
            ["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise OperatorError("Git unavailable")
        return "git-available"

    def target_check() -> Dict[str, Any]:
        state = RUNNER.capture_target_state(
            args.target_repo, args.target_branch, require_clean=True
        )
        return {"branch": state.branch, "head": state.head, "clean": state.clean}

    def governance_check() -> str:
        RUNNER.capture_governance({
            RUNNER.FRAMEWORK_STATIC: args.framework_static,
            RUNNER.FRAMEWORK_RUNTIME: args.framework_runtime,
            RUNNER.WORKLOAD_STATIC: args.workload_static,
            RUNNER.WORKLOAD_RUNTIME: args.workload_runtime,
        })
        for name in RUNNER.TURN_SCHEMAS:
            RUNNER.strict_json(RUNNER.schema_path(name).read_bytes())
        return "governance-and-schemas-readable"

    def framework_check() -> Dict[str, Any]:
        state = RUNNER.validate_framework_preflight(args)
        return {
            "branch": state["branch"],
            "head": state["head"],
            "remote_head": state["remote_head"],
        }

    def storage_check() -> str:
        RUNNER.validate_preflight(args)
        return "storage-boundaries-and-ignore-valid"

    checks = [
        _check("python_dependencies", python_check),
        _check("codex", codex_check),
        _check("profiles", profiles_check),
        _check("git", git_check),
        _check("target", target_check),
        _check("governance_schemas", governance_check),
        _check("framework_remote", framework_check),
        _check("storage_preflight", storage_check),
    ]
    overall = _overall(checks)
    return envelope("doctor", config, overall=overall, checks=checks, result={
        "config_valid": True,
        "operator_ready": overall == "PASS",
    })


def preflight(config: WorkloadConfig) -> Dict[str, Any]:
    args = build_runner_args(config)
    try:
        target, governance = RUNNER.validate_preflight(args)
        report = RUNNER.preflight_report(target, governance, args)
        return envelope(
            "preflight", config, overall="PASS",
            checks=[{"name": "runner_preflight", "status": "PASS", "code": "PREFLIGHT_PASSED", "detail": "existing runner validator passed"}],
            result=report,
        )
    except (OSError, RuntimeError, ValueError):
        return envelope(
            "preflight", config, overall="FAIL",
            checks=[{"name": "runner_preflight", "status": "FAIL", "code": "PREFLIGHT_FAILED", "detail": "existing runner validator failed"}],
        )


def run_mutation(config: WorkloadConfig, *, resume: bool = False) -> Tuple[int, Path]:
    args = resume_runner_args(config) if resume else build_runner_args(config)
    target, governance = RUNNER.validate_preflight(args)
    return RUNNER.orchestrate(
        args=args, target_initial=target, governance_initial=governance
    )


def _status_paths(config: WorkloadConfig, checkpoint: Mapping[str, Any]) -> Dict[str, str]:
    run_root = Path(str(checkpoint["run_root"])).resolve()
    summary = Path(config.resolved["evidence"]["summary_root"]) / f"{checkpoint['run_id']}.md"
    return {
        "config": str(config.path),
        "checkpoint": str(checkpoint_path(config)),
        "run_root": str(run_root),
        "manifest": str(run_root / "manifest.json"),
        "control_events": str(run_root / RUNNER.PROGRESS.EVENTS_FILENAME),
        "live_status": str(run_root / RUNNER.PROGRESS.STATUS_FILENAME),
        "tracked_summary": str(summary.resolve()),
    }


def safe_next_action(checkpoint: Mapping[str, Any]) -> str:
    state = checkpoint.get("state")
    logical = checkpoint.get("logical_outcome")
    outcome = logical.get("state") if isinstance(logical, dict) else None
    final = checkpoint.get("final_result")
    publication = final.get("evidence_publication") if isinstance(final, dict) else None
    if state == RUNNER.HUMAN_GATE or outcome == RUNNER.HUMAN_GATE:
        return "HUMAN_REVIEW_REQUIRED"
    if publication in {"FAILED", "PENDING", "COMMITTED"}:
        return "RESUME_ALLOWED"
    if state == RUNNER.FRAMEWORK_EVIDENCE_PUSHED:
        return (
            "TERMINAL_SUCCESS"
            if outcome == RUNNER.RUNTIME_TRANSITION_COMMITTED
            else "TERMINAL_FAILURE"
        )
    if state == RUNNER.RUNTIME_TRANSITION_COMMITTED and publication == "NOT_ENABLED":
        return "TERMINAL_SUCCESS"
    if state == RUNNER.FAILED_CLOSED and publication == "NOT_ENABLED":
        return "TERMINAL_FAILURE"
    if isinstance(state, str):
        return "RESUME_ALLOWED"
    return "STATE_UNAVAILABLE"


def _validate_observation(
    checkpoint: Mapping[str, Any], paths: Mapping[str, str]
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], bool]:
    progress = checkpoint.get("progress")
    if not isinstance(progress, dict):
        raise OperatorError("checkpoint progress metadata is unavailable")
    events_path = Path(paths["control_events"])
    events, incomplete = RUNNER.PROGRESS.scan_events(
        events_path, recover_incomplete_tail=False
    )
    cursor = progress.get("sequence")
    if type(cursor) is not int or cursor < 0 or cursor > len(events):
        raise OperatorError("checkpoint progress cursor is invalid")
    if cursor and events[cursor - 1].get("event_id") != progress.get("event_id"):
        raise OperatorError("checkpoint progress cursor identity is invalid")
    RUNNER.PROGRESS.validate_checkpoint_suffix(
        events=events,
        cursor=cursor,
        checkpoint_progress=progress,
        checkpoint_state=checkpoint["state"],
        run_id=checkpoint["run_id"],
    )
    status_path = Path(paths["live_status"])
    status: Optional[Dict[str, Any]] = None
    if status_path.is_file() and not status_path.is_symlink():
        status = _read_object(status_path, "live status")
        RUNNER.PROGRESS.validate_event(status)
        if not events or status != events[-1]:
            raise OperatorError("live status differs from the event projection")
    return status, events, incomplete


def status(config: WorkloadConfig) -> Dict[str, Any]:
    path = checkpoint_path(config)
    if not path.exists():
        return envelope(
            "status", config, overall="PASS",
            result={
                "workload_id": config.workload_id,
                "run_id": None,
                "checkpoint_state": None,
                "safe_next_action": "START_NEW_RUN_ALLOWED",
                "observation_availability": "UNAVAILABLE",
            },
            artifacts={"config": str(config.path), "checkpoint": str(path)},
        )
    try:
        checkpoint = load_bound_checkpoint(config)
    except OperatorError:
        return envelope(
            "status", config, overall="FAIL",
            result={"workload_id": config.workload_id, "safe_next_action": "STATE_UNAVAILABLE"},
            artifacts={"config": str(config.path), "checkpoint": str(path)},
        )
    paths = _status_paths(config, checkpoint)
    observation = "AVAILABLE"
    live: Optional[Dict[str, Any]] = None
    incomplete = False
    try:
        live, _events, incomplete = _validate_observation(checkpoint, paths)
        if live is None or incomplete:
            observation = "UNAVAILABLE"
    except (OSError, RuntimeError, ValueError, OperatorError):
        observation = "UNAVAILABLE"
    projection = live if live is not None and not incomplete else checkpoint.get("progress", {})
    if not isinstance(projection, dict):
        projection = {}
    final = checkpoint.get("final_result")
    if not isinstance(final, dict):
        final = {}
    logical = checkpoint.get("logical_outcome")
    logical_state = logical.get("state") if isinstance(logical, dict) else final.get("logical_outcome")
    result = {
        "workload_id": config.workload_id,
        "run_id": checkpoint.get("run_id"),
        "checkpoint_state": checkpoint.get("state"),
        "cycle": projection.get("cycle", checkpoint.get("cycle_number")),
        "role": projection.get("role"),
        "run_elapsed_seconds": projection.get("run_elapsed_seconds"),
        "stage_elapsed_seconds": projection.get("stage_elapsed_seconds"),
        "timeout_remaining_seconds": projection.get("timeout_remaining_seconds"),
        "last_activity": projection.get("last_activity"),
        "target_head": projection.get("target_head"),
        "logical_outcome": logical_state,
        "runtime_transition": final.get("runtime_transition"),
        "evidence_publication": final.get("evidence_publication"),
        "observation_availability": observation,
        "human_gate": checkpoint.get("state") == RUNNER.HUMAN_GATE or logical_state == RUNNER.HUMAN_GATE,
        "failed_closed": checkpoint.get("state") == RUNNER.FAILED_CLOSED or logical_state == RUNNER.FAILED_CLOSED,
        "safe_next_action": safe_next_action(checkpoint),
    }
    return envelope("status", config, overall="PASS", result=result, artifacts=paths)


def _inspection_check(name: str, function: Callable[[], Any]) -> Dict[str, Any]:
    try:
        detail = function()
    except FileNotFoundError:
        return {"name": name, "status": "UNAVAILABLE", "code": f"{name.upper()}_UNAVAILABLE", "detail": f"{name} artifact is unavailable"}
    except (OSError, RuntimeError, ValueError, OperatorError):
        return {"name": name, "status": "FAIL", "code": f"{name.upper()}_FAIL", "detail": f"{name} validation did not pass"}
    return {"name": name, "status": "PASS", "code": f"{name.upper()}_PASSED", "detail": detail}


def inspect_run(config: WorkloadConfig) -> Dict[str, Any]:
    try:
        checkpoint = load_bound_checkpoint(config)
    except OperatorError:
        return envelope(
            "inspect", config, overall="FAIL",
            checks=[{"name": "checkpoint_identity", "status": "FAIL", "code": "CHECKPOINT_IDENTITY_FAILED", "detail": "checkpoint identity validation did not pass"}],
            result={"safe_next_action": "STATE_UNAVAILABLE"},
            artifacts={"config": str(config.path), "checkpoint": str(checkpoint_path(config))},
        )
    paths = _status_paths(config, checkpoint)
    run_root = Path(paths["run_root"])

    def manifest_check() -> str:
        if not Path(paths["manifest"]).is_file():
            raise FileNotFoundError("local manifest is unavailable")
        manifest = _read_object(Path(paths["manifest"]), "manifest")
        if manifest.get("run_id") != checkpoint["run_id"]:
            raise OperatorError("manifest run identity mismatch")
        run_configuration = manifest.get("run_configuration")
        if not isinstance(run_configuration, dict) or run_configuration.get(
            "operator_config_identity"
        ) != config.identity():
            raise OperatorError("manifest config identity mismatch")
        if manifest.get("final_result") != checkpoint.get("final_result"):
            raise OperatorError("manifest final result differs from checkpoint")
        return "manifest identity matches checkpoint"

    observation_result: Dict[str, Any] = {}

    def event_check() -> str:
        if not Path(paths["control_events"]).is_file() or not Path(paths["live_status"]).is_file():
            raise FileNotFoundError("local observation artifacts are unavailable")
        status_value, events, incomplete = _validate_observation(checkpoint, paths)
        observation_result.update({
            "event_count": len(events),
            "status_available": status_value is not None,
            "incomplete_tail": incomplete,
        })
        if incomplete:
            raise FileNotFoundError("partial event tail is not modified by inspect")
        return "event sequence, hash, suffix, and live projection are valid"

    def summary_check() -> str:
        summary_path = Path(paths["tracked_summary"])
        progress = checkpoint.get("summary_progress", [])
        if not isinstance(progress, list):
            raise OperatorError("summary progress is invalid")
        if not run_root.is_dir():
            raise FileNotFoundError("local raw evidence root is unavailable")
        expected = RUNNER.P63.expected_summary_bytes(
            checkpoint["run_id"], run_root, progress
        )
        if progress:
            if not summary_path.is_file() or summary_path.is_symlink():
                raise OperatorError("tracked summary is missing")
            if summary_path.read_bytes() != expected:
                raise OperatorError("tracked summary bytes differ")
        elif summary_path.exists():
            raise OperatorError("unexpected summary exists")
        try:
            for record in progress:
                entry = RUNNER.P63._entry_from_record(record)
                artifacts = entry.get("raw_artifacts")
                if not isinstance(artifacts, list):
                    raise OperatorError("summary raw artifact list is invalid")
                for artifact in artifacts:
                    locator = artifact.get("locator") if isinstance(artifact, dict) else None
                    if not isinstance(locator, str) or not Path(locator).is_file():
                        raise FileNotFoundError("local raw evidence is unavailable")
            RUNNER.P63.validate_summary_artifacts(
                run_id=checkpoint["run_id"], run_root=run_root, progress=progress
            )
        except FileNotFoundError:
            raise
        return "tracked summary and available raw artifact identities are valid"

    def framework_commit_check() -> str:
        commit = checkpoint.get("framework_commit_id")
        plan = checkpoint.get("framework_commit_plan")
        if commit is None and plan is None:
            raise FileNotFoundError("framework evidence commit is not available")
        if not isinstance(commit, str) or not OBJECT_ID.fullmatch(commit) or not isinstance(plan, dict):
            raise OperatorError("framework commit checkpoint is incomplete")
        RUNNER.P63._validate_commit(plan, commit)
        return "framework evidence commit matches its checkpointed plan"

    def framework_push_check() -> str:
        if not checkpoint.get("framework_evidence_pushed"):
            raise FileNotFoundError("framework evidence push is not available")
        commit = checkpoint.get("framework_commit_id")
        plan = checkpoint.get("framework_commit_plan")
        if not isinstance(commit, str) or not isinstance(plan, dict):
            raise OperatorError("framework push identity is incomplete")
        observed = RUNNER.P63.remote_head(
            Path(plan["repo"]), plan["remote"], plan["push_ref"]
        )
        if observed != commit:
            raise OperatorError("framework remote does not contain the evidence commit")
        return "framework remote ref matches the evidence commit"

    def target_check() -> str:
        current = RUNNER.capture_target_state(
            Path(config.resolved["target"]["repo"]),
            config.resolved["target"]["branch"],
            require_clean=True,
        )
        expected = checkpoint.get("target_after") or checkpoint.get("target_before") or checkpoint.get("target_initial")
        if not isinstance(expected, dict) or current.metadata() != expected:
            raise OperatorError("target identity differs from checkpoint evidence")
        return "target branch, HEAD, and cleanliness match checkpoint"

    def target_evidence_check() -> str:
        progress = checkpoint.get("summary_progress")
        if not isinstance(progress, list):
            raise OperatorError("summary progress is invalid")
        target_repo = Path(config.resolved["target"]["repo"]).resolve()
        checked = 0
        for record in progress:
            entry = RUNNER.P63._entry_from_record(record)
            evidence_items = entry.get("structured_evidence")
            if evidence_items is None:
                continue
            if not isinstance(evidence_items, list):
                raise OperatorError("structured evidence list is invalid")
            for item in evidence_items:
                if not isinstance(item, dict):
                    raise OperatorError("structured evidence item is invalid")
                kind = item.get("kind")
                locator = item.get("locator")
                expected_sha = item.get("sha256")
                if (
                    kind not in {"commit", "file", "artifact", "test"}
                    or not isinstance(locator, str)
                    or not isinstance(expected_sha, str)
                    or SHA256_ID.fullmatch(expected_sha) is None
                ):
                    raise OperatorError("structured evidence declaration is invalid")
                if kind == "commit":
                    if OBJECT_ID.fullmatch(locator) is None:
                        raise OperatorError("commit evidence locator is invalid")
                    content = RUNNER.git_bytes(
                        target_repo, ["cat-file", "commit", locator]
                    )
                else:
                    evidence_path = Path(locator)
                    if (
                        not evidence_path.is_absolute()
                        or not evidence_path.is_file()
                        or evidence_path.is_symlink()
                        or not (
                            RUNNER.P4.path_is_within(evidence_path, target_repo)
                            or RUNNER.P4.path_is_within(evidence_path, run_root)
                        )
                    ):
                        raise OperatorError("file evidence locator is invalid")
                    content = evidence_path.read_bytes()
                if sha256_bytes(content) != expected_sha:
                    raise OperatorError("structured evidence hash differs")
                checked += 1
        if checked == 0:
            raise FileNotFoundError("structured target evidence is unavailable")
        return f"{checked} target evidence locator(s) are valid"

    checks = [
        {"name": "checkpoint_identity", "status": "PASS", "code": "CHECKPOINT_IDENTITY_PASSED", "detail": "checkpoint is bound to the exact config identity"},
        _inspection_check("manifest", manifest_check),
        _inspection_check("observation", event_check),
        _inspection_check("summary", summary_check),
        _inspection_check("framework_commit", framework_commit_check),
        _inspection_check("framework_push", framework_push_check),
        _inspection_check("target", target_check),
        _inspection_check("target_evidence", target_evidence_check),
    ]
    overall = _overall(checks)
    return envelope(
        "inspect", config, overall=overall, checks=checks,
        result={
            "workload_id": config.workload_id,
            "run_id": checkpoint["run_id"],
            "checkpoint_state": checkpoint["state"],
            "safe_next_action": safe_next_action(checkpoint) if overall != "FAIL" else "STATE_UNAVAILABLE",
            **observation_result,
        },
        artifacts=paths,
    )


def emit_json(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")))


def exit_code_for(value: Mapping[str, Any]) -> int:
    return 1 if value.get("overall_status") == "FAIL" else 0
