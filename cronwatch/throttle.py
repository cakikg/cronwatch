"""Alert throttling to prevent notification floods."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional, Tuple

from cronwatch.alerts import Alert, AlertType


@dataclass
class ThrottleConfig:
    """Configuration for alert throttling."""
    min_interval_seconds: int = 300  # 5 minutes default
    max_alerts_per_hour: int = 10


@dataclass
class _ThrottleState:
    last_sent: Optional[datetime] = None
    sent_this_hour: int = 0
    hour_window_start: Optional[datetime] = None


class AlertThrottle:
    """Wraps an alert handler and suppresses duplicate/flood alerts."""

    def __init__(
        self,
        config: ThrottleConfig,
        clock: Callable[[], datetime] = datetime.utcnow,
    ) -> None:
        self._config = config
        self._clock = clock
        # key: (job_name, alert_type) -> state
        self._state: Dict[Tuple[str, AlertType], _ThrottleState] = {}

    def _get_state(self, key: Tuple[str, AlertType]) -> _ThrottleState:
        if key not in self._state:
            self._state[key] = _ThrottleState()
        return self._state[key]

    def should_send(self, alert: Alert) -> bool:
        """Return True if the alert should be forwarded to the handler."""
        key = (alert.job_name, alert.alert_type)
        state = self._get_state(key)
        now = self._clock()

        # Reset hourly window if needed
        if state.hour_window_start is None or (
            now - state.hour_window_start >= timedelta(hours=1)
        ):
            state.hour_window_start = now
            state.sent_this_hour = 0

        if state.sent_this_hour >= self._config.max_alerts_per_hour:
            return False

        if state.last_sent is not None:
            elapsed = (now - state.last_sent).total_seconds()
            if elapsed < self._config.min_interval_seconds:
                return False

        return True

    def record_sent(self, alert: Alert) -> None:
        """Record that an alert was successfully dispatched."""
        key = (alert.job_name, alert.alert_type)
        state = self._get_state(key)
        state.last_sent = self._clock()
        state.sent_this_hour += 1

    def reset(self, job_name: str, alert_type: Optional[AlertType] = None) -> None:
        """Clear throttle state for a job, optionally filtered by type."""
        keys_to_remove = [
            k for k in self._state
            if k[0] == job_name and (alert_type is None or k[1] == alert_type)
        ]
        for k in keys_to_remove:
            del self._state[k]
