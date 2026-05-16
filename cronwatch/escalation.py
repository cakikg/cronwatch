"""Alert escalation: re-alert if a job remains unhealthy after a grace period."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from cronwatch.alerts import Alert, AlertType


@dataclass
class EscalationConfig:
    """Configuration for alert escalation behaviour."""
    grace_period: float          # seconds before first escalation
    repeat_interval: float       # seconds between subsequent escalations
    max_escalations: int = 3     # 0 = unlimited


@dataclass
class _EscalationState:
    first_alert_at: float
    last_escalated_at: float
    escalation_count: int = 0


Clock = Callable[[], float]


class AlertEscalator:
    """Wraps an alert handler and re-fires escalated alerts for persistent failures."""

    def __init__(
        self,
        config: EscalationConfig,
        handler: Callable[[Alert], None],
        clock: Clock = time.monotonic,
    ) -> None:
        self._config = config
        self._handler = handler
        self._clock = clock
        self._states: Dict[str, _EscalationState] = {}

    def __call__(self, alert: Alert) -> None:
        """Handle an incoming alert and record state for future escalation."""
        key = self._key(alert)
        now = self._clock()
        if key not in self._states:
            self._states[key] = _EscalationState(
                first_alert_at=now,
                last_escalated_at=now,
            )
        self._handler(alert)

    def tick(self, alert: Alert) -> None:
        """Call periodically to trigger escalations if the alert persists."""
        key = self._key(alert)
        state = self._states.get(key)
        if state is None:
            return

        cfg = self._config
        now = self._clock()
        elapsed_since_first = now - state.first_alert_at
        elapsed_since_last = now - state.last_escalated_at

        if elapsed_since_first < cfg.grace_period:
            return

        if elapsed_since_last < cfg.repeat_interval:
            return

        if cfg.max_escalations and state.escalation_count >= cfg.max_escalations:
            return

        state.escalation_count += 1
        state.last_escalated_at = now
        self._handler(alert)

    def resolve(self, job_name: str) -> None:
        """Clear escalation state once a job recovers."""
        self._states.pop(job_name, None)

    def _key(self, alert: Alert) -> str:
        return f"{alert.job_name}:{alert.alert_type.value}"
