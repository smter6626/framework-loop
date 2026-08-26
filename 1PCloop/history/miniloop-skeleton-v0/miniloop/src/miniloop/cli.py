"""Command-line entry point for the first Miniloop skeleton."""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

from .config import MiniloopConfig, build_reviewer_initial_context, load_config
from .eventlog import RunEventLogger
from .ollama import OllamaClient
from .orchestrator import MiniloopOrchestrator
from .receiver import ReceiverReader, ReviewerReceiverSetter
from .runtime_updater import RuntimeUpdater
from .sandbox import DockerSandbox
from .session import LogicalSession
from .envelope import Role
from .toolbox import ExecutorToolbox, ReviewerToolbox


def _default_config() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "miniloop.json"


def _sandbox(config: MiniloopConfig) -> DockerSandbox:
    return DockerSandbox(
        workspace=config.workspace_path,
        image=config.docker_image,
        network_mode=config.docker_network_mode,
        timeout_seconds=config.docker_timeout_seconds,
        forbidden_host_paths=(
            config.static_path,
            config.runtime_path,
            config.receiver_path,
        ),
    )


def _run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    run_id = args.run_id or (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid.uuid4().hex[:8]
    )
    log_path = config.project_root / "logs" / f"{run_id}.jsonl"
    sandbox = _sandbox(config)
    reviewer = LogicalSession(
        role=Role.REVIEWER,
        model=config.model,
        system_instruction=config.reviewer_instruction_path.read_text(encoding="utf-8"),
    )
    executor = LogicalSession(
        role=Role.EXECUTOR,
        model=config.model,
        system_instruction=config.executor_instruction_path.read_text(encoding="utf-8"),
    )
    orchestrator = MiniloopOrchestrator(
        run_id=run_id,
        model=config.model,
        backend=OllamaClient(
            base_url=config.ollama_base_url,
            timeout_seconds=config.ollama_timeout_seconds,
        ),
        reviewer_session=reviewer,
        executor_session=executor,
        receiver_reader=ReceiverReader(config.receiver_path),
        reviewer_tools=ReviewerToolbox(
            receiver_setter=ReviewerReceiverSetter(config.receiver_path),
            runtime_updater=RuntimeUpdater(config.runtime_path),
            sandbox=sandbox,
        ),
        executor_tools=ExecutorToolbox(sandbox),
        event_logger=RunEventLogger(path=log_path, run_id=run_id),
    )
    summary = orchestrator.run(
        reviewer_initial_context=build_reviewer_initial_context(config, args.kickoff)
    )
    print(json.dumps({**summary.__dict__, "outcome": summary.outcome.value, "log": str(log_path)}))
    return 0


def _show_sandbox_command(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    command = _sandbox(config).build_command(
        args.command, read_only_workspace=args.reviewer
    )
    print(json.dumps(command, ensure_ascii=False, indent=2))
    return 0


def _show_receiver(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    print(ReceiverReader(config.receiver_path).read().value)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Miniloop deterministic orchestrator")
    parser.add_argument("--config", type=Path, default=_default_config())
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    run = subparsers.add_parser("run", help="Run the live local Ollama loop")
    run.add_argument("--run-id")
    run.add_argument("--kickoff", required=True)
    run.set_defaults(handler=_run)

    receiver = subparsers.add_parser("show-receiver", help="Read receiver state")
    receiver.set_defaults(handler=_show_receiver)

    sandbox = subparsers.add_parser(
        "show-sandbox-command", help="Print the exact Docker argv without executing it"
    )
    sandbox.add_argument("--reviewer", action="store_true")
    sandbox.add_argument("command")
    sandbox.set_defaults(handler=_show_sandbox_command)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
