"""Tests for cronwatch.schedule_loader."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cronwatch.config import CronwatchConfig, JobConfig
from cronwatch.schedule_loader import build_scheduler


@pytest.fixture()
def sample_config() -> CronwatchConfig:
    return CronwatchConfig(
        jobs=[
            JobConfig(name="hourly_report", schedule="0 * * * *", timeout=60),
            JobConfig(name="daily_backup", schedule="0 2 * * *", timeout=300),
        ]
    )


def test_build_scheduler_registers_all_jobs(sample_config: CronwatchConfig) -> None:
    ref = datetime(2024, 3, 15, 8, 0, 0, tzinfo=timezone.utc)
    scheduler = build_scheduler(sample_config, reference=ref)
    assert len(scheduler) == 2


def test_build_scheduler_entries_have_correct_names(sample_config: CronwatchConfig) -> None:
    ref = datetime(2024, 3, 15, 8, 0, 0, tzinfo=timezone.utc)
    scheduler = build_scheduler(sample_config, reference=ref)
    assert scheduler.get_entry("hourly_report") is not None
    assert scheduler.get_entry("daily_backup") is not None


def test_build_scheduler_next_run_after_reference(sample_config: CronwatchConfig) -> None:
    ref = datetime(2024, 3, 15, 8, 0, 0, tzinfo=timezone.utc)
    scheduler = build_scheduler(sample_config, reference=ref)
    for name in ("hourly_report", "daily_backup"):
        entry = scheduler.get_entry(name)
        assert entry.next_run > ref


def test_build_scheduler_empty_config() -> None:
    config = CronwatchConfig(jobs=[])
    ref = datetime(2024, 1, 1, tzinfo=timezone.utc)
    scheduler = build_scheduler(config, reference=ref)
    assert len(scheduler) == 0


def test_build_scheduler_uses_utc_default_reference(sample_config: CronwatchConfig) -> None:
    """build_scheduler should not raise when reference is omitted."""
    scheduler = build_scheduler(sample_config)
    assert len(scheduler) == 2
