"""Inference boundary shared by Ollama and deterministic test backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True)
class ChatResult:
    content: str
    tool_calls: Sequence[ToolCall] = field(default_factory=tuple)
    model: Optional[str] = None
    done_reason: Optional[str] = None


class InferenceBackend(Protocol):
    def chat(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        tools: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> ChatResult:
        ...


ToolDefinition = Dict[str, Any]
Message = Dict[str, Any]
MessageList = List[Message]
