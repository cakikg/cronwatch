"""Tests for cronwatch.runner.JobRunner."""

import time
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import JobConfig
from cronwatch.runner import JobRunner
from cronwatch.tracker import JobTracker


@pytest.fixture()
def job_config():
    return JobConfig(name="test-job", command="echo hello", schedule="* * * * *", max_duration=10)


@pytest.fixture()
def tracker(job_config):
    t = JobTracker([job_config])
    return t


@pytest.fixture()
def runner(tracker):
    return JobRunner(tracker)


def test_run_success_records_exit_code(runner, tracker, job_config):
    exit_code = runner.run(job_config)
    assert exit_code == 0
    history = tracker.history(job_config.name)
    assert len(history) == 1
    assert history[0].exit_code == 0


def test_run_failure_records_nonzero_exit(runner, tracker):
    failing_job = JobConfig(name="fail-job", command="exit 2", schedule="* * * * *")
    tracker.register(failing_job)
    exit_code = runner.run(failing_job)
    assert exit_code != 0
    history = tracker.history(failing_job.name)
    assert history[0].exit_code != 0


def test_run_timeout_returns_124(tracker):
    slow_job = JobConfig(name="slow-job", command="sleep 60", schedule="* * * * *", max_duration=0)
    tracker.register(slow_job)
    runner = JobRunner(tracker, timeout_grace=0)
    exit_code = runner.run(slow_job)
    assert exit_code == 124


def test_run_async_returns_thread(runner, job_config):
    thread = runner.run_async(job_config)
    thread.join(timeout=5)
    assert not thread.is_alive()


def test_run_exception_records_exit_code_1(runner, tracker):
    bad_job = JobConfig(name="bad-job", command="", schedule="* * * * *")
    tracker.register(bad_job)
    with patch("subprocess.run", side_effect=OSError("boom")):
        exit_code = runner.run(bad_job)
    assert exit_code == 1
    assert tracker.history(bad_job.name)[0].exit_code == 1
