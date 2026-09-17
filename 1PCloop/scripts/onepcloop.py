#!/usr/bin/env python3
"""Unified operator CLI for one configured 1PCloop workload."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

import workload_operator as OPERATOR


COMMANDS = (
    "doctor",
    "preflight",
    "run",
    "resume",
    "status",
    "inspect",
    "human-gate",
    "tui",
)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("command", choices=COMMANDS)
    return parser.parse_args(argv)


def _config_failure(command: str) -> int:
    OPERATOR.emit_json(OPERATOR.envelope(
        command,
        None,
        overall="FAIL",
        checks=[{
            "name": "config",
            "status": "FAIL",
            "code": "CONFIG_INVALID",
            "detail": "workload config validation failed",
        }],
    ))
    return 2


def main(argv: Optional[Sequence[str]] = None) -> int:
    selected = parse_args(argv)
    try:
        config = OPERATOR.load_config(selected.config)
    except (OSError, RuntimeError, ValueError):
        return _config_failure(selected.command)

    if selected.command == "doctor":
        result = OPERATOR.doctor(config)
    elif selected.command == "preflight":
        result = OPERATOR.preflight(config)
    elif selected.command == "status":
        result = OPERATOR.status(config)
    elif selected.command == "inspect":
        result = OPERATOR.inspect_run(config)
    elif selected.command == "human-gate":
        result = OPERATOR.human_gate_status(config)
    elif selected.command == "tui":
        import local_tui

        return local_tui.main(local_tui.OperatorDataSource(OPERATOR, config))
    else:
        try:
            exit_code, _run_root = OPERATOR.run_mutation(
                config, resume=selected.command == "resume"
            )
            return exit_code
        except (OSError, RuntimeError, ValueError) as exc:
            try:
                args = (
                    OPERATOR.resume_runner_args(config)
                    if selected.command == "resume"
                    else OPERATOR.build_runner_args(config)
                )
                OPERATOR.RUNNER.emit_final_result(
                    OPERATOR.RUNNER.failure_result_for_main(args, exc)
                )
            except (OSError, RuntimeError, ValueError):
                OPERATOR.RUNNER.emit_final_result({
                    "run_id": "unavailable",
                    "logical_outcome": "PREFLIGHT_FAILED",
                    "exit_code": 1,
                    "runtime_transition": "NOT_APPLIED",
                    "evidence_publication": "NOT_STARTED",
                    "reason": "operator command failed; inspect checkpoint and local evidence",
                    "error_code": "OPERATOR_COMMAND_FAILED",
                    "run_root": str(Path(config.resolved["evidence"]["runs_root"]).resolve()),
                })
            return 1
    OPERATOR.emit_json(result)
    return OPERATOR.exit_code_for(result)


if __name__ == "__main__":
    sys.exit(main())
