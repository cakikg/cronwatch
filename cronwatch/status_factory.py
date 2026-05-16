"""Wires together the StatusBuilder from application components."""

from cronwatch.config import CronwatchConfig
from cronwatch.tracker import JobTracker
from cronwatch.history_recorder import HistoryRecorder
from cronwatch.scheduler import Scheduler
from cronwatch.status import StatusBuilder


def build_status_builder(
    config: CronwatchConfig,
    tracker: JobTracker,
    recorder: HistoryRecorder,
    scheduler: Scheduler,
) -> StatusBuilder:
    """Return a StatusBuilder wired to the live application components."""
    return StatusBuilder(
        tracker=tracker,
        recorder=recorder,
        scheduler=scheduler,
    )
