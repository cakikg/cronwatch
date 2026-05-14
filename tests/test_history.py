"""Tests for cronwatch.history and cronwatch.history_recorder."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from cronwatch.history import HistoryEntry, JobHistory, MAX_HISTORY_ENTRIES
from cronwatch.history_recorder import HistoryRecorder
from cronwatch.tracker import JobRun


@pytest.fixture
def history_file(tmp_path):
    return str(tmp_path / "history.json")


@pytest.fixture
def history(history_file):
    return JobHistory(path=history_file)


@pytest.fixture
def completed_run():
    run = JobRun(job_name="backup", started_at=datetime(2024, 1, 1, 2, 0, 0))
    run.finished_at = datetime(2024, 1, 1, 2, 5, 30)
    run.exit_code = 0
    run.timed_out = False
    return run


def test_record_and_retrieve(history):
    entry = HistoryEntry(
        job_name="backup",
        started_at="2024-01-01T02:00:00",
        finished_at="2024-01-01T02:05:30",
        exit_code=0,
        duration_seconds=330.0,
    )
    history.record(entry)
    assert len(history.get_for_job("backup")) == 1


def test_last_run_returns_most_recent(history):
    for i in range(3):
        history.record(
            HistoryEntry(
                job_name="job",
                started_at=f"2024-01-0{i+1}T00:00:00",
                finished_at=f"2024-01-0{i+1}T00:01:00",
                exit_code=i,
                duration_seconds=60.0,
            )
        )
    last = history.last_run("job")
    assert last is not None
    assert last.exit_code == 2


def test_persists_to_disk(history_file, history):
    history.record(
        HistoryEntry(
            job_name="sync",
            started_at="2024-06-01T10:00:00",
            finished_at="2024-06-01T10:02:00",
            exit_code=0,
            duration_seconds=120.0,
        )
    )
    reloaded = JobHistory(path=history_file)
    assert len(reloaded.get_for_job("sync")) == 1


def test_max_entries_trimmed(history):
    for i in range(MAX_HISTORY_ENTRIES + 10):
        history.record(
            HistoryEntry(
                job_name="job",
                started_at="2024-01-01T00:00:00",
                finished_at="2024-01-01T00:01:00",
                exit_code=0,
                duration_seconds=60.0,
            )
        )
    assert len(history.get_all()) == MAX_HISTORY_ENTRIES


def test_recorder_records_completed_run(history, completed_run):
    recorder = HistoryRecorder(history)
    recorder.record(completed_run)
    entry = history.last_run("backup")
    assert entry is not None
    assert entry.exit_code == 0
    assert entry.duration_seconds == pytest.approx(330.0)


def test_recorder_raises_on_incomplete_run(history):
    run = JobRun(job_name="nightly", started_at=datetime.now())
    recorder = HistoryRecorder(history)
    with pytest.raises(ValueError, match="incomplete"):
        recorder.record(run)


def test_entry_succeeded_false_on_nonzero(history):
    entry = HistoryEntry(
        job_name="job",
        started_at="2024-01-01T00:00:00",
        finished_at="2024-01-01T00:01:00",
        exit_code=1,
        duration_seconds=60.0,
    )
    assert not entry.succeeded()
