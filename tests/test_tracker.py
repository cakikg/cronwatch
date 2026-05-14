"""Tests for cronwatch.tracker."""

import time

import pytest

from cronwatch.config import JobConfig
from cronwatch.tracker import JobRun, JobTracker


@pytest.fixture()
def tracker():
    return JobTracker()


@pytest.fixture()
def job_config():
    return JobConfig(name="backup", schedule="0 2 * * *", max_duration=60)


def test_start_creates_active_run(tracker):
    run = tracker.start("backup")
    assert run.job_name == "backup"
    assert not run.is_complete
    assert len(tracker.active_runs()) == 1


def test_finish_moves_run_to_history(tracker):
    tracker.start("backup")
    run = tracker.finish("backup", exit_code=0)
    assert run.is_complete
    assert run.succeeded
    assert len(tracker.active_runs()) == 0
    assert len(tracker.history()) == 1


def test_finish_records_exit_code(tracker):
    tracker.start("backup")
    run = tracker.finish("backup", exit_code=1)
    assert not run.succeeded
    assert run.exit_code == 1


def test_duration_is_positive(tracker):
    tracker.start("backup")
    time.sleep(0.05)
    run = tracker.finish("backup", exit_code=0)
    assert run.duration is not None
    assert run.duration >= 0.05


def test_start_duplicate_raises(tracker):
    tracker.start("backup")
    with pytest.raises(ValueError, match="already running"):
        tracker.start("backup")


def test_finish_unknown_job_raises(tracker):
    with pytest.raises(KeyError):
        tracker.finish("nonexistent", exit_code=0)


def test_no_overrun_without_max_duration(tracker):
    config = JobConfig(name="backup", schedule="0 2 * * *", max_duration=None)
    tracker.start("backup")
    assert not tracker.is_overrun("backup", config)


def test_overrun_detected(tracker, job_config):
    run = tracker.start("backup")
    # Manually backdate the start time
    run.start_time = time.time() - 120
    assert tracker.is_overrun("backup", job_config)


def test_no_overrun_within_limit(tracker, job_config):
    tracker.start("backup")
    assert not tracker.is_overrun("backup", job_config)
