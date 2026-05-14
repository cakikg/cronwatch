"""Tests for the daemon wiring and startup logic."""

import signal
from unittest.mock import MagicMock, patch, call

import pytest

from cronwatch.daemon import build_daemon, run, configure_logging


@pytest.fixture()
def config_path(tmp_path):
    cfg = tmp_path / "cronwatch.yaml"
    cfg.write_text(
        "jobs:\n"
        "  - name: nightly-backup\n"
        "    schedule: '0 2 * * *'\n"
        "    command: /usr/bin/backup.sh\n"
        "    max_duration: 3600\n"
    )
    return str(cfg)


def test_build_daemon_returns_monitor(config_path):
    from cronwatch.monitor import CronMonitor

    with patch("cronwatch.daemon.build_notifiers", return_value=[]):
        monitor = build_daemon(config_path)
    assert isinstance(monitor, CronMonitor)


def test_build_daemon_registers_notifiers(config_path):
    mock_notifier = MagicMock()
    with patch("cronwatch.daemon.build_notifiers", return_value=[mock_notifier]):
        monitor = build_daemon(config_path)

    # Dispatcher should have our notifier registered; triggering a dispatch calls it
    from cronwatch.alerts import Alert, AlertType
    from datetime import datetime

    alert = Alert(
        alert_type=AlertType.FAILURE,
        job_name="nightly-backup",
        message="test",
        timestamp=datetime.utcnow(),
        run=MagicMock(),
    )
    monitor.dispatcher.dispatch(alert)
    mock_notifier.assert_called_once_with(alert)


def test_run_exits_on_missing_config(tmp_path):
    missing = str(tmp_path / "nonexistent.yaml")
    with pytest.raises(SystemExit) as exc_info:
        run(missing)
    assert exc_info.value.code == 1


def test_run_starts_and_stops_on_sigint(config_path):
    with patch("cronwatch.daemon.build_notifiers", return_value=[]):
        with patch("cronwatch.daemon.CronMonitor.start") as mock_start:
            with patch("cronwatch.daemon.CronMonitor.stop") as mock_stop:
                with patch("signal.signal") as mock_signal:
                    run(config_path, log_level="WARNING")

    mock_start.assert_called_once()
    # Two signal handlers registered: SIGTERM and SIGINT
    assert mock_signal.call_count == 2
    registered_signals = {c.args[0] for c in mock_signal.call_args_list}
    assert signal.SIGTERM in registered_signals
    assert signal.SIGINT in registered_signals


def test_configure_logging_sets_level():
    import logging
    configure_logging("DEBUG")
    assert logging.getLogger().level == logging.DEBUG
    configure_logging("INFO")
