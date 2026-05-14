"""Factory helpers for building history-related objects."""

from __future__ import annotations

import os

from cronwatch.config import CronwatchConfig
from cronwatch.history import DEFAULT_HISTORY_FILE, JobHistory
from cronwatch.history_recorder import HistoryRecorder


def build_history(config: CronwatchConfig) -> JobHistory:
    """Return a JobHistory using the path from config or the default."""
    path = getattr(config, "history_file", None) or os.environ.get(
        "CRONWATCH_HISTORY_FILE", DEFAULT_HISTORY_FILE
    )
    return JobHistory(path=path)


def build_recorder(config: CronwatchConfig) -> HistoryRecorder:
    history = build_history(config)
    return HistoryRecorder(history)
