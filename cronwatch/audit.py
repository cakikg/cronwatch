"""Audit log: records significant cronwatch events to a append-only file."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional


class AuditEventType(str, Enum):
    JOB_STARTED = "job_started"
    JOB_FINISHED = "job_finished"
    JOB_FAILED = "job_failed"
    JOB_OVERRUN = "job_overrun"
    DAEMON_STARTED = "daemon_started"
    DAEMON_STOPPED = "daemon_stopped"


@dataclass
class AuditEvent:
    event_type: AuditEventType
    job_name: Optional[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type.value,
            "job_name": self.job_name,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


class AuditLog:
    """Appends AuditEvent records as newline-delimited JSON."""

    def __init__(
        self,
        path: Path,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._path = path
        self._clock = clock
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: AuditEvent) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict()) + "\n")

    def read_all(self) -> List[AuditEvent]:
        if not self._path.exists():
            return []
        events: List[AuditEvent] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                events.append(
                    AuditEvent(
                        event_type=AuditEventType(data["event_type"]),
                        job_name=data.get("job_name"),
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        details=data.get("details", {}),
                    )
                )
        return events
