"""Tests for cronwatch.pipeline.ExecutionPipeline."""

from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerts import Alert, AlertDispatcher, AlertType
from cronwatch.config import JobConfig
from cronwatch.pipeline import ExecutionPipeline
from cronwatch.runner import JobRunner
from cronwatch.tracker import JobTracker


@pytest.fixture()
def good_job():
    return JobConfig(name="good", command="echo ok", schedule="* * * * *", max_duration=60)


@pytest.fixture()
def bad_job():
    return JobConfig(name="bad", command="exit 1", schedule="* * * * *")


@pytest.fixture()
def tracker(good_job, bad_job):
    t = JobTracker([good_job, bad_job])
    return t


@pytest.fixture()
def dispatcher():
    d = AlertDispatcher()
    d.dispatch = MagicMock()
    return d


@pytest.fixture()
def pipeline(tracker, dispatcher, good_job, bad_job):
    runner = JobRunner(tracker)
    return ExecutionPipeline(runner, tracker, dispatcher, [good_job, bad_job])


def test_success_does_not_dispatch_alert(pipeline, dispatcher, good_job):
    pipeline.execute(good_job)
    dispatcher.dispatch.assert_not_called()


def test_failure_dispatches_failure_alert(pipeline, dispatcher, bad_job):
    pipeline.execute(bad_job)
    dispatcher.dispatch.assert_called_once()
    alert: Alert = dispatcher.dispatch.call_args[0][0]
    assert alert.alert_type == AlertType.FAILURE
    assert alert.job_name == bad_job.name


def test_overrun_dispatches_overrun_alert(tracker, dispatcher):
    slow_job = JobConfig(name="slow", command="echo hi", schedule="* * * * *", max_duration=0)
    tracker.register(slow_job)
    runner = JobRunner(tracker)
    pipeline = ExecutionPipeline(runner, tracker, dispatcher, [slow_job])
    # Patch duration to simulate overrun
    with patch("cronwatch.pipeline.JobRun.duration", return_value=999.0):
        pipeline.execute(slow_job)
    dispatcher.dispatch.assert_called_once()
    alert: Alert = dispatcher.dispatch.call_args[0][0]
    assert alert.alert_type == AlertType.OVERRUN


def test_execute_returns_exit_code(pipeline, good_job):
    code = pipeline.execute(good_job)
    assert code == 0
