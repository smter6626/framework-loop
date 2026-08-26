"""Docker-backed Linux shell with an explicit single-workspace mount."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


class SandboxConfigurationError(ValueError):
    pass


class SandboxExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class SandboxResult:
    argv: Sequence[str]
    returncode: int
    stdout: str
    stderr: str


def _is_within(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


class DockerSandbox:
    """Runs `/bin/sh -lc` without parsing or blacklisting the shell command."""

    def __init__(
        self,
        *,
        workspace: Path,
        image: str,
        forbidden_host_paths: Iterable[Path],
        network_mode: Optional[str] = None,
        docker_binary: str = "docker",
        timeout_seconds: float = 600.0,
    ) -> None:
        if not image:
            raise SandboxConfigurationError("container image must not be empty")
        try:
            resolved_workspace = workspace.resolve(strict=True)
        except FileNotFoundError as exc:
            raise SandboxConfigurationError(f"workspace does not exist: {workspace}") from exc
        if not resolved_workspace.is_dir():
            raise SandboxConfigurationError("workspace must be a directory")

        for raw_path in forbidden_host_paths:
            forbidden = raw_path.resolve(strict=False)
            if _is_within(forbidden, resolved_workspace):
                raise SandboxConfigurationError(
                    f"forbidden governance/control path would be mounted: {forbidden}"
                )

        self.workspace = resolved_workspace
        self.image = image
        self.docker_binary = docker_binary
        self.timeout_seconds = timeout_seconds
        self.network_mode = network_mode

    def build_command(self, command: str, *, read_only_workspace: bool = False) -> List[str]:
        if not isinstance(command, str):
            raise TypeError("shell command must be a string")
        mount = (
            f"type=bind,source={self.workspace},target=/workspace"
            + (",readonly" if read_only_workspace else "")
        )
        argv = [
            self.docker_binary,
            "run",
            "--rm",
            "--pull=never",
            "--init",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
        ]
        if self.network_mode is not None:
            argv.append(f"--network={self.network_mode}")
        argv.extend(
            [
                "--mount",
                mount,
                "--tmpfs",
                "/tmp:rw,nosuid,nodev,size=256m",
                "--workdir",
                "/workspace",
                "--env",
                "PYTHONDONTWRITEBYTECODE=1",
                self.image,
                "/bin/sh",
                "-lc",
                command,
            ]
        )
        return argv

    def run(self, command: str, *, read_only_workspace: bool = False) -> SandboxResult:
        if self.network_mode is None:
            raise SandboxConfigurationError(
                "Executor network policy is unresolved; configure network_mode before execution"
            )
        argv = self.build_command(command, read_only_workspace=read_only_workspace)
        try:
            completed = subprocess.run(
                argv,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise SandboxExecutionError(
                f"Docker executable not found: {self.docker_binary}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise SandboxExecutionError(
                f"sandbox command exceeded {self.timeout_seconds} seconds"
            ) from exc
        return SandboxResult(argv, completed.returncode, completed.stdout, completed.stderr)
