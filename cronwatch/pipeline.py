"""Wires runner output to the alert dispatcher after each job execution."""

from datetime import datetime
from typing import List

from cronwatch.alerts import Alert, AlertDispatcher, AlertType
from cronwatch.config import JobConfig
from cronwatch.runner import JobRunner
from cronwatch.tracker import JobRun, JobTracker


def _build_alert(run: JobRun, job: JobConfig) -> Alert:
    if not run.succeeded():
        return Alert(
            alert_type=AlertType.FAILURE,
            job_name=run.job_name,
            run=run,
            message=f"Job '{run.job_name}' failed with exit code {run.exit_code}.",
        )
    if job.max_duration and run.duration() is not None and run.duration() > job.max_duration:
        return Alert(
            alert_type=AlertType.OVERRUN,
            job_name=run.job_name,
            run=run,
            message=(
                f"Job '{run.job_name}' exceeded max duration "
                f"({run.duration():.1f}s > {job.max_duration}s)."
            ),
        )
    return None


class ExecutionPipeline:
    """Runs a job and fires alerts based on the outcome."""

    def __init__(
        self,
        runner: JobRunner,
        tracker: JobTracker,
        dispatcher: AlertDispatcher,
        jobs: List[JobConfig],
    ) -> None:
        self._runner = runner
        self._tracker = tracker
        self._dispatcher = dispatcher
        self._job_map = {j.name: j for j in jobs}

    def execute(self, job: JobConfig) -> int:
        """Run *job*, evaluate the result, dispatch alerts if needed."""
        exit_code = self._runner.run(job)
        history = self._tracker.history(job.name)
        if not history:
            return exit_code
        last_run: JobRun = history[-1]
        alert = _build_alert(last_run, job)
        if alert is not None:
            self._dispatcher.dispatch(alert)
        return exit_code
