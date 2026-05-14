"""Built-in notification handlers for cronwatch alerts."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from typing import Optional

from cronwatch.alerts import Alert, AlertType

logger = logging.getLogger(__name__)


@dataclass
class SMTPConfig:
    host: str
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    from_addr: str = "cronwatch@localhost"
    to_addrs: list = None

    def __post_init__(self):
        if self.to_addrs is None:
            self.to_addrs = []


class EmailNotifier:
    """Sends alert notifications via email."""

    def __init__(self, smtp_config: SMTPConfig):
        self.smtp_config = smtp_config

    def __call__(self, alert: Alert) -> None:
        cfg = self.smtp_config
        if not cfg.to_addrs:
            logger.warning("EmailNotifier: no recipients configured, skipping.")
            return

        subject = self._build_subject(alert)
        body = self._build_body(alert)

        msg = MIMEMultipart()
        msg["From"] = cfg.from_addr
        msg["To"] = ", ".join(cfg.to_addrs)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(cfg.host, cfg.port) as server:
                if cfg.use_tls:
                    server.starttls()
                if cfg.username and cfg.password:
                    server.login(cfg.username, cfg.password)
                server.sendmail(cfg.from_addr, cfg.to_addrs, msg.as_string())
            logger.info("Alert email sent for job '%s'", alert.job_name)
        except smtplib.SMTPException as exc:
            logger.error("Failed to send alert email: %s", exc)

    def _build_subject(self, alert: Alert) -> str:
        tag = "FAILURE" if alert.alert_type == AlertType.FAILURE else "OVERRUN"
        return f"[cronwatch] {tag}: {alert.job_name}"

    def _build_body(self, alert: Alert) -> str:
        lines = [
            f"Job:      {alert.job_name}",
            f"Type:     {alert.alert_type.value}",
            f"Message:  {alert.message}",
        ]
        if alert.run:
            run = alert.run
            lines += [
                f"Exit code: {run.exit_code}",
                f"Duration:  {run.duration():.2f}s" if run.is_complete() else "",
            ]
        return "\n".join(line for line in lines if line)


class LogNotifier:
    """Logs alerts using Python's logging module."""

    def __init__(self, level: int = logging.WARNING):
        self.level = level

    def __call__(self, alert: Alert) -> None:
        logger.log(
            self.level,
            "[%s] %s — %s",
            alert.alert_type.value.upper(),
            alert.job_name,
            alert.message,
        )
