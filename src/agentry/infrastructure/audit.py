"""Append-only JSONL audit sink: one JSON line per run event."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from agentry.core.models import RunEvent


class JsonlAuditSink:
    """Writes each :class:`RunEvent` as a single JSON line, tagged with its event type."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: RunEvent) -> None:
        record = {"event_type": type(event).__name__, **asdict(event)}
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
