"""Circuit breaker for alert handlers — stops firing alerts when a handler
is repeatedly failing, and automatically resets after a cooldown period."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from cronwatch.alerts import Alert


class BreakerState(Enum):
    CLOSED = "closed"      # Normal operation — alerts pass through.
    OPEN = "open"          # Handler is failing — alerts are suppressed.
    HALF_OPEN = "half_open"  # Testing if handler has recovered.


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 3       # Consecutive failures before opening.
    recovery_timeout: float = 60.0   # Seconds before attempting half-open.
    success_threshold: int = 1       # Successes in half-open before closing.


@dataclass
class _BreakerState:
    state: BreakerState = BreakerState.CLOSED
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    opened_at: Optional[float] = None


class CircuitBreaker:
    """Wraps an alert handler with circuit-breaker logic."""

    def __init__(
        self,
        handler: Callable[[Alert], None],
        config: CircuitBreakerConfig,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._handler = handler
        self._config = config
        self._clock = clock
        self._state = _BreakerState()

    @property
    def state(self) -> BreakerState:
        return self._state.state

    def __call__(self, alert: Alert) -> None:
        s = self._state

        if s.state == BreakerState.OPEN:
            elapsed = self._clock() - (s.opened_at or 0.0)
            if elapsed >= self._config.recovery_timeout:
                s.state = BreakerState.HALF_OPEN
                s.consecutive_successes = 0
            else:
                return  # Still open — suppress alert.

        try:
            self._handler(alert)
        except Exception:
            s.consecutive_failures += 1
            s.consecutive_successes = 0
            if s.consecutive_failures >= self._config.failure_threshold:
                s.state = BreakerState.OPEN
                s.opened_at = self._clock()
            raise
        else:
            s.consecutive_successes += 1
            s.consecutive_failures = 0
            if s.state == BreakerState.HALF_OPEN:
                if s.consecutive_successes >= self._config.success_threshold:
                    s.state = BreakerState.CLOSED

    def reset(self) -> None:
        """Manually reset to CLOSED state."""
        self._state = _BreakerState()
