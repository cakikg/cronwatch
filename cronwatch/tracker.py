"""Job execution tracker — records start/end times and detects overruns."""

import time
from dataclasses import dataclass, field
from typing import Optional

from cronwatch.config import JobConfig


@dataclass
class JobRun:
    job_name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    exit_code: Optional[int] = None

    @property
    def duration(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return self.end_time - self.start_time

    @property
    def is_complete(self) -> bool:
        return self.end_time is not None

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


class JobTracker:
    """Tracks active and historical job runs."""

    def __init__(self):
        self._active: dict[str, JobRun] = {}
        self._history: list[JobRun] = []

    def start(self, job_name: str) -> JobRun:
        if job_name in self._active:
            raise ValueError(f"Job '{job_name}' is already running.")
        run = JobRun(job_name=job_name)
        self._active[job_name] = run
        return run

    def finish(self, job_name: str, exit_code: int) -> JobRun:
        if job_name not in self._active:
            raise KeyError(f"No active run found for job '{job_name}'.")
        run = self._active.pop(job_name)
        run.end_time = time.time()
        run.exit_code = exit_code
        self._history.append(run)
        return run

    def is_overrun(self, job_name: str, config: JobConfig) -> bool:
        if config.max_duration is None:
            return False
        if job_name not in self._active:
            return False
        elapsed = time.time() - self._active[job_name].start_time
        return elapsed > config.max_duration

    def active_runs(self) -> list[JobRun]:
        return list(self._active.values())

    def history(self) -> list[JobRun]:
        return list(self._history)
