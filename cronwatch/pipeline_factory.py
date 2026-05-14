"""Factory that assembles an ExecutionPipeline from a CronwatchConfig."""

from cronwatch.alerts import AlertDispatcher
from cronwatch.config import CronwatchConfig
from cronwatch.notifier_factory import build_notifiers
from cronwatch.pipeline import ExecutionPipeline
from cronwatch.runner import JobRunner
from cronwatch.tracker import JobTracker


def build_pipeline(config: CronwatchConfig) -> ExecutionPipeline:
    """Create a fully wired :class:`ExecutionPipeline` from *config*."""
    tracker = JobTracker(config.jobs)

    dispatcher = AlertDispatcher()
    for notifier in build_notifiers(config):
        dispatcher.register_handler(notifier)

    runner = JobRunner(tracker)

    return ExecutionPipeline(
        runner=runner,
        tracker=tracker,
        dispatcher=dispatcher,
        jobs=config.jobs,
    )
