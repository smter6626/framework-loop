"""Small JSON configuration loader with paths anchored to the project directory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class MiniloopConfig:
    project_root: Path
    model: str
    ollama_base_url: str
    ollama_timeout_seconds: float
    docker_image: str
    docker_network_mode: Optional[str]
    docker_timeout_seconds: float
    static_path: Path
    runtime_path: Path
    receiver_path: Path
    workspace_path: Path
    reviewer_instruction_path: Path
    executor_instruction_path: Path


def load_config(path: Path) -> MiniloopConfig:
    document: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    project_root = path.parent.parent.resolve()

    def project_path(key: str) -> Path:
        value = document.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"config field {key} must be a non-empty string")
        return (project_root / value).resolve()

    model = document.get("model")
    if not isinstance(model, str) or not model:
        raise ValueError("config field model must be a non-empty string")
    return MiniloopConfig(
        project_root=project_root,
        model=model,
        ollama_base_url=str(document.get("ollama_base_url", "http://127.0.0.1:11434")),
        ollama_timeout_seconds=float(document.get("ollama_timeout_seconds", 900)),
        docker_image=str(document.get("docker_image", "python:3.12-slim")),
        docker_network_mode=(
            str(document["docker_network_mode"])
            if document.get("docker_network_mode") is not None
            else None
        ),
        docker_timeout_seconds=float(document.get("docker_timeout_seconds", 600)),
        static_path=project_path("static_path"),
        runtime_path=project_path("runtime_path"),
        receiver_path=project_path("receiver_path"),
        workspace_path=project_path("workspace_path"),
        reviewer_instruction_path=project_path("reviewer_instruction_path"),
        executor_instruction_path=project_path("executor_instruction_path"),
    )


def build_reviewer_initial_context(config: MiniloopConfig, kickoff: str) -> str:
    static_text = config.static_path.read_text(encoding="utf-8")
    runtime_text = config.runtime_path.read_text(encoding="utf-8")
    return (
        "Authoritative Static follows.\n\n"
        + static_text
        + "\n\nAuthoritative Runtime follows.\n\n"
        + runtime_text
        + "\n\nHuman kickoff for this run follows.\n\n"
        + kickoff
    )
