#!/usr/bin/env python3
"""One bounded live request proving the local wrapper uses Ollama's blocking lifecycle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from miniloop.ollama import OllamaClient


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen35b-64k:latest")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--disable-thinking", action="store_true")
    args = parser.parse_args()
    tool = {
        "type": "function",
        "function": {
            "name": "set_receiver",
            "description": "Set receiver for this isolated smoke test only.",
            "parameters": {
                "type": "object",
                "properties": {"receiver": {"type": "string", "enum": ["human"]}},
                "required": ["receiver"],
                "additionalProperties": False,
            },
        },
    }
    result = OllamaClient(
        options={"temperature": 0, "num_predict": 128},
        think=False if args.disable_thinking else None,
    ).chat(
        model=args.model,
        messages=[
            {
                "role": "system",
                "content": "Use the provided native tool. Do not encode a tool call in text.",
            },
            {"role": "user", "content": "Call set_receiver with receiver human."},
        ],
        tools=[tool],
    )
    document = {
        "model_requested": args.model,
        "model_returned": result.model,
        "done_reason": result.done_reason,
        "thinking_disabled": args.disable_thinking,
        "content": result.content,
        "tool_calls": [
            {"name": call.name, "arguments": dict(call.arguments)}
            for call in result.tool_calls
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(document, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
