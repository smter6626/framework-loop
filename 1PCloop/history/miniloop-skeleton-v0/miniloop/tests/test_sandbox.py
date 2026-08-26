from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from miniloop.sandbox import DockerSandbox, SandboxConfigurationError


class SandboxTests(unittest.TestCase):
    def test_only_authorized_workspace_is_mounted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            static = root / "docs" / "static.md"
            static.parent.mkdir()
            static.write_text("governance", encoding="utf-8")
            command = "git status && rm -f generated.tmp"
            sandbox = DockerSandbox(
                workspace=workspace,
                image="python:test",
                forbidden_host_paths=(static,),
            )
            argv = sandbox.build_command(command)
            mounts = [value for value in argv if value.startswith("type=bind")]
            self.assertEqual(len(mounts), 1)
            self.assertIn(str(workspace.resolve()), mounts[0])
            self.assertNotIn(str(static), " ".join(argv))
            self.assertEqual(argv[-1], command)
            self.assertIn("--pull=never", argv)
            self.assertNotIn("readonly", mounts[0])

    def test_reviewer_workspace_mount_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            workspace.mkdir()
            sandbox = DockerSandbox(
                workspace=workspace, image="python:test", forbidden_host_paths=()
            )
            argv = sandbox.build_command("python -m unittest", read_only_workspace=True)
            mount = next(value for value in argv if value.startswith("type=bind"))
            self.assertTrue(mount.endswith(",readonly"))

    def test_configuration_rejects_governance_inside_mount(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            workspace.mkdir()
            forbidden = workspace / "runtime.md"
            forbidden.write_text("authority", encoding="utf-8")
            with self.assertRaises(SandboxConfigurationError):
                DockerSandbox(
                    workspace=workspace,
                    image="python:test",
                    forbidden_host_paths=(forbidden,),
                )

    def test_execution_refuses_unresolved_network_policy_before_docker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            workspace.mkdir()
            sandbox = DockerSandbox(
                workspace=workspace,
                image="python:test",
                forbidden_host_paths=(),
                network_mode=None,
            )
            with self.assertRaisesRegex(SandboxConfigurationError, "network policy"):
                sandbox.run("true")

    def test_explicit_network_policy_is_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            workspace.mkdir()
            sandbox = DockerSandbox(
                workspace=workspace,
                image="python:test",
                forbidden_host_paths=(),
                network_mode="none",
            )
            self.assertIn("--network=none", sandbox.build_command("true"))


if __name__ == "__main__":
    unittest.main()
