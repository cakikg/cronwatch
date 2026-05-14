"""Persistent history storage for completed job runs."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_FILE = "/var/lib/cronwatch/history.json"
MAX_HISTORY_ENTRIES = 500


@dataclass
class HistoryEntry:
    job_name: str
    started_at: str
    finished_at: str
    exit_code: int
    duration_seconds: float
    timed_out: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(**data)

    def succeeded(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


class JobHistory:
    """Reads and writes job run history to a JSON file."""

    def __init__(self, path: str = DEFAULT_HISTORY_FILE) -> None:
        self._path = Path(path)
        self._entries: List[HistoryEntry] = []
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text())
            self._entries = [HistoryEntry.from_dict(e) for e in raw]
        except (json.JSONDecodeError, TypeError, KeyError):
            self._entries = []

    def record(self, entry: HistoryEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > MAX_HISTORY_ENTRIES:
            self._entries = self._entries[-MAX_HISTORY_ENTRIES:]
        self._persist()

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps([asdict(e) for e in self._entries], indent=2))

    def get_all(self) -> List[HistoryEntry]:
        return list(self._entries)

    def get_for_job(self, job_name: str) -> List[HistoryEntry]:
        return [e for e in self._entries if e.job_name == job_name]

    def last_run(self, job_name: str) -> Optional[HistoryEntry]:
        runs = self.get_for_job(job_name)
        return runs[-1] if runs else None
