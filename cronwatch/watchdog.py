"""Watchdog: detects and alerts on jobs that have exceeded their max runtime."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List

from cronwatch.tracker import JobTracker
from cronwatch.alerts import Alert, AlertDispatcher, AlertType


@dataclass
class WatchdogConfig:
    poll_interval: float = 10.0  # seconds between checks


class Watchdog:
    """Periodically checks active job runs and fires overrun alerts."""

    def __init__(
        self,
        tracker: JobTracker,
        dispatcher: AlertDispatcher,
        config: WatchdogConfig | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._tracker = tracker
        self._dispatcher = dispatcher
        self._config = config or WatchdogConfig()
        self._clock = clock
        self._alerted: set[str] = set()  # run_ids already alerted

    def check(self) -> List[Alert]:
        """Inspect all active runs; return list of overrun alerts dispatched."""
        now = self._clock()
        fired: List[Alert] = []

        for run in self._tracker.active_runs():
            job_cfg = self._tracker.get_config(run.job_name)
            if job_cfg is None or job_cfg.max_runtime is None:
                continue

            elapsed = now - run.started_at
            if elapsed > job_cfg.max_runtime and run.run_id not in self._alerted:
                self._alerted.add(run.run_id)
                alert = Alert(
                    alert_type=AlertType.OVERRUN,
                    job_name=run.job_name,
                    run=run,
                    message=(
                        f"Job '{run.job_name}' has been running for "
                        f"{elapsed:.1f}s (limit {job_cfg.max_runtime}s)"
                    ),
                )
                self._dispatcher.dispatch(alert)
                fired.append(alert)

        return fired

    def reset(self, run_id: str) -> None:
        """Clear the alerted flag for a run (e.g. after it finishes)."""
        self._alerted.discard(run_id)
