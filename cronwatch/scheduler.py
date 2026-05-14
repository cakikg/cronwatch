"""Cron expression parser and next-run scheduler for cronwatch."""

from __future__ import annotations

from croniter import croniter
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from cronwatch.config import JobConfig


@dataclass
class ScheduleEntry:
    """Represents a scheduled job with its next expected run time."""

    job: JobConfig
    next_run: datetime
    last_checked: datetime

    def is_due(self, now: Optional[datetime] = None) -> bool:
        """Return True if the job is due to run at or before *now*."""
        if now is None:
            now = datetime.now(tz=timezone.utc)
        return now >= self.next_run

    def advance(self) -> None:
        """Move next_run forward to the following scheduled occurrence."""
        base = self.next_run
        cron = croniter(self.job.schedule, base)
        self.next_run = cron.get_next(datetime).replace(tzinfo=timezone.utc)
        self.last_checked = datetime.now(tz=timezone.utc)


class Scheduler:
    """Maintains schedule entries for all configured jobs."""

    def __init__(self) -> None:
        self._entries: dict[str, ScheduleEntry] = {}

    def register(self, job: JobConfig, reference: Optional[datetime] = None) -> None:
        """Register a job and compute its first upcoming run time."""
        if reference is None:
            reference = datetime.now(tz=timezone.utc)
        cron = croniter(job.schedule, reference)
        next_run = cron.get_next(datetime).replace(tzinfo=timezone.utc)
        self._entries[job.name] = ScheduleEntry(
            job=job,
            next_run=next_run,
            last_checked=reference,
        )

    def due_jobs(self, now: Optional[datetime] = None) -> list[ScheduleEntry]:
        """Return all entries whose next_run is at or before *now*."""
        if now is None:
            now = datetime.now(tz=timezone.utc)
        return [e for e in self._entries.values() if e.is_due(now)]

    def get_entry(self, job_name: str) -> Optional[ScheduleEntry]:
        return self._entries.get(job_name)

    def __len__(self) -> int:
        return len(self._entries)
