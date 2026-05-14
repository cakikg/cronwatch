"""Tests for cronwatch.report and cronwatch.report_emitter."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from cronwatch.report import ReportBuilder
from cronwatch.report_emitter import ReportEmitter, file_handler, stdout_handler
from cronwatch.summary import CronwatchSummary, JobSummary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_summary(jobs: list[JobSummary] | None = None) -> CronwatchSummary:
    if jobs is None:
        jobs = [
            JobSummary(name="backup", total_runs=10, success_count=10, last_run=datetime(2024, 1, 1, 3, 0)),
            JobSummary(name="cleanup", total_runs=5, success_count=3, last_run=datetime(2024, 1, 1, 4, 0)),
            JobSummary(name="report", total_runs=0, success_count=0, last_run=None),
        ]
    return CronwatchSummary(jobs=jobs)


@pytest.fixture
def summary() -> CronwatchSummary:
    return _make_summary()


@pytest.fixture
def builder() -> ReportBuilder:
    return ReportBuilder()


@pytest.fixture
def emitter() -> ReportEmitter:
    return ReportEmitter()


# ---------------------------------------------------------------------------
# ReportBuilder tests
# ---------------------------------------------------------------------------


def test_report_contains_job_names(builder, summary):
    text = builder.build(summary)
    assert "backup" in text
    assert "cleanup" in text
    assert "report" in text


def test_report_shows_success_rate(builder, summary):
    text = builder.build(summary)
    assert "100%" in text   # backup
    assert "60%" in text    # cleanup


def test_report_shows_never_for_no_last_run(builder, summary):
    text = builder.build(summary)
    assert "never" in text


def test_report_footer_totals(builder, summary):
    text = builder.build(summary)
    assert "Total jobs : 3" in text


# ---------------------------------------------------------------------------
# ReportEmitter tests
# ---------------------------------------------------------------------------


def test_emit_calls_all_handlers(emitter, summary):
    h1, h2 = MagicMock(), MagicMock()
    emitter.register_handler(h1)
    emitter.register_handler(h2)
    emitter.emit(summary)
    h1.assert_called_once()
    h2.assert_called_once()


def test_emit_no_handlers_does_not_raise(emitter, summary):
    emitter.emit(summary)  # should not raise


def test_handler_exception_does_not_propagate(emitter, summary):
    bad = MagicMock(side_effect=RuntimeError("boom"))
    emitter.register_handler(bad)
    emitter.emit(summary)  # must not raise


def test_file_handler_writes_report(tmp_path, summary):
    out = tmp_path / "report.txt"
    handler = file_handler(str(out))
    builder = ReportBuilder()
    text = builder.build(summary)
    handler(text)
    content = out.read_text()
    assert "backup" in content
    assert "CronWatch Health Report" in content
