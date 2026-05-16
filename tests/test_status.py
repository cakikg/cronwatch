"""Tests for cronwatch.status."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from cronwatch.status import JobStatus, StatusBuilder, StatusSnapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(next_run: datetime):
    entry = MagicMock()
    entry.next_run = next_run
    return entry


def _make_history_entry(finished_at: datetime, exit_code: int):
    he = MagicMock()
    he.finished_at = finished_at
    he.exit_code = exit_code
    return he


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def now():
    return datetime(2024, 6, 1, 12, 0, 0)


@pytest.fixture
def tracker():
    t = MagicMock()
    t.active_runs.return_value = []
    return t


@pytest.fixture
def recorder():
    return MagicMock()


@pytest.fixture
def scheduler(now):
    s = MagicMock()
    s.entries.return_value = [
        ("backup", _make_entry(now + timedelta(hours=1))),
        ("cleanup", _make_entry(now + timedelta(hours=2))),
    ]
    return s


@pytest.fixture
def builder(tracker, recorder, scheduler):
    return StatusBuilder(tracker=tracker, recorder=recorder, scheduler=scheduler)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_build_returns_snapshot(builder, recorder):
    recorder.last_run.return_value = None
    snap = builder.build()
    assert isinstance(snap, StatusSnapshot)
    assert len(snap.jobs) == 2


def test_job_names_match_scheduler(builder, recorder):
    recorder.last_run.return_value = None
    snap = builder.build()
    names = {j.name for j in snap.jobs}
    assert names == {"backup", "cleanup"}


def test_healthy_count_all_ok(builder, recorder, now):
    recorder.last_run.return_value = _make_history_entry(now, 0)
    snap = builder.build()
    assert snap.healthy_count == 2
    assert snap.failed_count == 0


def test_failed_count(builder, recorder, now):
    recorder.last_run.return_value = _make_history_entry(now, 1)
    snap = builder.build()
    assert snap.failed_count == 2


def test_running_job_detected(builder, recorder, tracker, now):
    run = MagicMock()
    run.job_name = "backup"
    tracker.active_runs.return_value = [run]
    recorder.last_run.return_value = None
    snap = builder.build()
    running = [j for j in snap.jobs if j.is_running]
    assert len(running) == 1
    assert running[0].name == "backup"
    assert snap.running_count == 1


def test_status_label_pending(builder, recorder):
    recorder.last_run.return_value = None
    snap = builder.build()
    assert all(j.status_label == "pending" for j in snap.jobs)


def test_status_label_failed(builder, recorder, now):
    recorder.last_run.return_value = _make_history_entry(now, 2)
    snap = builder.build()
    assert all(j.status_label == "failed" for j in snap.jobs)


def test_captured_at_is_recent(builder, recorder):
    recorder.last_run.return_value = None
    before = datetime.utcnow()
    snap = builder.build()
    after = datetime.utcnow()
    assert before <= snap.captured_at <= after
