"""Subprocess runner that executes cron jobs and reports results to the tracker."""

import subprocess
import threading
from datetime import datetime
from typing import Optional

from cronwatch.config import JobConfig
from cronwatch.tracker import JobTracker


class JobRunner:
    """Runs a job as a subprocess and records the outcome in the tracker."""

    def __init__(self, tracker: JobTracker, timeout_grace: int = 5) -> None:
        self._tracker = tracker
        self._timeout_grace = timeout_grace
        self._lock = threading.Lock()

    def run(self, job: JobConfig) -> int:
        """Execute *job* synchronously and return the exit code."""
        run_id = self._tracker.start(job.name, datetime.utcnow())
        exit_code: int = -1
        try:
            timeout = job.max_duration + self._timeout_grace if job.max_duration else None
            result = subprocess.run(
                job.command,
                shell=True,
                capture_output=True,
                timeout=timeout,
            )
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            exit_code = 124  # same convention as the `timeout` utility
        except Exception:  # noqa: BLE001
            exit_code = 1
        finally:
            self._tracker.finish(run_id, exit_code, datetime.utcnow())
        return exit_code

    def run_async(self, job: JobConfig) -> threading.Thread:
        """Spawn a daemon thread to run *job* and return it immediately."""
        thread = threading.Thread(target=self.run, args=(job,), daemon=True, name=f"runner-{job.name}")
        thread.start()
        return thread
