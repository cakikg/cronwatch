"""Build a HistoryPruner from application config."""

from __future__ import annotations

from cronwatch.config import CronwatchConfig
from cronwatch.history import JobHistory
from cronwatch.retention import HistoryPruner, RetentionPolicy

_DEFAULT_MAX_AGE_DAYS = 30
_DEFAULT_MAX_ENTRIES = 100


def build_pruner(config: CronwatchConfig, history: JobHistory) -> HistoryPruner:
    """Construct a HistoryPruner using retention settings from *config*."""
    retention_cfg = getattr(config, "retention", None) or {}

    max_age = int(retention_cfg.get("max_age_days", _DEFAULT_MAX_AGE_DAYS))
    max_entries = int(retention_cfg.get("max_entries_per_job", _DEFAULT_MAX_ENTRIES))

    policy = RetentionPolicy(
        max_age_days=max_age,
        max_entries_per_job=max_entries,
    )
    return HistoryPruner(history=history, policy=policy)
