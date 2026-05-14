"""Generates periodic health reports from job history and summary data."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from cronwatch.summary import CronwatchSummary, JobSummary


@dataclass
class ReportLine:
    job_name: str
    success_rate: float
    total_runs: int
    last_run: Optional[datetime]
    last_status: Optional[str]

    def status_symbol(self) -> str:
        if self.success_rate >= 1.0:
            return "✓"
        if self.success_rate == 0.0:
            return "✗"
        return "~"


class ReportBuilder:
    """Builds a human-readable report from a CronwatchSummary."""

    def build(self, summary: CronwatchSummary) -> str:
        lines = self._header()
        for job_summary in summary.jobs:
            lines.append(self._format_job(job_summary))
        lines.append(self._footer(summary))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def _header(self) -> list[str]:
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        return [
            "=" * 60,
            f"  CronWatch Health Report  —  {ts}",
            "=" * 60,
            f"  {'JOB':<30} {'RATE':>6}  {'RUNS':>5}  {'LAST RUN':<20}  ST",
            "-" * 60,
        ]

    def _format_job(self, job: JobSummary) -> str:
        rate_pct = f"{job.success_rate * 100:.0f}%"
        runs = str(job.total_runs)
        last = (
            job.last_run.strftime("%Y-%m-%d %H:%M") if job.last_run else "never"
        )
        symbol = "✓" if job.success_rate >= 1.0 else ("✗" if job.success_rate == 0.0 else "~")
        return f"  {job.name:<30} {rate_pct:>6}  {runs:>5}  {last:<20}  {symbol}"

    def _footer(self, summary: CronwatchSummary) -> str:
        return textwrap.dedent(f"""\
            {'-' * 60}
              Total jobs : {summary.total_jobs}
              Healthy    : {summary.healthy_jobs}
              Degraded   : {summary.total_jobs - summary.healthy_jobs}
            {'=' * 60}"""
        )
