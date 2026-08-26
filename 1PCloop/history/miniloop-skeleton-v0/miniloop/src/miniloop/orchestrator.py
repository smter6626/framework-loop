"""Serial Reviewer -> Executor -> Reviewer deterministic event loop."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Sequence

from .envelope import MessageEnvelope, Role
from .eventlog import RunEventLogger
from .inference import ChatResult, InferenceBackend, ToolCall
from .receiver import Receiver, ReceiverReader
from .session import LogicalSession
from .toolbox import ExecutorToolbox, ReviewerToolbox, ToolExecutionError


class RunOutcome(str, Enum):
    HANDED_TO_HUMAN = "handed_to_human"
    STARTED_WITH_HUMAN = "started_with_human"


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    outcome: RunOutcome
    peer_turns: int
    reviewer_inferences: int
    executor_inferences: int


class MiniloopOrchestrator:
    def __init__(
        self,
        *,
        run_id: str,
        model: str,
        backend: InferenceBackend,
        reviewer_session: LogicalSession,
        executor_session: LogicalSession,
        receiver_reader: ReceiverReader,
        reviewer_tools: ReviewerToolbox,
        executor_tools: ExecutorToolbox,
        event_logger: RunEventLogger,
    ) -> None:
        if reviewer_session.role is not Role.REVIEWER:
            raise ValueError("reviewer_session has the wrong role")
        if executor_session.role is not Role.EXECUTOR:
            raise ValueError("executor_session has the wrong role")
        if reviewer_session.model != model or executor_session.model != model:
            raise ValueError("both logical sessions must use the same model ID")
        self.run_id = run_id
        self.model = model
        self.backend = backend
        self.reviewer = reviewer_session
        self.executor = executor_session
        self.receiver = receiver_reader
        self.reviewer_tools = reviewer_tools
        self.executor_tools = executor_tools
        self.events = event_logger
        self._peer_turn = 0
        self._reviewer_inferences = 0
        self._executor_inferences = 0

    def run(self, *, reviewer_initial_context: str) -> RunSummary:
        self.reviewer.add_local_context(reviewer_initial_context)
        startup_receiver = self.receiver.read()
        self.events.record(
            "run_started",
            model=self.model,
            receiver=startup_receiver.value,
            reviewer_session="reviewer_messages",
            executor_session="executor_messages",
        )
        if startup_receiver is Receiver.HUMAN:
            return self._finish(RunOutcome.STARTED_WITH_HUMAN)

        while True:
            reviewer_result = self._infer_reviewer()

            # The control file is re-read after every blocking Reviewer inference.
            receiver_after_inference = self.receiver.read()
            self.events.record(
                "receiver_read",
                after="reviewer_inference",
                receiver=receiver_after_inference.value,
            )
            if receiver_after_inference is Receiver.HUMAN:
                return self._finish(RunOutcome.HANDED_TO_HUMAN)

            if reviewer_result.tool_calls:
                self._execute_tools(
                    role=Role.REVIEWER,
                    result=reviewer_result,
                    toolbox=self.reviewer_tools,
                    session=self.reviewer,
                )
                receiver_after_tools = self.receiver.read()
                self.events.record(
                    "receiver_read",
                    after="reviewer_tools",
                    receiver=receiver_after_tools.value,
                )
                if receiver_after_tools is Receiver.HUMAN:
                    return self._finish(RunOutcome.HANDED_TO_HUMAN)
                # Native tool results go back only to the same isolated session.
                continue

            reviewer_envelope = self._route(
                sender=Role.REVIEWER,
                receiver=Role.EXECUTOR,
                payload=reviewer_result.content,
            )
            self.executor.receive_peer(reviewer_envelope)

            executor_result = self._infer_executor_until_payload()
            executor_envelope = self._route(
                sender=Role.EXECUTOR,
                receiver=Role.REVIEWER,
                payload=executor_result.content,
            )
            self.reviewer.receive_peer(executor_envelope)

    def _infer_reviewer(self) -> ChatResult:
        result = self.backend.chat(
            model=self.model,
            messages=self.reviewer.messages,
            tools=self.reviewer_tools.definitions,
        )
        self._reviewer_inferences += 1
        self.reviewer.record_assistant(result)
        self._log_inference(Role.REVIEWER, result, self._reviewer_inferences)
        return result

    def _infer_executor_until_payload(self) -> ChatResult:
        while True:
            result = self.backend.chat(
                model=self.model,
                messages=self.executor.messages,
                tools=self.executor_tools.definitions,
            )
            self._executor_inferences += 1
            self.executor.record_assistant(result)
            self._log_inference(Role.EXECUTOR, result, self._executor_inferences)
            if not result.tool_calls:
                return result
            self._execute_tools(
                role=Role.EXECUTOR,
                result=result,
                toolbox=self.executor_tools,
                session=self.executor,
            )

    def _execute_tools(
        self, *, role: Role, result: ChatResult, toolbox: Any, session: LogicalSession
    ) -> None:
        for call in result.tool_calls:
            try:
                tool_result = toolbox.execute(call)
                ok = True
            except (ToolExecutionError, ValueError, RuntimeError, OSError) as exc:
                tool_result = json.dumps(
                    {"ok": False, "error_type": type(exc).__name__, "error": str(exc)},
                    ensure_ascii=False,
                )
                ok = False
            session.record_tool_result(name=call.name, content=tool_result)
            self.events.record(
                "tool_result",
                role=role.value,
                tool=call.name,
                ok=ok,
                result=tool_result,
            )

    def _route(self, *, sender: Role, receiver: Role, payload: str) -> MessageEnvelope:
        self._peer_turn += 1
        envelope = MessageEnvelope.create(
            run_id=self.run_id,
            sender=sender,
            receiver=receiver,
            turn=self._peer_turn,
            payload=payload,
        )
        self.events.record("peer_message_routed", **envelope.as_dict())
        return envelope

    def _log_inference(self, role: Role, result: ChatResult, role_turn: int) -> None:
        calls: Sequence[Dict[str, Any]] = tuple(
            {"name": call.name, "arguments": dict(call.arguments)}
            for call in result.tool_calls
        )
        self.events.record(
            "inference_completed",
            role=role.value,
            role_turn=role_turn,
            response_model=result.model,
            done_reason=result.done_reason,
            content=result.content,
            tool_calls=calls,
        )

    def _finish(self, outcome: RunOutcome) -> RunSummary:
        summary = RunSummary(
            run_id=self.run_id,
            outcome=outcome,
            peer_turns=self._peer_turn,
            reviewer_inferences=self._reviewer_inferences,
            executor_inferences=self._executor_inferences,
        )
        self.events.record(
            "run_stopped",
            outcome=outcome.value,
            peer_turns=summary.peer_turns,
            reviewer_inferences=summary.reviewer_inferences,
            executor_inferences=summary.executor_inferences,
        )
        return summary
