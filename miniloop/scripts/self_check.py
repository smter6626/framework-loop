#!/usr/bin/env python3
"""Run repository checks and persist exact command output as JSON evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    repository = project.parent
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(project / "src")
    commands: List[List[str]] = [
        [sys.executable, "-m", "compileall", "-q", "miniloop/src", "miniloop/scripts", "miniloop/tests"],
        [sys.executable, "-m", "unittest", "discover", "-s", "miniloop/tests", "-v"],
        ["git", "diff", "--check"],
        [
            "git",
            "diff",
            "--",
            "miniloop/docs/miniloop_static.md",
            "miniloop/docs/miniloop_runtime.md",
        ],
    ]
    results: List[Dict[str, Any]] = []
    passed = True
    for argv in commands:
        completed = subprocess.run(
            argv,
            cwd=repository,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        results.append(
            {
                "argv": argv,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
        passed = passed and completed.returncode == 0

    hashes = {}
    for name in ("miniloop_static.md", "miniloop_runtime.md"):
        raw = (project / "docs" / name).read_bytes()
        hashes[name] = hashlib.sha256(raw).hexdigest()
    document = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "passed": passed,
        "authoritative_document_sha256": hashes,
        "commands": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"passed": passed, "output": str(args.output.resolve())}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
