"""Persistent two-value receiver control plane."""

from __future__ import annotations

import os
import tempfile
from enum import Enum
from pathlib import Path


class Receiver(str, Enum):
    EXECUTOR = "executor"
    HUMAN = "human"


class InvalidReceiverState(ValueError):
    pass


def _validated(value: str) -> Receiver:
    try:
        return Receiver(value)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in Receiver)
        raise InvalidReceiverState(f"receiver must be one of: {allowed}") from exc


def _atomic_write(path: Path, receiver: Receiver) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".receiver-", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(receiver.value + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def initialize_receiver(path: Path, initial: Receiver = Receiver.EXECUTOR) -> None:
    """Administrative bootstrap; not exposed as an Agent tool."""

    _atomic_write(path, initial)


class ReceiverReader:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> Receiver:
        try:
            raw = self.path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise InvalidReceiverState(f"receiver file does not exist: {self.path}") from exc
        return _validated(raw.strip())


class ReviewerReceiverSetter:
    """Narrow capability instantiated only in the Reviewer toolbox."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def set_receiver(self, value: str) -> Receiver:
        receiver = _validated(value)
        _atomic_write(self._path, receiver)
        return receiver
