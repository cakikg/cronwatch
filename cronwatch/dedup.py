"""Alert deduplication: suppress repeated identical alerts within a cooldown window."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Tuple

from cronwatch.alerts import Alert, AlertType


@dataclass
class DedupConfig:
    """Configuration for alert deduplication."""
    cooldown_seconds: int = 300  # 5 minutes default


# Key: (job_name, alert_type)
_DedupKey = Tuple[str, AlertType]


class AlertDeduplicator:
    """Wraps an alert handler and suppresses duplicate alerts within the cooldown window."""

    def __init__(
        self,
        handler: Callable[[Alert], None],
        config: DedupConfig,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._handler = handler
        self._config = config
        self._clock = clock
        self._last_sent: Dict[_DedupKey, float] = {}

    def __call__(self, alert: Alert) -> None:
        """Forward the alert to the wrapped handler only if outside the cooldown window."""
        key: _DedupKey = (alert.job_name, alert.alert_type)
        now = self._clock()
        last = self._last_sent.get(key)

        if last is not None and (now - last) < self._config.cooldown_seconds:
            return  # suppressed

        self._last_sent[key] = now
        self._handler(alert)

    def reset(self, job_name: str, alert_type: Optional[AlertType] = None) -> None:
        """Clear dedup state for a job (or a specific alert type)."""
        if alert_type is not None:
            self._last_sent.pop((job_name, alert_type), None)
        else:
            keys = [k for k in self._last_sent if k[0] == job_name]
            for k in keys:
                del self._last_sent[k]

    def is_suppressed(self, job_name: str, alert_type: AlertType) -> bool:
        """Return True if an alert for this job/type would currently be suppressed."""
        key: _DedupKey = (job_name, alert_type)
        last = self._last_sent.get(key)
        if last is None:
            return False
        return (self._clock() - last) < self._config.cooldown_seconds
