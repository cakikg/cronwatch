"""Tests for cronwatch.alerts."""

import pytest

from cronwatch.alerts import Alert, AlertDispatcher, AlertType
from cronwatch.tracker import JobRun


@pytest.fixture()
def dispatcher():
    return AlertDispatcher()


@pytest.fixture()
def failed_run():
    run = JobRun(job_name="sync", start_time=1000.0)
    run.end_time = 1005.0
    run.exit_code = 2
    return run


def test_failure_alert_dispatched(dispatcher, failed_run):
    received = []
    dispatcher.register_handler(received.append)
    dispatcher.failure(failed_run)
    assert len(received) == 1
    alert = received[0]
    assert alert.alert_type == AlertType.FAILURE
    assert alert.job_name == "sync"
    assert "exit code 2" in alert.message


def test_overrun_alert_dispatched(dispatcher):
    received = []
    dispatcher.register_handler(received.append)
    dispatcher.overrun("sync", elapsed=120.0, max_duration=60.0)
    assert len(received) == 1
    alert = received[0]
    assert alert.alert_type == AlertType.OVERRUN
    assert "120.0" in alert.message
    assert "60.0" in alert.message


def test_multiple_handlers_called(dispatcher, failed_run):
    results_a, results_b = [], []
    dispatcher.register_handler(results_a.append)
    dispatcher.register_handler(results_b.append)
    dispatcher.failure(failed_run)
    assert len(results_a) == 1
    assert len(results_b) == 1


def test_failing_handler_does_not_stop_others(dispatcher, failed_run):
    def bad_handler(alert):
        raise RuntimeError("boom")

    results = []
    dispatcher.register_handler(bad_handler)
    dispatcher.register_handler(results.append)
    dispatcher.failure(failed_run)  # should not raise
    assert len(results) == 1


def test_all_alerts_accumulates(dispatcher, failed_run):
    dispatcher.failure(failed_run)
    dispatcher.overrun("sync", 90.0, 60.0)
    assert len(dispatcher.all_alerts()) == 2
