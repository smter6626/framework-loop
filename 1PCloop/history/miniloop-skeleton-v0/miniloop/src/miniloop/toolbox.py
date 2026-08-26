"""Role-scoped runtime-enforced tools; free text is never treated as a tool call."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

from .inference import ToolCall, ToolDefinition
from .receiver import ReviewerReceiverSetter
from .runtime_updater import RuntimeUpdater
from .sandbox import DockerSandbox, SandboxResult


class ToolExecutionError(ValueError):
    pass


def _tool(name: str, description: str, properties: Dict[str, Any], required: Sequence[str]) -> ToolDefinition:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(required),
                "additionalProperties": False,
            },
        },
    }


def _string(description: str, *, enum: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {"type": "string", "description": description}
    if enum is not None:
        schema["enum"] = list(enum)
    return schema


def _required_string(arguments: Mapping[str, Any], name: str) -> str:
    value = arguments.get(name)
    if not isinstance(value, str):
        raise ToolExecutionError(f"{name} must be a string")
    return value


def _optional_string(arguments: Mapping[str, Any], name: str) -> Optional[str]:
    value = arguments.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ToolExecutionError(f"{name} must be a string when provided")
    return value


def _sandbox_payload(result: SandboxResult) -> Dict[str, Any]:
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


class ExecutorToolbox:
    """Executor receives only a writable-workspace Linux shell."""

    def __init__(self, sandbox: DockerSandbox) -> None:
        self._sandbox = sandbox

    @property
    def definitions(self) -> Sequence[ToolDefinition]:
        return (
            _tool(
                "run_shell",
                "Run an unrestricted shell command inside the Linux sandbox. Only /workspace is a writable host mount.",
                {"command": _string("Verbatim /bin/sh command")},
                ["command"],
            ),
        )

    def execute(self, call: ToolCall) -> str:
        if call.name != "run_shell":
            raise ToolExecutionError(f"Executor is not authorized for tool: {call.name}")
        command = _required_string(call.arguments, "command")
        return json.dumps(
            {"ok": True, **_sandbox_payload(self._sandbox.run(command))},
            ensure_ascii=False,
        )


class ReviewerToolbox:
    """Reviewer-only control/runtime capabilities plus read-only verification shell."""

    def __init__(
        self,
        *,
        receiver_setter: ReviewerReceiverSetter,
        runtime_updater: RuntimeUpdater,
        sandbox: DockerSandbox,
    ) -> None:
        self._receiver_setter = receiver_setter
        self._runtime = runtime_updater
        self._sandbox = sandbox

    @property
    def definitions(self) -> Sequence[ToolDefinition]:
        digest = {"expected_sha256": _string("Optional optimistic-concurrency Runtime digest")}
        provenance = {
            "step": _string("Step provenance"),
            "commit": _string("Git commit id provenance"),
            "body": _string("Markdown body; no H2 headings"),
            **digest,
        }
        return (
            _tool(
                "set_receiver",
                "Set the deterministic loop receiver control state.",
                {"receiver": _string("Next receiver", enum=["executor", "human"])},
                ["receiver"],
            ),
            _tool(
                "run_verification",
                "Independently run a command with /workspace mounted read-only.",
                {"command": _string("Verbatim /bin/sh verification command")},
                ["command"],
            ),
            _tool(
                "runtime_append_done",
                "Append a completed record with mandatory Step and commit provenance.",
                provenance,
                ["step", "commit", "body"],
            ),
            _tool(
                "runtime_append_other_note",
                "Append a correction/invalidation/supersession note with provenance.",
                provenance,
                ["step", "commit", "body"],
            ),
            _tool(
                "runtime_replace_active_step",
                "Replace only the mutable Active Step body.",
                {"body": _string("New Active Step body"), **digest},
                ["body"],
            ),
            _tool(
                "runtime_append_pending_task",
                "Append a pending task without removing existing pending text.",
                {"body": _string("Pending task body"), **digest},
                ["body"],
            ),
            _tool(
                "runtime_progress_pending_task",
                "Explicitly replace one exact pending fragment with its progressed form.",
                {
                    "expected": _string("Exact current pending fragment"),
                    "replacement": _string("Progressed pending fragment"),
                    **digest,
                },
                ["expected", "replacement"],
            ),
            _tool(
                "runtime_close_pending_task",
                "Explicitly mark one exact pending fragment closed and retain a closure record.",
                {
                    "expected": _string("Exact current pending fragment"),
                    "closure": _string("Closure evidence/reason record"),
                    **digest,
                },
                ["expected", "closure"],
            ),
            _tool(
                "runtime_replace_next_steps",
                "Replace only the mutable Next Steps body.",
                {"body": _string("New Next Steps body"), **digest},
                ["body"],
            ),
        )

    def execute(self, call: ToolCall) -> str:
        arguments = call.arguments
        expected_sha256 = _optional_string(arguments, "expected_sha256")
        handlers: Dict[str, Callable[[], Dict[str, Any]]] = {
            "set_receiver": lambda: {
                "receiver": self._receiver_setter.set_receiver(
                    _required_string(arguments, "receiver")
                ).value
            },
            "run_verification": lambda: _sandbox_payload(
                self._sandbox.run(
                    _required_string(arguments, "command"), read_only_workspace=True
                )
            ),
            "runtime_append_done": lambda: {
                "runtime_sha256": self._runtime.append_done(
                    step=_required_string(arguments, "step"),
                    commit=_required_string(arguments, "commit"),
                    body=_required_string(arguments, "body"),
                    expected_sha256=expected_sha256,
                )
            },
            "runtime_append_other_note": lambda: {
                "runtime_sha256": self._runtime.append_other_note(
                    step=_required_string(arguments, "step"),
                    commit=_required_string(arguments, "commit"),
                    body=_required_string(arguments, "body"),
                    expected_sha256=expected_sha256,
                )
            },
            "runtime_replace_active_step": lambda: {
                "runtime_sha256": self._runtime.replace_active_step(
                    body=_required_string(arguments, "body"),
                    expected_sha256=expected_sha256,
                )
            },
            "runtime_append_pending_task": lambda: {
                "runtime_sha256": self._runtime.append_pending_task(
                    body=_required_string(arguments, "body"),
                    expected_sha256=expected_sha256,
                )
            },
            "runtime_progress_pending_task": lambda: {
                "runtime_sha256": self._runtime.progress_pending_task(
                    expected=_required_string(arguments, "expected"),
                    replacement=_required_string(arguments, "replacement"),
                    expected_sha256=expected_sha256,
                )
            },
            "runtime_close_pending_task": lambda: {
                "runtime_sha256": self._runtime.close_pending_task(
                    expected=_required_string(arguments, "expected"),
                    closure=_required_string(arguments, "closure"),
                    expected_sha256=expected_sha256,
                )
            },
            "runtime_replace_next_steps": lambda: {
                "runtime_sha256": self._runtime.replace_next_steps(
                    body=_required_string(arguments, "body"),
                    expected_sha256=expected_sha256,
                )
            },
        }
        handler = handlers.get(call.name)
        if handler is None:
            raise ToolExecutionError(f"Reviewer is not authorized for tool: {call.name}")
        return json.dumps({"ok": True, **handler()}, ensure_ascii=False)
