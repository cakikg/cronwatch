"""Generates periodic summary reports of cron job execution history."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from cronwatch.history import JobHistory
from cronwatch.history_recorder import HistoryRecorder


@dataclass
class JobSummary:
    job_name: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    avg_duration_seconds: Optional[float]
    last_run_at: Optional[datetime]
    last_exit_code: Optional[int]

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs * 100.0


@dataclass
class CronwatchSummary:
    generated_at: datetime
    jobs: List[JobSummary]

    @property
    def total_jobs(self) -> int:
        return len(self.jobs)

    @property
    def healthy_jobs(self) -> int:
        return sum(1 for j in self.jobs if j.last_exit_code == 0)


class SummaryBuilder:
    def __init__(self, recorder: HistoryRecorder) -> None:
        self._recorder = recorder

    def build(self, job_names: List[str]) -> CronwatchSummary:
        job_summaries = [self._summarise_job(name) for name in job_names]
        return CronwatchSummary(
            generated_at=datetime.utcnow(),
            jobs=job_summaries,
        )

    def _summarise_job(self, job_name: str) -> JobSummary:
        history: JobHistory = self._recorder.get_for_job(job_name)
        entries = history.all()

        total = len(entries)
        successful = sum(1 for e in entries if e.succeeded)
        failed = total - successful

        durations = [
            e.duration_seconds
            for e in entries
            if e.duration_seconds is not None
        ]
        avg_duration = sum(durations) / len(durations) if durations else None

        last = history.last()
        return JobSummary(
            job_name=job_name,
            total_runs=total,
            successful_runs=successful,
            failed_runs=failed,
            avg_duration_seconds=avg_duration,
            last_run_at=last.finished_at if last else None,
            last_exit_code=last.exit_code if last else None,
        )
