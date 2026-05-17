"""Tests for cronwatch.replay.AlertReplayBuffer."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from cronwatch.alerts import Alert, AlertType
from cronwatch.replay import AlertReplayBuffer, ReplayConfig


def _alert(name: str = "job1") -> Alert:
    return Alert(
        alert_type=AlertType.FAILURE,
        job_name=name,
        message=f"{name} failed",
        timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture
def buf() -> AlertReplayBuffer:
    return AlertReplayBuffer(config=ReplayConfig(max_size=5))


def test_record_stores_alert(buf):
    a = _alert()
    buf.record(a)
    assert len(buf) == 1
    assert buf.buffered[0] is a


def test_record_forwards_to_handlers(buf):
    handler = MagicMock()
    buf.register_handler(handler, replay=False)
    a = _alert()
    buf.record(a)
    handler.assert_called_once_with(a)


def test_register_replays_buffered_alerts(buf):
    a1, a2 = _alert("j1"), _alert("j2")
    buf.record(a1)
    buf.record(a2)
    handler = MagicMock()
    buf.register_handler(handler, replay=True)
    assert handler.call_count == 2
    handler.assert_any_call(a1)
    handler.assert_any_call(a2)


def test_register_no_replay(buf):
    buf.record(_alert())
    handler = MagicMock()
    buf.register_handler(handler, replay=False)
    handler.assert_not_called()


def test_max_size_evicts_oldest(buf):
    for i in range(6):
        buf.record(_alert(f"job{i}"))
    assert len(buf) == 5
    assert buf.buffered[0].job_name == "job1"


def test_clear_empties_buffer(buf):
    buf.record(_alert())
    buf.clear()
    assert len(buf) == 0


def test_new_handler_receives_future_alerts_after_replay(buf):
    old = _alert("old")
    buf.record(old)
    handler = MagicMock()
    buf.register_handler(handler, replay=True)
    new = _alert("new")
    buf.record(new)
    assert handler.call_count == 2
    handler.assert_called_with(new)
