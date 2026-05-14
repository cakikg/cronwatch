"""Tests for cronwatch built-in notifiers."""

import logging
from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest

from cronwatch.alerts import Alert, AlertType
from cronwatch.notifiers import EmailNotifier, LogNotifier, SMTPConfig
from cronwatch.tracker import JobRun


@pytest.fixture
def smtp_config():
    return SMTPConfig(
        host="smtp.example.com",
        port=587,
        username="user",
        password="secret",
        from_addr="cronwatch@example.com",
        to_addrs=["ops@example.com"],
    )


@pytest.fixture
def failure_alert():
    run = JobRun(job_name="backup", started_at=datetime.utcnow())
    run.exit_code = 1
    run.finished_at = datetime.utcnow()
    return Alert(
        alert_type=AlertType.FAILURE,
        job_name="backup",
        message="Job exited with code 1",
        run=run,
    )


@pytest.fixture
def overrun_alert():
    return Alert(
        alert_type=AlertType.OVERRUN,
        job_name="report",
        message="Job exceeded max duration of 60s",
        run=None,
    )


class TestEmailNotifier:
    def test_sends_email_on_alert(self, smtp_config, failure_alert):
        notifier = EmailNotifier(smtp_config)
        mock_server = MagicMock()
        with patch("smtplib.SMTP") as mock_smtp_cls:
            mock_smtp_cls.return_value.__enter__.return_value = mock_server
            notifier(failure_alert)
        mock_server.sendmail.assert_called_once()

    def test_subject_contains_failure_tag(self, smtp_config, failure_alert):
        notifier = EmailNotifier(smtp_config)
        subject = notifier._build_subject(failure_alert)
        assert "FAILURE" in subject
        assert "backup" in subject

    def test_subject_contains_overrun_tag(self, smtp_config, overrun_alert):
        notifier = EmailNotifier(smtp_config)
        subject = notifier._build_subject(overrun_alert)
        assert "OVERRUN" in subject

    def test_body_contains_job_name(self, smtp_config, failure_alert):
        notifier = EmailNotifier(smtp_config)
        body = notifier._build_body(failure_alert)
        assert "backup" in body
        assert "1" in body  # exit code

    def test_skips_send_when_no_recipients(self, failure_alert, caplog):
        cfg = SMTPConfig(host="smtp.example.com", to_addrs=[])
        notifier = EmailNotifier(cfg)
        with caplog.at_level(logging.WARNING, logger="cronwatch.notifiers"):
            notifier(failure_alert)
        assert "no recipients" in caplog.text

    def test_logs_error_on_smtp_failure(self, smtp_config, failure_alert, caplog):
        notifier = EmailNotifier(smtp_config)
        with patch("smtplib.SMTP", side_effect=Exception("connection refused")):
            with caplog.at_level(logging.ERROR, logger="cronwatch.notifiers"):
                notifier(failure_alert)
        assert "Failed to send" in caplog.text


class TestLogNotifier:
    def test_logs_failure_alert(self, failure_alert, caplog):
        notifier = LogNotifier(level=logging.WARNING)
        with caplog.at_level(logging.WARNING, logger="cronwatch.notifiers"):
            notifier(failure_alert)
        assert "backup" in caplog.text
        assert "FAILURE" in caplog.text

    def test_logs_overrun_alert(self, overrun_alert, caplog):
        notifier = LogNotifier()
        with caplog.at_level(logging.WARNING, logger="cronwatch.notifiers"):
            notifier(overrun_alert)
        assert "report" in caplog.text
        assert "OVERRUN" in caplog.text
