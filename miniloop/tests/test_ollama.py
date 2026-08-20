from __future__ import annotations

import json
import unittest

from miniloop.ollama import OllamaClient, OllamaError


class _Response:
    def __init__(self, document: object) -> None:
        self._raw = json.dumps(document).encode("utf-8")

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._raw


class OllamaClientTests(unittest.TestCase):
    def test_chat_is_blocking_non_streaming_and_preserves_content(self) -> None:
        observed = {}

        def opener(request: object, timeout: float) -> _Response:
            observed["body"] = json.loads(request.data.decode("utf-8"))
            observed["timeout"] = timeout
            return _Response(
                {
                    "model": "qwen35b-64k:latest",
                    "done_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "  raw output\n",
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "set_receiver",
                                    "arguments": {"receiver": "human"},
                                }
                            }
                        ],
                    },
                }
            )

        client = OllamaClient(timeout_seconds=123, think=False, opener=opener)
        result = client.chat(
            model="qwen35b-64k:latest",
            messages=[{"role": "system", "content": "role"}],
            tools=[{"type": "function", "function": {"name": "set_receiver"}}],
        )

        self.assertIs(observed["body"]["stream"], False)
        self.assertIs(observed["body"]["think"], False)
        self.assertEqual(observed["body"]["model"], "qwen35b-64k:latest")
        self.assertEqual(observed["timeout"], 123)
        self.assertEqual(result.content, "  raw output\n")
        self.assertEqual(result.tool_calls[0].arguments, {"receiver": "human"})

    def test_string_tool_arguments_are_rejected_not_parsed(self) -> None:
        client = OllamaClient(
            opener=lambda request, timeout: _Response(
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {"function": {"name": "x", "arguments": '{"guess": true}'}}
                        ],
                    }
                }
            )
        )
        with self.assertRaises(OllamaError):
            client.chat(model="m", messages=[])


if __name__ == "__main__":
    unittest.main()
