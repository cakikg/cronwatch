"""Tests for cronwatch.ratelimit."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cronwatch.alerts import Alert, AlertType
from cronwatch.ratelimit import AlertRateLimiter, RateLimitConfig


@pytest.fixture()
def now(monkeypatch):
    _t = [0.0]

    def _clock():
        return _t[0]

    def _advance(seconds: float):
        _t[0] += seconds

    return _clock, _advance


@pytest.fixture()
def config():
    return RateLimitConfig(max_alerts=3, window_seconds=60.0)


@pytest.fixture()
def handler():
    return MagicMock()


@pytest.fixture()
def limiter(handler, config, now):
    clock, _ = now
    return AlertRateLimiter(handler=handler, config=config, clock=clock)


def _alert(job_name: str = "backup", alert_type: AlertType = AlertType.FAILURE) -> Alert:
    return Alert(job_name=job_name, alert_type=alert_type, message="test")


def test_alert_passes_within_limit(limiter, handler):
    for _ in range(3):
        limiter(_alert())
    assert handler.call_count == 3


def test_alert_dropped_when_limit_exceeded(limiter, handler):
    for _ in range(5):
        limiter(_alert())
    assert handler.call_count == 3


def test_window_resets_after_expiry(limiter, handler, now):
    clock, advance = now
    for _ in range(3):
        limiter(_alert())
    assert handler.call_count == 3

    advance(61.0)  # slide past the 60-second window
    limiter(_alert())
    assert handler.call_count == 4


def test_different_jobs_tracked_independently(limiter, handler):
    for _ in range(3):
        limiter(_alert(job_name="backup"))
    for _ in range(3):
        limiter(_alert(job_name="cleanup"))
    assert handler.call_count == 6


def test_different_alert_types_tracked_independently(limiter, handler):
    for _ in range(3):
        limiter(_alert(alert_type=AlertType.FAILURE))
    for _ in range(3):
        limiter(_alert(alert_type=AlertType.OVERRUN))
    assert handler.call_count == 6


def test_reset_clears_all_state(limiter, handler):
    for _ in range(3):
        limiter(_alert())
    limiter.reset()
    limiter(_alert())
    assert handler.call_count == 4


def test_reset_scoped_to_job(limiter, handler):
    for _ in range(3):
        limiter(_alert(job_name="backup"))
    for _ in range(3):
        limiter(_alert(job_name="cleanup"))
    limiter.reset(job_name="backup")
    limiter(_alert(job_name="backup"))   # should pass
    limiter(_alert(job_name="cleanup"))  # still blocked
    assert handler.call_count == 7
