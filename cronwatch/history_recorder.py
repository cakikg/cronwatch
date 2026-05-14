"""Bridges JobTracker finished runs into JobHistory storage."""

from __future__ import annotations

from cronwatch.history import HistoryEntry, JobHistory
from cronwatch.tracker import JobRun


class HistoryRecorder:
    """Converts a completed JobRun into a HistoryEntry and persists it."""

    def __init__(self, history: JobHistory) -> None:
        self._history = history

    def record(self, run: JobRun) -> None:
        if not run.is_complete():
            raise ValueError(f"Cannot record incomplete run for job '{run.job_name}'")

        entry = HistoryEntry(
            job_name=run.job_name,
            started_at=run.started_at.isoformat(),
            finished_at=run.finished_at.isoformat(),  # type: ignore[union-attr]
            exit_code=run.exit_code if run.exit_code is not None else -1,
            duration_seconds=run.duration().total_seconds(),
            timed_out=run.timed_out,
        )
        self._history.record(entry)

    def last_run(self, job_name: str):
        return self._history.last_run(job_name)

    def get_for_job(self, job_name: str):
        return self._history.get_for_job(job_name)
