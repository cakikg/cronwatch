"""Tests for cronwatch.audit."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwatch.audit import AuditEvent, AuditEventType, AuditLog


@pytest.fixture
def audit_path(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


@pytest.fixture
def audit_log(audit_path: Path) -> AuditLog:
    return AuditLog(path=audit_path)


def _make_event(
    event_type: AuditEventType = AuditEventType.JOB_STARTED,
    job_name: str = "backup",
) -> AuditEvent:
    return AuditEvent(
        event_type=event_type,
        job_name=job_name,
        timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        details={"exit_code": 0},
    )


def test_record_writes_json_line(audit_log: AuditLog, audit_path: Path) -> None:
    event = _make_event()
    audit_log.record(event)
    lines = audit_path.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["event_type"] == "job_started"
    assert data["job_name"] == "backup"


def test_record_appends_multiple_events(audit_log: AuditLog, audit_path: Path) -> None:
    audit_log.record(_make_event(AuditEventType.JOB_STARTED))
    audit_log.record(_make_event(AuditEventType.JOB_FINISHED))
    lines = audit_path.read_text().strip().splitlines()
    assert len(lines) == 2


def test_read_all_returns_empty_when_no_file(tmp_path: Path) -> None:
    log = AuditLog(path=tmp_path / "nonexistent.jsonl")
    assert log.read_all() == []


def test_read_all_round_trips_event(audit_log: AuditLog) -> None:
    original = _make_event(AuditEventType.JOB_FAILED, "cleanup")
    audit_log.record(original)
    events = audit_log.read_all()
    assert len(events) == 1
    evt = events[0]
    assert evt.event_type == AuditEventType.JOB_FAILED
    assert evt.job_name == "cleanup"
    assert evt.details == {"exit_code": 0}


def test_read_all_preserves_order(audit_log: AuditLog) -> None:
    types = [
        AuditEventType.DAEMON_STARTED,
        AuditEventType.JOB_STARTED,
        AuditEventType.JOB_FINISHED,
        AuditEventType.DAEMON_STOPPED,
    ]
    for t in types:
        audit_log.record(_make_event(t))
    events = audit_log.read_all()
    assert [e.event_type for e in events] == types


def test_creates_parent_directories(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "audit.jsonl"
    log = AuditLog(path=nested)
    log.record(_make_event())
    assert nested.exists()


def test_to_dict_contains_required_keys() -> None:
    event = _make_event()
    d = event.to_dict()
    assert set(d.keys()) == {"event_type", "job_name", "timestamp", "details"}
