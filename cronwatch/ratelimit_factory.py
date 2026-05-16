"""Factory for building AlertRateLimiter from config."""

from __future__ import annotations

from typing import Callable

from cronwatch.alerts import Alert
from cronwatch.ratelimit import AlertRateLimiter, RateLimitConfig


def build_rate_limiter(
    handler: Callable[[Alert], None],
    max_alerts: int = 5,
    window_seconds: float = 3600.0,
) -> AlertRateLimiter:
    """Wrap *handler* with rate-limiting behaviour.

    Args:
        handler: The downstream alert handler to protect.
        max_alerts: Maximum number of alerts allowed per job per window.
        window_seconds: Length of the sliding time window in seconds.

    Returns:
        A configured :class:`AlertRateLimiter` instance.
    """
    config = RateLimitConfig(
        max_alerts=max_alerts,
        window_seconds=window_seconds,
    )
    return AlertRateLimiter(handler=handler, config=config)
