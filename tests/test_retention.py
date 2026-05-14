"""Tests for history retention / pruning."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from cronwatch.retention import HistoryPruner, RetentionPolicy
from cronwatch.history import HistoryEntry


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(days_ago: int, job: str = "backup") -> HistoryEntry:
    started = NOW - timedelta(days=days_ago)
    finished = started + timedelta(minutes=1)
    return HistoryEntry(
        job_name=job,
        started_at=started,
        finished_at=finished,
        exit_code=0,
    )


@pytest.fixture
def policy() -> RetentionPolicy:
    return RetentionPolicy(max_age_days=7, max_entries_per_job=3)


def _make_history(entries_by_job: dict) -> MagicMock:
    history = MagicMock()
    history.job_names.return_value = list(entries_by_job.keys())
    history.get.side_effect = lambda name: entries_by_job[name]
    history.replace = MagicMock()
    return history


class TestRetentionPolicy:
    def test_fresh_entry_not_expired(self, policy):
        entry = _entry(days_ago=1)
        assert not policy.is_expired(entry, now=NOW)

    def test_old_entry_is_expired(self, policy):
        entry = _entry(days_ago=10)
        assert policy.is_expired(entry, now=NOW)

    def test_boundary_entry_is_expired(self, policy):
        # Exactly at cutoff is considered expired
        entry = _entry(days_ago=7)
        assert policy.is_expired(entry, now=NOW)


class TestHistoryPruner:
    def test_removes_expired_entries(self, policy):
        entries = [_entry(1), _entry(5), _entry(10), _entry(20)]
        history = _make_history({"backup": entries})
        pruner = HistoryPruner(history, policy)

        removed = pruner.prune(now=NOW)

        assert removed == 2
        kept = history.replace.call_args[0][1]
        assert all(not policy.is_expired(e, NOW) for e in kept)

    def test_enforces_max_entries(self, policy):
        # 4 fresh entries but max is 3 — oldest should be dropped
        entries = [_entry(i) for i in range(4, 0, -1)]  # 4,3,2,1 days ago
        history = _make_history({"backup": entries})
        pruner = HistoryPruner(history, policy)

        removed = pruner.prune(now=NOW)

        assert removed == 1
        kept = history.replace.call_args[0][1]
        assert len(kept) == 3

    def test_no_entries_removed_when_all_fresh(self, policy):
        entries = [_entry(1), _entry(2)]
        history = _make_history({"backup": entries})
        pruner = HistoryPruner(history, policy)

        removed = pruner.prune(now=NOW)

        assert removed == 0

    def test_prune_multiple_jobs(self, policy):
        history = _make_history({
            "backup": [_entry(1, "backup"), _entry(15, "backup")],
            "sync": [_entry(2, "sync"), _entry(3, "sync")],
        })
        pruner = HistoryPruner(history, policy)

        removed = pruner.prune(now=NOW)

        assert removed == 1  # one expired in "backup"
