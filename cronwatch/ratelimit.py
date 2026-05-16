"""Rate limiting for alert dispatching — caps alerts per job per time window."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List

from cronwatch.alerts import Alert, AlertType


@dataclass
class RateLimitConfig:
    max_alerts: int = 5
    window_seconds: float = 3600.0


@dataclass
class _WindowState:
    timestamps: List[float] = field(default_factory=list)

    def prune(self, cutoff: float) -> None:
        self.timestamps = [t for t in self.timestamps if t >= cutoff]

    def count(self) -> int:
        return len(self.timestamps)

    def record(self, ts: float) -> None:
        self.timestamps.append(ts)


class AlertRateLimiter:
    """Wraps an alert handler and drops alerts that exceed the rate limit."""

    def __init__(
        self,
        handler: Callable[[Alert], None],
        config: RateLimitConfig,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._handler = handler
        self._config = config
        self._clock = clock
        self._states: Dict[str, _WindowState] = defaultdict(_WindowState)

    def __call__(self, alert: Alert) -> None:
        key = f"{alert.job_name}:{alert.alert_type.value}"
        now = self._clock()
        cutoff = now - self._config.window_seconds
        state = self._states[key]
        state.prune(cutoff)

        if state.count() >= self._config.max_alerts:
            return

        state.record(now)
        self._handler(alert)

    def reset(self, job_name: str | None = None) -> None:
        """Clear rate-limit state, optionally scoped to a single job."""
        if job_name is None:
            self._states.clear()
        else:
            keys = [k for k in self._states if k.startswith(f"{job_name}:")]
            for k in keys:
                del self._states[k]
