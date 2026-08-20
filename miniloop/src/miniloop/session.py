"""Isolated logical conversation state for one Miniloop role."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Mapping, Sequence

from .envelope import MessageEnvelope, Role
from .inference import ChatResult


class LogicalSession:
    def __init__(self, *, role: Role, model: str, system_instruction: str) -> None:
        if not model:
            raise ValueError("model must not be empty")
        if not system_instruction:
            raise ValueError("system instruction must not be empty")
        self.role = role
        self.model = model
        self._messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_instruction}
        ]

    @property
    def messages(self) -> Sequence[Mapping[str, Any]]:
        """Return a copy so callers cannot cross-mutate session history."""

        return tuple(copy.deepcopy(self._messages))

    def add_local_context(self, content: str) -> None:
        if not isinstance(content, str):
            raise TypeError("content must be a string")
        self._messages.append({"role": "user", "content": content})

    def receive_peer(self, envelope: MessageEnvelope) -> None:
        expected = Role.EXECUTOR if self.role is Role.REVIEWER else Role.REVIEWER
        if envelope.receiver is not self.role or envelope.sender is not expected:
            raise ValueError("envelope routing does not match this session")
        # This assignment is deliberately exact: no prefix, strip, parsing, or rewrite.
        self._messages.append({"role": "user", "content": envelope.payload})

    def record_assistant(self, result: ChatResult) -> None:
        message: Dict[str, Any] = {"role": "assistant", "content": result.content}
        if result.tool_calls:
            message["tool_calls"] = [
                {
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": dict(call.arguments),
                    },
                }
                for call in result.tool_calls
            ]
        self._messages.append(message)

    def record_tool_result(self, *, name: str, content: str) -> None:
        self._messages.append({"role": "tool", "tool_name": name, "content": content})
