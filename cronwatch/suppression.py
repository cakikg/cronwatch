"""Alert suppression windows — silence alerts during scheduled maintenance."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from cronwatch.alerts import Alert


@dataclass
class SuppressionWindow:
    """A time window during which alerts for specific jobs are suppressed."""

    job_name: str
    start: float  # Unix timestamp
    end: float    # Unix timestamp
    reason: str = ""

    def is_active(self, clock: Callable[[], float] = time.time) -> bool:
        """Return True if the window is currently active."""
        now = clock()
        return self.start <= now <= self.end

    def covers(self, alert: Alert, clock: Callable[[], float] = time.time) -> bool:
        """Return True if this window suppresses the given alert."""
        return alert.job_name == self.job_name and self.is_active(clock)


@dataclass
class AlertSuppressor:
    """Wraps an alert handler and skips calls during active suppression windows."""

    handler: Callable[[Alert], None]
    _windows: List[SuppressionWindow] = field(default_factory=list, init=False)
    _clock: Callable[[], float] = field(default=time.time, init=False)

    def set_clock(self, clock: Callable[[], float]) -> None:
        self._clock = clock

    def add_window(self, window: SuppressionWindow) -> None:
        """Register a suppression window."""
        self._windows.append(window)

    def remove_expired(self) -> None:
        """Prune windows that have already ended."""
        now = self._clock()
        self._windows = [w for w in self._windows if w.end >= now]

    def is_suppressed(self, alert: Alert) -> bool:
        """Return True if any active window covers this alert."""
        return any(w.covers(alert, self._clock) for w in self._windows)

    def __call__(self, alert: Alert) -> None:
        """Forward the alert to the inner handler unless suppressed."""
        if not self.is_suppressed(alert):
            self.handler(alert)

    def active_windows(self) -> List[SuppressionWindow]:
        """Return currently active windows."""
        return [w for w in self._windows if w.is_active(self._clock)]
