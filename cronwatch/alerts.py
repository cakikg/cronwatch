"""Alert dispatching for job failures and overruns."""

import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from cronwatch.tracker import JobRun

logger = logging.getLogger(__name__)


class AlertType(Enum):
    FAILURE = auto()
    OVERRUN = auto()


@dataclass
class Alert:
    alert_type: AlertType
    job_name: str
    message: str
    run: Optional[JobRun] = None


class AlertDispatcher:
    """Collects and dispatches alerts to registered handlers."""

    def __init__(self):
        self._handlers: list = []
        self._alerts: list[Alert] = []

    def register_handler(self, handler) -> None:
        """Register a callable handler(alert: Alert) -> None."""
        self._handlers.append(handler)

    def dispatch(self, alert: Alert) -> None:
        self._alerts.append(alert)
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception as exc:  # noqa: BLE001
                logger.error("Alert handler %s raised: %s", handler, exc)

    def failure(self, run: JobRun) -> None:
        alert = Alert(
            alert_type=AlertType.FAILURE,
            job_name=run.job_name,
            message=(
                f"Job '{run.job_name}' failed with exit code {run.exit_code} "
                f"after {run.duration:.1f}s."
            ),
            run=run,
        )
        self.dispatch(alert)

    def overrun(self, job_name: str, elapsed: float, max_duration: float) -> None:
        alert = Alert(
            alert_type=AlertType.OVERRUN,
            job_name=job_name,
            message=(
                f"Job '{job_name}' overrun: running for {elapsed:.1f}s, "
                f"limit is {max_duration}s."
            ),
        )
        self.dispatch(alert)

    def all_alerts(self) -> list[Alert]:
        return list(self._alerts)

    def alerts_for_job(self, job_name: str) -> list[Alert]:
        """Return all alerts recorded for a specific job name."""
        return [a for a in self._alerts if a.job_name == job_name]

    def clear_alerts(self) -> None:
        """Discard all stored alerts, e.g. after they have been reported."""
        self._alerts.clear()
