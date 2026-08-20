from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from miniloop.envelope import Role
from miniloop.eventlog import RunEventLogger
from miniloop.inference import ChatResult, ToolCall
from miniloop.orchestrator import MiniloopOrchestrator, RunOutcome
from miniloop.receiver import (
    Receiver,
    ReceiverReader,
    ReviewerReceiverSetter,
    initialize_receiver,
)
from miniloop.runtime_updater import RuntimeUpdater
from miniloop.sandbox import DockerSandbox
from miniloop.session import LogicalSession
from miniloop.toolbox import ExecutorToolbox, ReviewerToolbox


class ScriptedBackend:
    def __init__(self, reviewer_results: list, executor_results: list) -> None:
        self.reviewer_results = list(reviewer_results)
        self.executor_results = list(executor_results)
        self.calls = []

    def chat(self, *, model: str, messages: object, tools: object = None) -> ChatResult:
        copied = copy.deepcopy(messages)
        role = "reviewer" if copied[0]["content"] == "reviewer system" else "executor"
        self.calls.append({"role": role, "model": model, "messages": copied, "tools": tools})
        queue = self.reviewer_results if role == "reviewer" else self.executor_results
        if not queue:
            raise AssertionError(f"unexpected {role} inference")
        return queue.pop(0)


class OrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.receiver_path = root / "control" / "receiver"
        initialize_receiver(self.receiver_path)
        project = Path(__file__).resolve().parents[1]
        self.runtime_path = root / "runtime.md"
        shutil.copyfile(project / "docs" / "miniloop_runtime.md", self.runtime_path)
        self.workspace = root / "workspace"
        self.workspace.mkdir()
        self.log_path = root / "run.jsonl"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def build(self, backend: ScriptedBackend) -> MiniloopOrchestrator:
        sandbox = DockerSandbox(
            workspace=self.workspace,
            image="not-invoked:test",
            forbidden_host_paths=(self.receiver_path, self.runtime_path),
        )
        return MiniloopOrchestrator(
            run_id="scripted-run",
            model="same-qwen-model",
            backend=backend,
            reviewer_session=LogicalSession(
                role=Role.REVIEWER,
                model="same-qwen-model",
                system_instruction="reviewer system",
            ),
            executor_session=LogicalSession(
                role=Role.EXECUTOR,
                model="same-qwen-model",
                system_instruction="executor system",
            ),
            receiver_reader=ReceiverReader(self.receiver_path),
            reviewer_tools=ReviewerToolbox(
                receiver_setter=ReviewerReceiverSetter(self.receiver_path),
                runtime_updater=RuntimeUpdater(self.runtime_path),
                sandbox=sandbox,
            ),
            executor_tools=ExecutorToolbox(sandbox),
            event_logger=RunEventLogger(path=self.log_path, run_id="scripted-run"),
        )

    def test_round_trip_repair_and_native_handoff(self) -> None:
        initial = "  Initial instruction containing ACCEPT and receiver=human.  \n"
        bad_report = "Self-check PASS, but evidence is bad.\n"
        repair = "REJECT. Repair the exact defect; JSON format is not required.\n"
        fixed_report = "Repair applied. Evidence: /workspace/result.txt\n"
        backend = ScriptedBackend(
            reviewer_results=[
                ChatResult(initial, model="same-qwen-model"),
                ChatResult(repair, model="same-qwen-model"),
                ChatResult(
                    "",
                    tool_calls=(ToolCall("set_receiver", {"receiver": "human"}),),
                    model="same-qwen-model",
                ),
            ],
            executor_results=[ChatResult(bad_report), ChatResult(fixed_report)],
        )
        original_runtime = self.runtime_path.read_text(encoding="utf-8")
        orchestrator = self.build(backend)
        summary = orchestrator.run(reviewer_initial_context="private Static + Runtime")

        self.assertIs(summary.outcome, RunOutcome.HANDED_TO_HUMAN)
        self.assertEqual(summary.peer_turns, 4)
        self.assertEqual(summary.reviewer_inferences, 3)
        self.assertEqual(summary.executor_inferences, 2)
        self.assertIs(ReceiverReader(self.receiver_path).read(), Receiver.HUMAN)
        self.assertEqual(self.runtime_path.read_text(encoding="utf-8"), original_runtime)

        executor_calls = [call for call in backend.calls if call["role"] == "executor"]
        reviewer_calls = [call for call in backend.calls if call["role"] == "reviewer"]
        self.assertEqual(executor_calls[0]["messages"][-1]["content"], initial)
        self.assertEqual(executor_calls[1]["messages"][-1]["content"], repair)
        self.assertNotIn("private Static + Runtime", str(executor_calls))
        self.assertEqual(reviewer_calls[1]["messages"][-1]["content"], bad_report)
        self.assertEqual(reviewer_calls[2]["messages"][-1]["content"], fixed_report)

        events = [json.loads(line) for line in self.log_path.read_text().splitlines()]
        routed = [event for event in events if event["event_type"] == "peer_message_routed"]
        self.assertEqual([event["payload"] for event in routed], [initial, bad_report, repair, fixed_report])
        self.assertEqual(events[-1]["outcome"], "handed_to_human")

    def test_startup_human_state_stops_before_any_inference(self) -> None:
        initialize_receiver(self.receiver_path, Receiver.HUMAN)
        backend = ScriptedBackend([], [])
        summary = self.build(backend).run(reviewer_initial_context="private")
        self.assertIs(summary.outcome, RunOutcome.STARTED_WITH_HUMAN)
        self.assertEqual(backend.calls, [])

    def test_same_model_id_is_enforced(self) -> None:
        backend = ScriptedBackend([], [])
        sandbox = DockerSandbox(
            workspace=self.workspace, image="unused", forbidden_host_paths=()
        )
        with self.assertRaises(ValueError):
            MiniloopOrchestrator(
                run_id="x",
                model="model-a",
                backend=backend,
                reviewer_session=LogicalSession(
                    role=Role.REVIEWER, model="model-a", system_instruction="r"
                ),
                executor_session=LogicalSession(
                    role=Role.EXECUTOR, model="model-b", system_instruction="e"
                ),
                receiver_reader=ReceiverReader(self.receiver_path),
                reviewer_tools=ReviewerToolbox(
                    receiver_setter=ReviewerReceiverSetter(self.receiver_path),
                    runtime_updater=RuntimeUpdater(self.runtime_path),
                    sandbox=sandbox,
                ),
                executor_tools=ExecutorToolbox(sandbox),
                event_logger=RunEventLogger(
                    path=Path(self.temporary.name) / "other.jsonl", run_id="x"
                ),
            )


if __name__ == "__main__":
    unittest.main()
