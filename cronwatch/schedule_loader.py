"""Utility that builds a Scheduler from a CronwatchConfig."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from cronwatch.config import CronwatchConfig
from cronwatch.scheduler import Scheduler


def build_scheduler(
    config: CronwatchConfig,
    reference: Optional[datetime] = None,
) -> Scheduler:
    """Create and populate a :class:`Scheduler` from *config*.

    Parameters
    ----------
    config:
        Parsed application configuration.
    reference:
        The datetime used as the base for computing the first ``next_run``
        of every job.  Defaults to the current UTC time.

    Returns
    -------
    Scheduler
        A fully populated scheduler instance.
    """
    if reference is None:
        reference = datetime.now(tz=timezone.utc)

    scheduler = Scheduler()
    for job in config.jobs:
        scheduler.register(job, reference=reference)
    return scheduler
