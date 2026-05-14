"""Monitor module: watches running jobs and triggers alerts on failures or overruns."""

import time
import logging
from datetime import datetime, timezone
from threading import Thread, Event

from cronwatch.tracker import JobTracker, JobRun
from cronwatch.alerts import AlertDispatcher, Alert, AlertType
from cronwatch.config import CronwatchConfig

logger = logging.getLogger(__name__)


class CronMonitor:
    """Periodically checks active job runs and dispatches alerts as needed."""

    def __init__(
        self,
        config: CronwatchConfig,
        tracker: JobTracker,
        dispatcher: AlertDispatcher,
        poll_interval: float = 5.0,
    ):
        self.config = config
        self.tracker = tracker
        self.dispatcher = dispatcher
        self.poll_interval = poll_interval
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._overrun_alerted: set[str] = set()

    def start(self) -> None:
        """Start the background monitoring thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Monitor is already running.")
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run_loop, daemon=True, name="cronwatch-monitor")
        self._thread.start()
        logger.info("CronMonitor started (poll_interval=%.1fs).", self.poll_interval)

    def stop(self, timeout: float = 10.0) -> None:
        """Signal the monitoring thread to stop and wait for it to finish."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        logger.info("CronMonitor stopped.")

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self._check_active_runs()
            self._check_completed_runs()
            self._stop_event.wait(self.poll_interval)

    def _check_active_runs(self) -> None:
        """Alert on jobs that have exceeded their configured max_duration."""
        now = datetime.now(timezone.utc)
        for run in self.tracker.active_runs():
            job_cfg = self.config.job_by_name(run.job_name)
            if job_cfg is None or job_cfg.max_duration is None:
                continue
            elapsed = (now - run.started_at).total_seconds()
            if elapsed > job_cfg.max_duration and run.run_id not in self._overrun_alerted:
                self._overrun_alerted.add(run.run_id)
                alert = Alert(
                    alert_type=AlertType.OVERRUN,
                    job_name=run.job_name,
                    run=run,
                    message=(
                        f"Job '{run.job_name}' has been running for {elapsed:.0f}s, "
                        f"exceeding max_duration of {job_cfg.max_duration}s."
                    ),
                )
                self.dispatcher.dispatch(alert)

    def _check_completed_runs(self) -> None:
        """Alert on recently completed runs that exited with a non-zero code."""
        for run in self.tracker.drain_unalerted():
            if not run.succeeded():
                alert = Alert(
                    alert_type=AlertType.FAILURE,
                    job_name=run.job_name,
                    run=run,
                    message=(
                        f"Job '{run.job_name}' failed with exit code {run.exit_code} "
                        f"(duration: {run.duration():.1f}s)."
                    ),
                )
                self.dispatcher.dispatch(alert)
