#!/usr/bin/env python3
"""Exercise the real orchestrator with deterministic scripted inference responses."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, List

from miniloop.envelope import Role
from miniloop.eventlog import RunEventLogger
from miniloop.inference import ChatResult, ToolCall
from miniloop.orchestrator import MiniloopOrchestrator
from miniloop.receiver import ReceiverReader, ReviewerReceiverSetter, initialize_receiver
from miniloop.runtime_updater import RuntimeUpdater
from miniloop.sandbox import DockerSandbox
from miniloop.session import LogicalSession
from miniloop.toolbox import ExecutorToolbox, ReviewerToolbox


class ScriptedBackend:
    def __init__(self) -> None:
        self.reviewer: List[ChatResult] = [
            ChatResult("  Implement the bounded task. Literal ACCEPT is only text.\n"),
            ChatResult("REJECT: repair the evidence locator without a JSON schema.\n"),
            ChatResult(
                "",
                tool_calls=(ToolCall("set_receiver", {"receiver": "human"}),),
            ),
        ]
        self.executor: List[ChatResult] = [
            ChatResult("Self-check PASS; first evidence is intentionally insufficient.\n"),
            ChatResult("Repair complete; evidence locator: /workspace/result.txt\n"),
        ]

    def chat(self, *, model: str, messages: Any, tools: Any = None) -> ChatResult:
        queue = self.reviewer if messages[0]["content"] == "reviewer demo" else self.executor
        if not queue:
            raise RuntimeError("scripted response queue exhausted")
        return queue.pop(0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory() as temporary_name:
        temporary = Path(temporary_name)
        receiver = temporary / "receiver"
        runtime = temporary / "runtime.md"
        workspace = temporary / "workspace"
        workspace.mkdir()
        initialize_receiver(receiver)
        shutil.copyfile(project / "docs" / "miniloop_runtime.md", runtime)
        original_runtime = runtime.read_text(encoding="utf-8")
        sandbox = DockerSandbox(
            workspace=workspace,
            image="not-invoked:scripted-demo",
            forbidden_host_paths=(receiver, runtime),
        )
        summary = MiniloopOrchestrator(
            run_id="step1-scripted-demo",
            model="same-local-model-id",
            backend=ScriptedBackend(),
            reviewer_session=LogicalSession(
                role=Role.REVIEWER,
                model="same-local-model-id",
                system_instruction="reviewer demo",
            ),
            executor_session=LogicalSession(
                role=Role.EXECUTOR,
                model="same-local-model-id",
                system_instruction="executor demo",
            ),
            receiver_reader=ReceiverReader(receiver),
            reviewer_tools=ReviewerToolbox(
                receiver_setter=ReviewerReceiverSetter(receiver),
                runtime_updater=RuntimeUpdater(runtime),
                sandbox=sandbox,
            ),
            executor_tools=ExecutorToolbox(sandbox),
            event_logger=RunEventLogger(path=args.output, run_id="step1-scripted-demo"),
        ).run(reviewer_initial_context="private governance context")

        result = {
            "summary": {**summary.__dict__, "outcome": summary.outcome.value},
            "authoritative_runtime_was_not_targeted": runtime.read_text(encoding="utf-8")
            == original_runtime,
            "temporary_receiver": ReceiverReader(receiver).read().value,
            "event_log": str(args.output.resolve()),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
