from __future__ import annotations

import unittest

from miniloop.envelope import MessageEnvelope, Role
from miniloop.session import LogicalSession


class TransportTests(unittest.TestCase):
    def test_payload_is_received_verbatim(self) -> None:
        payload = "  REJECT?\n```json\n{not stable}\n```\n接受 ✅  \n"
        envelope = MessageEnvelope.create(
            run_id="run-1",
            sender=Role.REVIEWER,
            receiver=Role.EXECUTOR,
            turn=1,
            payload=payload,
        )
        session = LogicalSession(
            role=Role.EXECUTOR, model="same-model", system_instruction="executor-only"
        )
        session.receive_peer(envelope)

        self.assertEqual(session.messages[-1]["content"], payload)
        self.assertEqual(envelope.payload, payload)
        self.assertEqual(len(envelope.payload_sha256), 64)

    def test_logical_histories_are_independent(self) -> None:
        reviewer = LogicalSession(
            role=Role.REVIEWER, model="same-model", system_instruction="reviewer-secret"
        )
        executor = LogicalSession(
            role=Role.EXECUTOR, model="same-model", system_instruction="executor-secret"
        )
        reviewer.add_local_context("Static and Runtime private context")
        envelope = MessageEnvelope.create(
            run_id="run-1",
            sender=Role.REVIEWER,
            receiver=Role.EXECUTOR,
            turn=1,
            payload="bounded peer instruction",
        )
        executor.receive_peer(envelope)

        self.assertNotIn("Static and Runtime private context", str(executor.messages))
        self.assertNotIn("reviewer-secret", str(executor.messages))
        self.assertNotIn("executor-secret", str(reviewer.messages))

    def test_envelope_identity_is_deterministic(self) -> None:
        fields = dict(
            run_id="repeatable",
            sender=Role.EXECUTOR,
            receiver=Role.REVIEWER,
            turn=9,
            payload="same bytes",
        )
        self.assertEqual(
            MessageEnvelope.create(**fields).message_id,
            MessageEnvelope.create(**fields).message_id,
        )


if __name__ == "__main__":
    unittest.main()
