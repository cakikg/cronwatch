"""Tests for cronwatch.scheduler."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cronwatch.config import JobConfig
from cronwatch.scheduler import Scheduler, ScheduleEntry


@pytest.fixture()
def job_config() -> JobConfig:
    return JobConfig(name="backup", schedule="*/5 * * * *", timeout=120)


@pytest.fixture()
def scheduler(job_config: JobConfig) -> Scheduler:
    s = Scheduler()
    reference = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    s.register(job_config, reference=reference)
    return s


def test_register_creates_entry(scheduler: Scheduler, job_config: JobConfig) -> None:
    assert len(scheduler) == 1
    entry = scheduler.get_entry("backup")
    assert entry is not None
    assert entry.job is job_config


def test_next_run_is_in_future(scheduler: Scheduler) -> None:
    reference = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    entry = scheduler.get_entry("backup")
    assert entry.next_run > reference


def test_due_jobs_returns_overdue_entries(scheduler: Scheduler) -> None:
    far_future = datetime(2099, 1, 1, tzinfo=timezone.utc)
    due = scheduler.due_jobs(now=far_future)
    assert len(due) == 1
    assert due[0].job.name == "backup"


def test_due_jobs_empty_before_next_run(scheduler: Scheduler) -> None:
    past = datetime(2000, 1, 1, tzinfo=timezone.utc)
    due = scheduler.due_jobs(now=past)
    assert due == []


def test_advance_moves_next_run_forward(scheduler: Scheduler) -> None:
    entry = scheduler.get_entry("backup")
    original_next = entry.next_run
    entry.advance()
    assert entry.next_run > original_next


def test_is_due_true_when_now_equals_next_run() -> None:
    job = JobConfig(name="test", schedule="0 * * * *", timeout=60)
    now = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    entry = ScheduleEntry(job=job, next_run=now, last_checked=now)
    assert entry.is_due(now=now) is True


def test_is_due_false_before_next_run() -> None:
    job = JobConfig(name="test", schedule="0 * * * *", timeout=60)
    future = datetime(2024, 6, 1, 11, 0, 0, tzinfo=timezone.utc)
    now = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    entry = ScheduleEntry(job=job, next_run=future, last_checked=now)
    assert entry.is_due(now=now) is False


def test_register_multiple_jobs() -> None:
    s = Scheduler()
    ref = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    for name, sched in [("job_a", "*/10 * * * *"), ("job_b", "0 9 * * *")]:
        s.register(JobConfig(name=name, schedule=sched, timeout=30), reference=ref)
    assert len(s) == 2
    assert s.get_entry("job_a") is not None
    assert s.get_entry("job_b") is not None
