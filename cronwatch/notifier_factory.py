"""Factory for building notifiers from CronwatchConfig."""

import logging
from typing import List, Callable

from cronwatch.alerts import Alert
from cronwatch.notifiers import EmailNotifier, LogNotifier, SMTPConfig

logger = logging.getLogger(__name__)


def build_notifiers(config: dict) -> List[Callable[[Alert], None]]:
    """Instantiate notifiers based on the 'notifiers' section of config.

    Expected config structure::

        notifiers:
          - type: log
            level: warning
          - type: email
            host: smtp.example.com
            port: 587
            username: user
            password: secret
            from_addr: cronwatch@example.com
            to_addrs:
              - ops@example.com

    Returns a list of callables suitable for use with AlertDispatcher.
    """
    handlers: List[Callable[[Alert], None]] = []
    notifier_cfgs = config.get("notifiers", [])

    if not notifier_cfgs:
        logger.info("No notifiers configured; using default log notifier.")
        handlers.append(LogNotifier())
        return handlers

    for entry in notifier_cfgs:
        ntype = entry.get("type", "").lower()

        if ntype == "log":
            level_name = entry.get("level", "warning").upper()
            level = getattr(logging, level_name, logging.WARNING)
            handlers.append(LogNotifier(level=level))
            logger.debug("Registered LogNotifier at level %s", level_name)

        elif ntype == "email":
            smtp_cfg = SMTPConfig(
                host=entry["host"],
                port=int(entry.get("port", 587)),
                username=entry.get("username"),
                password=entry.get("password"),
                use_tls=bool(entry.get("use_tls", True)),
                from_addr=entry.get("from_addr", "cronwatch@localhost"),
                to_addrs=entry.get("to_addrs", []),
            )
            handlers.append(EmailNotifier(smtp_cfg))
            logger.debug("Registered EmailNotifier → %s", smtp_cfg.host)

        else:
            logger.warning("Unknown notifier type '%s'; skipping.", ntype)

    return handlers
