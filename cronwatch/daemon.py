"""Daemon entry point that wires all components together and runs the monitor loop."""

import logging
import signal
import sys
from pathlib import Path

from cronwatch.config import load_config
from cronwatch.notifier_factory import build_notifiers
from cronwatch.pipeline_factory import build_pipeline
from cronwatch.schedule_loader import build_scheduler
from cronwatch.tracker import JobTracker
from cronwatch.alerts import AlertDispatcher
from cronwatch.monitor import CronMonitor

logger = logging.getLogger(__name__)


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=getattr(logging, level.upper(), logging.INFO),
    )


def build_daemon(config_path: str) -> CronMonitor:
    """Construct a fully wired CronMonitor from a config file path."""
    config = load_config(config_path)

    tracker = JobTracker()
    dispatcher = AlertDispatcher()

    for notifier in build_notifiers(config):
        dispatcher.register_handler(notifier)

    scheduler = build_scheduler(config)
    pipeline = build_pipeline(config, tracker, dispatcher)

    monitor = CronMonitor(
        config=config,
        scheduler=scheduler,
        pipeline=pipeline,
        tracker=tracker,
        dispatcher=dispatcher,
    )
    return monitor


def run(config_path: str, log_level: str = "INFO") -> None:
    """Start the cronwatch daemon, blocking until a termination signal is received."""
    configure_logging(log_level)
    logger.info("Starting cronwatch daemon with config: %s", config_path)

    if not Path(config_path).exists():
        logger.error("Config file not found: %s", config_path)
        sys.exit(1)

    monitor = build_daemon(config_path)

    def _shutdown(signum, frame):  # noqa: ANN001
        logger.info("Received signal %s, shutting down...", signum)
        monitor.stop()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        monitor.start()
    except Exception as exc:  # pragma: no cover
        logger.exception("Daemon crashed: %s", exc)
        sys.exit(1)
    finally:
        logger.info("cronwatch daemon stopped.")
