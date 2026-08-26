"""Blocking, serial Ollama chat client using only the Python standard library."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from typing import Any, Callable, Mapping, Optional, Sequence

from .inference import ChatResult, ToolCall


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: float = 900.0,
        options: Optional[Mapping[str, Any]] = None,
        think: Optional[bool] = None,
        opener: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._url = base_url.rstrip("/") + "/api/chat"
        self._timeout = timeout_seconds
        self._options = dict(options or {})
        self._think = think
        self._opener = opener or urllib.request.urlopen
        # One lock guarantees that Reviewer and Executor never infer concurrently.
        self._serial_lock = threading.Lock()

    def chat(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        tools: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> ChatResult:
        request_body: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "stream": False,
        }
        if tools:
            request_body["tools"] = list(tools)
        if self._options:
            request_body["options"] = self._options
        if self._think is not None:
            request_body["think"] = self._think

        request = urllib.request.Request(
            self._url,
            data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._serial_lock:
                # Returning from this blocking request is the sole turn-completion signal.
                with self._opener(request, timeout=self._timeout) as response:
                    raw = response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise OllamaError(f"blocking Ollama chat request failed: {exc}") from exc

        try:
            document = json.loads(raw.decode("utf-8"))
            message = document["message"]
            content = message.get("content", "")
            if not isinstance(content, str):
                raise TypeError("message.content is not a string")
            tool_calls = []
            for raw_call in message.get("tool_calls", []):
                function = raw_call["function"]
                arguments = function.get("arguments", {})
                if not isinstance(arguments, dict):
                    raise TypeError("tool arguments are not an object")
                tool_calls.append(ToolCall(name=function["name"], arguments=arguments))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise OllamaError(f"invalid Ollama chat response: {exc}") from exc

        return ChatResult(
            content=content,
            tool_calls=tuple(tool_calls),
            model=document.get("model"),
            done_reason=document.get("done_reason"),
        )
