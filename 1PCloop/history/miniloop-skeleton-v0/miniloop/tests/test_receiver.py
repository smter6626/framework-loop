from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from miniloop.inference import ToolCall
from miniloop.receiver import (
    InvalidReceiverState,
    Receiver,
    ReceiverReader,
    ReviewerReceiverSetter,
    initialize_receiver,
)
from miniloop.sandbox import DockerSandbox
from miniloop.toolbox import ExecutorToolbox, ToolExecutionError


class ReceiverTests(unittest.TestCase):
    def test_only_two_persistent_values_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "receiver"
            initialize_receiver(path)
            reader = ReceiverReader(path)
            setter = ReviewerReceiverSetter(path)
            self.assertIs(reader.read(), Receiver.EXECUTOR)
            setter.set_receiver("human")
            self.assertIs(reader.read(), Receiver.HUMAN)
            with self.assertRaises(InvalidReceiverState):
                setter.set_receiver("reviewer")

    def test_invalid_file_content_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "receiver"
            path.write_text("executor\nhuman\n", encoding="utf-8")
            with self.assertRaises(InvalidReceiverState):
                ReceiverReader(path).read()

    def test_executor_toolbox_has_no_receiver_setter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            workspace.mkdir()
            sandbox = DockerSandbox(
                workspace=workspace,
                image="unused:test",
                forbidden_host_paths=(),
            )
            toolbox = ExecutorToolbox(sandbox)
            names = [item["function"]["name"] for item in toolbox.definitions]
            self.assertEqual(names, ["run_shell"])
            with self.assertRaises(ToolExecutionError):
                toolbox.execute(ToolCall("set_receiver", {"receiver": "human"}))


if __name__ == "__main__":
    unittest.main()
