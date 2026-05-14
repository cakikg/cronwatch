"""Job run tracking: records start/finish times and exit codes for cron jobs."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class JobRun:
    job_name: str
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None
    exit_code: Optional[int] = None

    def duration(self) -> float:
        """Return elapsed seconds; uses now if the job is still running."""
        end = self.finished_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()

    def is_complete(self) -> bool:
        return self.finished_at is not None

    def succeeded(self) -> bool:
        return self.is_complete() and self.exit_code == 0


class JobTracker:
    """Thread-safe store for active and historical job runs."""

    def __init__(self) -> None:
        self._active: dict[str, JobRun] = {}
        self._history: list[JobRun] = []
        self._unalerted: list[JobRun] = []

    def start(self, job_name: str) -> JobRun:
        run = JobRun(job_name=job_name)
        self._active[run.run_id] = run
        return run

    def finish(self, run_id: str, exit_code: int) -> Optional[JobRun]:
        run = self._active.pop(run_id, None)
        if run is None:
            return None
        run.finished_at = datetime.now(timezone.utc)
        run.exit_code = exit_code
        self._history.append(run)
        self._unalerted.append(run)
        return run

    def active_runs(self) -> list[JobRun]:
        return list(self._active.values())

    def history(self) -> list[JobRun]:
        return list(self._history)

    def drain_unalerted(self) -> list[JobRun]:
        """Return and clear the list of completed-but-not-yet-alerted runs."""
        runs, self._unalerted = self._unalerted, []
        return runs

    def get_run(self, run_id: str) -> Optional[JobRun]:
        return self._active.get(run_id) or next(
            (r for r in self._history if r.run_id == run_id), None
        )
