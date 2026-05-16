"""Factory helpers for constructing a Watchdog from project components."""

from cronwatch.tracker import JobTracker
from cronwatch.alerts import AlertDispatcher
from cronwatch.watchdog import Watchdog, WatchdogConfig
from cronwatch.config import CronwatchConfig


def build_watchdog(
    config: CronwatchConfig,
    tracker: JobTracker,
    dispatcher: AlertDispatcher,
) -> Watchdog:
    """Build a Watchdog wired to the given tracker and dispatcher.

    Reads ``watchdog_poll_interval`` from the config's ``extra`` dict when
    present, falling back to the default poll interval.
    """
    poll_interval: float = WatchdogConfig.poll_interval

    extra = getattr(config, "extra", {}) or {}
    if "watchdog_poll_interval" in extra:
        try:
            poll_interval = float(extra["watchdog_poll_interval"])
        except (TypeError, ValueError):
            pass

    watchdog_config = WatchdogConfig(poll_interval=poll_interval)
    return Watchdog(tracker=tracker, dispatcher=dispatcher, config=watchdog_config)
