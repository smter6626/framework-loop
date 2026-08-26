"""Deterministic transport metadata around opaque peer payloads."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class Role(str, Enum):
    REVIEWER = "reviewer"
    EXECUTOR = "executor"


@dataclass(frozen=True)
class MessageEnvelope:
    """Python-owned routing fields plus an untouched natural-language payload."""

    message_id: str
    run_id: str
    sender: Role
    receiver: Role
    turn: int
    payload: str

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        sender: Role,
        receiver: Role,
        turn: int,
        payload: str,
    ) -> "MessageEnvelope":
        if not run_id:
            raise ValueError("run_id must not be empty")
        if sender == receiver:
            raise ValueError("sender and receiver must differ")
        if turn < 1:
            raise ValueError("turn must be positive")
        if not isinstance(payload, str):
            raise TypeError("payload must be a string")

        identity = json.dumps(
            {
                "payload": payload,
                "receiver": receiver.value,
                "run_id": run_id,
                "sender": sender.value,
                "turn": turn,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        message_id = hashlib.sha256(identity).hexdigest()
        return cls(message_id, run_id, sender, receiver, turn, payload)

    @property
    def payload_sha256(self) -> str:
        return hashlib.sha256(self.payload.encode("utf-8")).hexdigest()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "run_id": self.run_id,
            "sender": self.sender.value,
            "receiver": self.receiver.value,
            "turn": self.turn,
            "payload": self.payload,
            "payload_sha256": self.payload_sha256,
        }
