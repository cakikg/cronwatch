"""Alert replay buffer: stores recent alerts and replays them to newly registered handlers."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Deque, List

from cronwatch.alerts import Alert

AlertHandler = Callable[[Alert], None]


@dataclass
class ReplayConfig:
    max_size: int = 50


@dataclass
class AlertReplayBuffer:
    """Buffers recent alerts and replays them to handlers that register late."""

    config: ReplayConfig = field(default_factory=ReplayConfig)
    _buffer: Deque[Alert] = field(init=False, default_factory=deque)
    _handlers: List[AlertHandler] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self._buffer = deque(maxlen=self.config.max_size)

    def record(self, alert: Alert) -> None:
        """Store an alert in the buffer and forward it to registered handlers."""
        self._buffer.append(alert)
        for handler in self._handlers:
            handler(alert)

    def register_handler(self, handler: AlertHandler, *, replay: bool = True) -> None:
        """Register a handler, optionally replaying buffered alerts to it."""
        if replay:
            for alert in list(self._buffer):
                handler(alert)
        self._handlers.append(handler)

    def clear(self) -> None:
        """Discard all buffered alerts."""
        self._buffer.clear()

    @property
    def buffered(self) -> List[Alert]:
        return list(self._buffer)

    def __len__(self) -> int:
        return len(self._buffer)
