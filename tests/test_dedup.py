"""Tests for cronwatch.dedup alert deduplication."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from cronwatch.alerts import Alert, AlertType
from cronwatch.dedup import AlertDeduplicator, DedupConfig


@pytest.fixture
def now(monkeypatch):
    """Mutable clock value."""
    t = [0.0]
    return t


@pytest.fixture
def clock(now):
    return lambda: now[0]


@pytest.fixture
def config():
    return DedupConfig(cooldown_seconds=60)


@pytest.fixture
def handler():
    return MagicMock()


@pytest.fixture
def dedup(handler, config, clock):
    return AlertDeduplicator(handler=handler, config=config, clock=clock)


def _alert(job_name="backup", alert_type=AlertType.FAILURE):
    return Alert(
        job_name=job_name,
        alert_type=alert_type,
        message="something went wrong",
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
    )


def test_first_alert_is_forwarded(dedup, handler):
    dedup(_alert())
    handler.assert_called_once()


def test_duplicate_within_cooldown_is_suppressed(dedup, handler, now):
    dedup(_alert())
    now[0] = 30.0  # still within 60s cooldown
    dedup(_alert())
    assert handler.call_count == 1


def test_alert_forwarded_after_cooldown_expires(dedup, handler, now):
    dedup(_alert())
    now[0] = 61.0  # past cooldown
    dedup(_alert())
    assert handler.call_count == 2


def test_different_job_names_are_independent(dedup, handler):
    dedup(_alert(job_name="backup"))
    dedup(_alert(job_name="cleanup"))
    assert handler.call_count == 2


def test_different_alert_types_are_independent(dedup, handler):
    dedup(_alert(alert_type=AlertType.FAILURE))
    dedup(_alert(alert_type=AlertType.OVERRUN))
    assert handler.call_count == 2


def test_reset_clears_state_for_job(dedup, handler, now):
    dedup(_alert())
    now[0] = 10.0
    dedup.reset("backup")
    dedup(_alert())
    assert handler.call_count == 2


def test_reset_specific_type_only(dedup, handler, now):
    dedup(_alert(alert_type=AlertType.FAILURE))
    now[0] = 10.0
    dedup.reset("backup", AlertType.OVERRUN)  # wrong type, should not clear FAILURE
    dedup(_alert(alert_type=AlertType.FAILURE))
    assert handler.call_count == 1  # still suppressed


def test_is_suppressed_returns_true_within_cooldown(dedup, now):
    dedup(_alert())
    now[0] = 30.0
    assert dedup.is_suppressed("backup", AlertType.FAILURE) is True


def test_is_suppressed_returns_false_after_cooldown(dedup, now):
    dedup(_alert())
    now[0] = 61.0
    assert dedup.is_suppressed("backup", AlertType.FAILURE) is False


def test_is_suppressed_returns_false_for_unseen_job(dedup):
    assert dedup.is_suppressed("never_seen", AlertType.FAILURE) is False
