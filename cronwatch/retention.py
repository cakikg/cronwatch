"""History retention policy: prune old job history entries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List

from cronwatch.history import HistoryEntry, JobHistory


@dataclass
class RetentionPolicy:
    """Defines how long history entries are kept."""

    max_age_days: int = 30
    max_entries_per_job: int = 100

    def is_expired(self, entry: HistoryEntry, now: datetime | None = None) -> bool:
        """Return True if the entry is older than max_age_days."""
        if now is None:
            now = datetime.now(tz=timezone.utc)
        cutoff = now - timedelta(days=self.max_age_days)
        started = entry.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        return started < cutoff


class HistoryPruner:
    """Applies a RetentionPolicy to a JobHistory store."""

    def __init__(self, history: JobHistory, policy: RetentionPolicy) -> None:
        self._history = history
        self._policy = policy

    def prune(self, now: datetime | None = None) -> int:
        """Remove expired / excess entries. Returns number of entries removed."""
        if now is None:
            now = datetime.now(tz=timezone.utc)

        removed = 0
        for job_name in list(self._history.job_names()):
            entries: List[HistoryEntry] = self._history.get(job_name)

            # Filter out age-expired entries
            kept = [e for e in entries if not self._policy.is_expired(e, now)]

            # Enforce max entries (keep most recent)
            if len(kept) > self._policy.max_entries_per_job:
                kept = kept[-self._policy.max_entries_per_job :]

            removed += len(entries) - len(kept)
            self._history.replace(job_name, kept)

        return removed
