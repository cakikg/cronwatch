"""Cooldown: suppresses repeated alerts for a job until a quiet period elapses."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Tuple

from cronwatch.alerts import Alert, AlertType


@dataclass
class CooldownConfig:
    """Configuration for the alert cooldown window."""

    # Seconds that must pass after the last alert before the same
    # (job, alert_type) pair is forwarded again.
    window_seconds: int = 300


# Key: (job_name, AlertType)
_StateKey = Tuple[str, AlertType]


class AlertCooldown:
    """Callable wrapper that suppresses duplicate alerts within a cooldown window.

    Wrap any alert handler with this class and register the wrapper instead::

        cooldown = AlertCooldown(config, clock=time.time)
        dispatcher.register_handler(cooldown(my_handler))
    """

    def __init__(
        self,
        config: CooldownConfig,
        handler: Callable[[Alert], None],
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._config = config
        self._handler = handler
        self._clock = clock
        # Maps (job_name, alert_type) -> timestamp of last forwarded alert
        self._last_sent: Dict[_StateKey, float] = {}

    def __call__(self, alert: Alert) -> None:
        key: _StateKey = (alert.job_name, alert.alert_type)
        now = self._clock()
        last = self._last_sent.get(key)

        if last is None or (now - last) >= self._config.window_seconds:
            self._last_sent[key] = now
            self._handler(alert)

    def reset(self, job_name: Optional[str] = None, alert_type: Optional[AlertType] = None) -> None:
        """Clear cooldown state, optionally scoped to a specific job/alert_type."""
        if job_name is None and alert_type is None:
            self._last_sent.clear()
            return
        keys_to_remove = [
            k for k in self._last_sent
            if (job_name is None or k[0] == job_name)
            and (alert_type is None or k[1] == alert_type)
        ]
        for k in keys_to_remove:
            del self._last_sent[k]
