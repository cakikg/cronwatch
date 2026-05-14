"""Emits periodic reports via registered output channels."""

from __future__ import annotations

import logging
from typing import Callable, List

from cronwatch.report import ReportBuilder
from cronwatch.summary import CronwatchSummary

log = logging.getLogger(__name__)

OutputHandler = Callable[[str], None]


class ReportEmitter:
    """Renders a CronwatchSummary and forwards the text to all handlers."""

    def __init__(self, builder: ReportBuilder | None = None) -> None:
        self._builder: ReportBuilder = builder or ReportBuilder()
        self._handlers: List[OutputHandler] = []

    # ------------------------------------------------------------------
    def register_handler(self, handler: OutputHandler) -> None:
        """Add an output channel (e.g. print, email, file write)."""
        self._handlers.append(handler)

    def emit(self, summary: CronwatchSummary) -> None:
        """Build the report and send it to every registered handler."""
        if not self._handlers:
            log.debug("ReportEmitter: no handlers registered, skipping emit")
            return
        report_text = self._builder.build(summary)
        for handler in self._handlers:
            try:
                handler(report_text)
            except Exception:
                log.exception("ReportEmitter: handler %r raised an exception", handler)


def stdout_handler(text: str) -> None:
    """Simple handler that prints the report to stdout."""
    print(text)


def file_handler(path: str) -> OutputHandler:
    """Factory that returns a handler writing the report to *path*."""

    def _write(text: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.write("\n")

    return _write
