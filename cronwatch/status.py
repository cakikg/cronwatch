"""Provides a live status snapshot of all tracked cron jobs."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from cronwatch.tracker import JobTracker
from cronwatch.history_recorder import HistoryRecorder
from cronwatch.scheduler import Scheduler


@dataclass
class JobStatus:
    name: str
    last_run: Optional[datetime]
    last_exit_code: Optional[int]
    next_run: Optional[datetime]
    is_running: bool

    @property
    def is_healthy(self) -> bool:
        if self.last_exit_code is None:
            return True
        return self.last_exit_code == 0

    @property
    def status_label(self) -> str:
        if self.is_running:
            return "running"
        if self.last_exit_code is None:
            return "pending"
        return "ok" if self.is_healthy else "failed"


@dataclass
class StatusSnapshot:
    captured_at: datetime
    jobs: List[JobStatus]

    @property
    def healthy_count(self) -> int:
        return sum(1 for j in self.jobs if j.is_healthy and not j.is_running)

    @property
    def failed_count(self) -> int:
        return sum(1 for j in self.jobs if not j.is_healthy)

    @property
    def running_count(self) -> int:
        return sum(1 for j in self.jobs if j.is_running)


class StatusBuilder:
    def __init__(
        self,
        tracker: JobTracker,
        recorder: HistoryRecorder,
        scheduler: Scheduler,
    ) -> None:
        self._tracker = tracker
        self._recorder = recorder
        self._scheduler = scheduler

    def build(self) -> StatusSnapshot:
        jobs: List[JobStatus] = []
        active_names = {run.job_name for run in self._tracker.active_runs()}

        for name, entry in self._scheduler.entries():
            last = self._recorder.last_run(name)
            jobs.append(
                JobStatus(
                    name=name,
                    last_run=last.finished_at if last else None,
                    last_exit_code=last.exit_code if last else None,
                    next_run=entry.next_run,
                    is_running=name in active_names,
                )
            )

        return StatusSnapshot(captured_at=datetime.utcnow(), jobs=jobs)
