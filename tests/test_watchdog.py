"""Tests for cronwatch.watchdog and cronwatch.watchdog_factory."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerts import Alert, AlertDispatcher, AlertType
from cronwatch.config import JobConfig
from cronwatch.tracker import JobTracker
from cronwatch.watchdog import Watchdog, WatchdogConfig
from cronwatch.watchdog_factory import build_watchdog


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def job_config():
    return JobConfig(name="backup", schedule="0 2 * * *", max_runtime=30)


@pytest.fixture
def tracker(job_config):
    t = JobTracker()
    t.register(job_config)
    return t


@pytest.fixture
def dispatcher():
    d = AlertDispatcher()
    d._handler = MagicMock()
    d.register_handler(d._handler)
    return d


@pytest.fixture
def frozen_clock():
    """Returns a callable clock fixed at a known epoch."""
    base = 1_700_000_000.0
    return lambda: base


# ---------------------------------------------------------------------------
# Watchdog.check
# ---------------------------------------------------------------------------

def test_no_alert_when_within_limit(tracker, dispatcher, frozen_clock):
    run_id = tracker.start("backup")
    # Patch the run's started_at so elapsed < max_runtime
    tracker.active_runs()[0].started_at = frozen_clock() - 10  # 10s elapsed, limit 30
    watchdog = Watchdog(tracker, dispatcher, clock=frozen_clock)
    alerts = watchdog.check()
    assert alerts == []
    dispatcher._handler.assert_not_called()


def test_alert_fired_on_overrun(tracker, dispatcher, frozen_clock):
    run_id = tracker.start("backup")
    tracker.active_runs()[0].started_at = frozen_clock() - 60  # 60s elapsed, limit 30
    watchdog = Watchdog(tracker, dispatcher, clock=frozen_clock)
    alerts = watchdog.check()
    assert len(alerts) == 1
    assert alerts[0].alert_type == AlertType.OVERRUN
    assert alerts[0].job_name == "backup"
    dispatcher._handler.assert_called_once()


def test_alert_not_duplicated_on_second_check(tracker, dispatcher, frozen_clock):
    run_id = tracker.start("backup")
    tracker.active_runs()[0].started_at = frozen_clock() - 60
    watchdog = Watchdog(tracker, dispatcher, clock=frozen_clock)
    watchdog.check()
    watchdog.check()  # second call — should not re-alert
    assert dispatcher._handler.call_count == 1


def test_reset_clears_alerted_flag(tracker, dispatcher, frozen_clock):
    run_id = tracker.start("backup")
    tracker.active_runs()[0].started_at = frozen_clock() - 60
    watchdog = Watchdog(tracker, dispatcher, clock=frozen_clock)
    watchdog.check()
    watchdog.reset(run_id)
    watchdog.check()  # should fire again after reset
    assert dispatcher._handler.call_count == 2


def test_no_alert_when_max_runtime_not_set(dispatcher, frozen_clock):
    cfg = JobConfig(name="nolimit", schedule="* * * * *", max_runtime=None)
    t = JobTracker()
    t.register(cfg)
    run_id = t.start("nolimit")
    t.active_runs()[0].started_at = frozen_clock() - 9999
    watchdog = Watchdog(t, dispatcher, clock=frozen_clock)
    alerts = watchdog.check()
    assert alerts == []


# ---------------------------------------------------------------------------
# watchdog_factory.build_watchdog
# ---------------------------------------------------------------------------

def test_build_watchdog_returns_watchdog(tracker, dispatcher):
    config = MagicMock()
    config.extra = {}
    wd = build_watchdog(config, tracker, dispatcher)
    assert isinstance(wd, Watchdog)


def test_build_watchdog_uses_custom_poll_interval(tracker, dispatcher):
    config = MagicMock()
    config.extra = {"watchdog_poll_interval": "5.5"}
    wd = build_watchdog(config, tracker, dispatcher)
    assert wd._config.poll_interval == pytest.approx(5.5)
