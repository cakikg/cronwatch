"""Tests for cronwatch.summary module."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from cronwatch.history import JobHistory, HistoryEntry
from cronwatch.history_recorder import HistoryRecorder
from cronwatch.summary import SummaryBuilder, JobSummary, CronwatchSummary


def _make_entry(exit_code: int, duration: float) -> HistoryEntry:
    now = datetime.utcnow()
    return HistoryEntry(
        job_name="test_job",
        started_at=now - timedelta(seconds=duration),
        finished_at=now,
        exit_code=exit_code,
        duration_seconds=duration,
    )


@pytest.fixture
def recorder():
    return MagicMock(spec=HistoryRecorder)


@pytest.fixture
def builder(recorder):
    return SummaryBuilder(recorder)


def _setup_recorder(recorder, entries):
    history = MagicMock(spec=JobHistory)
    history.all.return_value = entries
    history.last.return_value = entries[-1] if entries else None
    recorder.get_for_job.return_value = history


def test_build_returns_cronwatch_summary(builder, recorder):
    _setup_recorder(recorder, [_make_entry(0, 10.0)])
    result = builder.build(["job_a"])
    assert isinstance(result, CronwatchSummary)
    assert len(result.jobs) == 1


def test_summary_counts_successes_and_failures(builder, recorder):
    entries = [
        _make_entry(0, 5.0),
        _make_entry(0, 6.0),
        _make_entry(1, 3.0),
    ]
    _setup_recorder(recorder, entries)
    summary = builder.build(["job_a"])
    job: JobSummary = summary.jobs[0]
    assert job.total_runs == 3
    assert job.successful_runs == 2
    assert job.failed_runs == 1


def test_success_rate_calculation(builder, recorder):
    entries = [_make_entry(0, 1.0), _make_entry(1, 1.0)]
    _setup_recorder(recorder, entries)
    summary = builder.build(["job_a"])
    assert summary.jobs[0].success_rate == pytest.approx(50.0)


def test_avg_duration_computed(builder, recorder):
    entries = [_make_entry(0, 10.0), _make_entry(0, 20.0)]
    _setup_recorder(recorder, entries)
    summary = builder.build(["job_a"])
    assert summary.jobs[0].avg_duration_seconds == pytest.approx(15.0)


def test_no_runs_produces_zero_success_rate(builder, recorder):
    _setup_recorder(recorder, [])
    summary = builder.build(["empty_job"])
    job = summary.jobs[0]
    assert job.total_runs == 0
    assert job.success_rate == 0.0
    assert job.avg_duration_seconds is None
    assert job.last_run_at is None


def test_healthy_jobs_count(builder, recorder):
    history_ok = MagicMock(spec=JobHistory)
    history_ok.all.return_value = [_make_entry(0, 5.0)]
    history_ok.last.return_value = _make_entry(0, 5.0)

    history_fail = MagicMock(spec=JobHistory)
    history_fail.all.return_value = [_make_entry(1, 5.0)]
    history_fail.last.return_value = _make_entry(1, 5.0)

    recorder.get_for_job.side_effect = lambda name: (
        history_ok if name == "good" else history_fail
    )
    summary = builder.build(["good", "bad"])
    assert summary.healthy_jobs == 1
    assert summary.total_jobs == 2
