"""Tests for cronwatch.suppression."""

from __future__ import annotations

import pytest

from cronwatch.alerts import Alert, AlertType
from cronwatch.suppression import AlertSuppressor, SuppressionWindow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = 1_000_000.0


def _clock() -> float:
    return NOW


def _make_alert(job_name: str = "backup") -> Alert:
    return Alert(type=AlertType.FAILURE, job_name=job_name, message="boom")


@pytest.fixture
def handler():
    received: list[Alert] = []
    return received, received.append


@pytest.fixture
def suppressor(handler):
    _, fn = handler
    s = AlertSuppressor(handler=fn)
    s.set_clock(_clock)
    return s


# ---------------------------------------------------------------------------
# SuppressionWindow tests
# ---------------------------------------------------------------------------

def test_window_active_within_range():
    w = SuppressionWindow(job_name="backup", start=NOW - 60, end=NOW + 60)
    assert w.is_active(_clock) is True


def test_window_inactive_before_start():
    w = SuppressionWindow(job_name="backup", start=NOW + 10, end=NOW + 120)
    assert w.is_active(_clock) is False


def test_window_inactive_after_end():
    w = SuppressionWindow(job_name="backup", start=NOW - 120, end=NOW - 10)
    assert w.is_active(_clock) is False


def test_window_covers_matching_job():
    w = SuppressionWindow(job_name="backup", start=NOW - 60, end=NOW + 60)
    alert = _make_alert("backup")
    assert w.covers(alert, _clock) is True


def test_window_does_not_cover_other_job():
    w = SuppressionWindow(job_name="backup", start=NOW - 60, end=NOW + 60)
    alert = _make_alert("cleanup")
    assert w.covers(alert, _clock) is False


# ---------------------------------------------------------------------------
# AlertSuppressor tests
# ---------------------------------------------------------------------------

def test_alert_forwarded_when_no_windows(handler, suppressor):
    received, _ = handler
    suppressor(_make_alert())
    assert len(received) == 1


def test_alert_suppressed_during_active_window(handler, suppressor):
    received, _ = handler
    suppressor.add_window(SuppressionWindow("backup", NOW - 60, NOW + 60))
    suppressor(_make_alert("backup"))
    assert len(received) == 0


def test_alert_forwarded_for_different_job(handler, suppressor):
    received, _ = handler
    suppressor.add_window(SuppressionWindow("backup", NOW - 60, NOW + 60))
    suppressor(_make_alert("cleanup"))
    assert len(received) == 1


def test_remove_expired_prunes_old_windows(suppressor):
    suppressor.add_window(SuppressionWindow("backup", NOW - 200, NOW - 10))
    suppressor.add_window(SuppressionWindow("cleanup", NOW - 60, NOW + 60))
    suppressor.remove_expired()
    assert len(suppressor._windows) == 1
    assert suppressor._windows[0].job_name == "cleanup"


def test_active_windows_returns_only_active(suppressor):
    suppressor.add_window(SuppressionWindow("backup", NOW - 200, NOW - 10))
    suppressor.add_window(SuppressionWindow("cleanup", NOW - 60, NOW + 60))
    active = suppressor.active_windows()
    assert len(active) == 1
    assert active[0].job_name == "cleanup"


def test_multiple_windows_all_suppressed(handler, suppressor):
    received, _ = handler
    suppressor.add_window(SuppressionWindow("backup", NOW - 60, NOW + 60))
    suppressor.add_window(SuppressionWindow("backup", NOW - 30, NOW + 30))
    suppressor(_make_alert("backup"))
    assert len(received) == 0
