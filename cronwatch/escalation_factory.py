"""Build an AlertEscalator from CronwatchConfig."""

from __future__ import annotations

from typing import Callable

from cronwatch.alerts import Alert
from cronwatch.config import CronwatchConfig
from cronwatch.escalation import AlertEscalator, EscalationConfig

_DEFAULT_GRACE = 300.0      # 5 minutes
_DEFAULT_REPEAT = 600.0     # 10 minutes
_DEFAULT_MAX = 3


def build_escalator(
    config: CronwatchConfig,
    handler: Callable[[Alert], None],
) -> AlertEscalator:
    """Construct an AlertEscalator using values from *config* or sensible defaults."""
    raw = getattr(config, "escalation", {}) or {}

    esc_config = EscalationConfig(
        grace_period=float(raw.get("grace_period", _DEFAULT_GRACE)),
        repeat_interval=float(raw.get("repeat_interval", _DEFAULT_REPEAT)),
        max_escalations=int(raw.get("max_escalations", _DEFAULT_MAX)),
    )

    return AlertEscalator(config=esc_config, handler=handler)
