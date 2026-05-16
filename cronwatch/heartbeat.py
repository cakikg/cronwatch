"""Heartbeat module: periodically writes a timestamp to signal the daemon is alive."""

from __future__ import annotations

import os
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class HeartbeatConfig:
    path: Path
    interval_seconds: float = 60.0


class Heartbeat:
    """Writes a Unix timestamp to a file at a regular interval."""

    def __init__(
        self,
        config: HeartbeatConfig,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._config = config
        self._clock = clock
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the background heartbeat thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="heartbeat")
        self._thread.start()

    def stop(self) -> None:
        """Signal the heartbeat thread to stop and wait for it."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self._config.interval_seconds + 1)
            self._thread = None

    def beat(self) -> None:
        """Write the current timestamp to the heartbeat file immediately."""
        self._config.path.parent.mkdir(parents=True, exist_ok=True)
        self._config.path.write_text(str(self._clock()))

    def last_beat(self) -> float | None:
        """Return the timestamp of the last heartbeat, or None if unavailable."""
        try:
            return float(self._config.path.read_text().strip())
        except (FileNotFoundError, ValueError):
            return None

    def is_alive(self, max_age_seconds: float | None = None) -> bool:
        """Return True if the last heartbeat is within max_age_seconds."""
        age_limit = max_age_seconds if max_age_seconds is not None else self._config.interval_seconds * 2
        last = self.last_beat()
        if last is None:
            return False
        return (self._clock() - last) <= age_limit

    def _loop(self) -> None:
        while not self._stop_event.wait(self._config.interval_seconds):
            self.beat()
