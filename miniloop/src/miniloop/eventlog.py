"""Append-only JSONL run/event evidence."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RunEventLogger:
    def __init__(self, *, path: Path, run_id: str) -> None:
        if not run_id:
            raise ValueError("run_id must not be empty")
        self.path = path
        self.run_id = run_id
        self._event_index = 0
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        # Refuse accidental mixing of independent runs in one evidence file.
        with path.open("x", encoding="utf-8"):
            pass

    def record(self, event_type: str, **fields: Any) -> None:
        if not event_type:
            raise ValueError("event_type must not be empty")
        with self._lock:
            self._event_index += 1
            event = {
                "event_index": self._event_index,
                "event_type": event_type,
                "run_id": self.run_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }
            event.update(fields)
            encoded = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(encoded + "\n")
