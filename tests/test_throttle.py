"""Tests for alert throttling logic."""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from cronwatch.alerts import Alert, AlertType
from cronwatch.throttle import AlertThrottle, ThrottleConfig


@pytest.fixture()
def now() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0)


@pytest.fixture()
def clock(now):
    mock = MagicMock(return_value=now)
    return mock


@pytest.fixture()
def config() -> ThrottleConfig:
    return ThrottleConfig(min_interval_seconds=60, max_alerts_per_hour=3)


@pytest.fixture()
def throttle(config, clock) -> AlertThrottle:
    return AlertThrottle(config=config, clock=clock)


def _alert(job_name="backup", alert_type=AlertType.FAILURE) -> Alert:
    run = MagicMock()
    run.job_name = job_name
    return Alert(alert_type=alert_type, job_name=job_name, run=run, message="oops")


def test_first_alert_is_allowed(throttle):
    alert = _alert()
    assert throttle.should_send(alert) is True


def test_second_alert_within_interval_is_suppressed(throttle, clock, now):
    alert = _alert()
    throttle.record_sent(alert)
    # Still within the min_interval_seconds window
    clock.return_value = now + timedelta(seconds=30)
    assert throttle.should_send(alert) is False


def test_alert_allowed_after_interval_passes(throttle, clock, now):
    alert = _alert()
    throttle.record_sent(alert)
    clock.return_value = now + timedelta(seconds=90)
    assert throttle.should_send(alert) is True


def test_max_alerts_per_hour_suppresses_excess(throttle, clock, now):
    alert = _alert()
    # Send up to the limit
    for i in range(3):
        clock.return_value = now + timedelta(seconds=i * 70)
        assert throttle.should_send(alert) is True
        throttle.record_sent(alert)
    # Next one should be suppressed even after interval
    clock.return_value = now + timedelta(seconds=4 * 70)
    assert throttle.should_send(alert) is False


def test_hourly_window_resets(throttle, clock, now):
    alert = _alert()
    for i in range(3):
        clock.return_value = now + timedelta(seconds=i * 70)
        throttle.record_sent(alert)
    # Advance past 1 hour — window resets
    clock.return_value = now + timedelta(hours=1, seconds=1)
    assert throttle.should_send(alert) is True


def test_different_job_names_tracked_independently(throttle):
    a1 = _alert(job_name="backup")
    a2 = _alert(job_name="cleanup")
    throttle.record_sent(a1)
    assert throttle.should_send(a2) is True


def test_reset_clears_state(throttle, clock, now):
    alert = _alert()
    throttle.record_sent(alert)
    throttle.reset("backup")
    # After reset, throttle should allow the alert again
    assert throttle.should_send(alert) is True


def test_reset_by_alert_type_only_clears_matching(throttle, clock, now):
    a_fail = _alert(alert_type=AlertType.FAILURE)
    a_over = _alert(alert_type=AlertType.OVERRUN)
    throttle.record_sent(a_fail)
    throttle.record_sent(a_over)
    throttle.reset("backup", AlertType.FAILURE)
    assert throttle.should_send(a_fail) is True
    # overrun still throttled
    assert throttle.should_send(a_over) is False
