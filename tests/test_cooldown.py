"""Tests for cronwatch.cooldown."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cronwatch.alerts import Alert, AlertType
from cronwatch.cooldown import AlertCooldown, CooldownConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def now(monkeypatch):
    """Mutable current time (seconds)."""
    t = [1_000_000.0]
    return t


@pytest.fixture()
def clock(now):
    return lambda: now[0]


@pytest.fixture()
def config():
    return CooldownConfig(window_seconds=60)


@pytest.fixture()
def handler():
    return MagicMock()


@pytest.fixture()
def cooldown(config, handler, clock):
    return AlertCooldown(config, handler, clock=clock)


def _alert(job_name: str = "backup", alert_type: AlertType = AlertType.FAILURE) -> Alert:
    return Alert(job_name=job_name, alert_type=alert_type, message="test")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_first_alert_is_forwarded(cooldown, handler):
    cooldown(_alert())
    handler.assert_called_once()


def test_second_alert_within_window_suppressed(cooldown, handler, now):
    cooldown(_alert())
    now[0] += 30  # still inside 60-second window
    cooldown(_alert())
    assert handler.call_count == 1


def test_alert_forwarded_after_window_expires(cooldown, handler, now):
    cooldown(_alert())
    now[0] += 61  # past the 60-second window
    cooldown(_alert())
    assert handler.call_count == 2


def test_different_jobs_tracked_independently(cooldown, handler):
    cooldown(_alert(job_name="backup"))
    cooldown(_alert(job_name="cleanup"))
    assert handler.call_count == 2


def test_different_alert_types_tracked_independently(cooldown, handler):
    cooldown(_alert(alert_type=AlertType.FAILURE))
    cooldown(_alert(alert_type=AlertType.OVERRUN))
    assert handler.call_count == 2


def test_reset_clears_all_state(cooldown, handler, now):
    cooldown(_alert())
    cooldown.reset()
    cooldown(_alert())  # should be forwarded again
    assert handler.call_count == 2


def test_reset_scoped_to_job(cooldown, handler, now):
    cooldown(_alert(job_name="backup"))
    cooldown(_alert(job_name="cleanup"))
    cooldown.reset(job_name="backup")
    cooldown(_alert(job_name="backup"))   # forwarded — state cleared
    cooldown(_alert(job_name="cleanup"))  # suppressed — state intact
    assert handler.call_count == 3


def test_alert_at_exact_window_boundary_is_forwarded(cooldown, handler, now):
    cooldown(_alert())
    now[0] += 60  # exactly at boundary
    cooldown(_alert())
    assert handler.call_count == 2
