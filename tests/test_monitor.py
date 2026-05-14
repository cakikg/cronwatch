"""Tests for CronMonitor — overrun detection and failure alerting."""

import time
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.monitor import CronMonitor
from cronwatch.tracker import JobTracker, JobRun
from cronwatch.alerts import AlertDispatcher, AlertType
from cronwatch.config import CronwatchConfig, JobConfig


@pytest.fixture
def job_config():
    return JobConfig(name="backup", schedule="0 2 * * *", max_duration=60)


@pytest.fixture
def config(job_config):
    cfg = MagicMock(spec=CronwatchConfig)
    cfg.job_by_name.return_value = job_config
    return cfg


@pytest.fixture
def tracker():
    return JobTracker()


@pytest.fixture
def dispatcher():
    d = AlertDispatcher()
    d.dispatch = MagicMock()
    return d


@pytest.fixture
def monitor(config, tracker, dispatcher):
    return CronMonitor(config, tracker, dispatcher, poll_interval=0.05)


def test_failure_alert_on_nonzero_exit(monitor, tracker, dispatcher):
    run = tracker.start("backup")
    tracker.finish(run.run_id, exit_code=1)
    monitor._check_completed_runs()
    dispatcher.dispatch.assert_called_once()
    alert = dispatcher.dispatch.call_args[0][0]
    assert alert.alert_type == AlertType.FAILURE
    assert alert.job_name == "backup"


def test_no_alert_on_success(monitor, tracker, dispatcher):
    run = tracker.start("backup")
    tracker.finish(run.run_id, exit_code=0)
    monitor._check_completed_runs()
    dispatcher.dispatch.assert_not_called()


def test_overrun_alert_when_exceeded(monitor, tracker, dispatcher, job_config):
    run = tracker.start("backup")
    # Backdate start time so elapsed > max_duration
    run.started_at = datetime.now(timezone.utc) - timedelta(seconds=job_config.max_duration + 10)
    monitor._check_active_runs()
    dispatcher.dispatch.assert_called_once()
    alert = dispatcher.dispatch.call_args[0][0]
    assert alert.alert_type == AlertType.OVERRUN


def test_overrun_alert_not_repeated(monitor, tracker, dispatcher, job_config):
    run = tracker.start("backup")
    run.started_at = datetime.now(timezone.utc) - timedelta(seconds=job_config.max_duration + 10)
    monitor._check_active_runs()
    monitor._check_active_runs()  # second check should not re-alert
    assert dispatcher.dispatch.call_count == 1


def test_monitor_start_stop(monitor):
    monitor.start()
    assert monitor._thread is not None
    assert monitor._thread.is_alive()
    monitor.stop(timeout=2.0)
    assert not monitor._thread.is_alive()


def test_drain_unalerted_cleared_after_check(monitor, tracker, dispatcher):
    run = tracker.start("backup")
    tracker.finish(run.run_id, exit_code=2)
    monitor._check_completed_runs()
    # Second call should find nothing new
    dispatcher.dispatch.reset_mock()
    monitor._check_completed_runs()
    dispatcher.dispatch.assert_not_called()
