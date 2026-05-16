"""Tests for cronwatch.escalation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cronwatch.alerts import Alert, AlertType
from cronwatch.escalation import AlertEscalator, EscalationConfig


@pytest.fixture()
def now(monkeypatch):
    _t = [0.0]

    def _clock():
        return _t[0]

    def _advance(seconds: float):
        _t[0] += seconds

    return _clock, _advance


@pytest.fixture()
def config():
    return EscalationConfig(grace_period=60.0, repeat_interval=120.0, max_escalations=2)


@pytest.fixture()
def handler():
    return MagicMock()


@pytest.fixture()
def escalator(config, handler, now):
    clock, _ = now
    return AlertEscalator(config=config, handler=handler, clock=clock)


def _alert(job_name: str = "backup") -> Alert:
    return Alert(job_name=job_name, alert_type=AlertType.FAILURE, message="fail")


def test_initial_call_fires_handler(escalator, handler):
    alert = _alert()
    escalator(alert)
    handler.assert_called_once_with(alert)


def test_tick_within_grace_does_not_escalate(escalator, handler, now):
    _, advance = now
    alert = _alert()
    escalator(alert)
    handler.reset_mock()
    advance(30.0)  # still within 60 s grace
    escalator.tick(alert)
    handler.assert_not_called()


def test_tick_after_grace_and_interval_escalates(escalator, handler, now):
    _, advance = now
    alert = _alert()
    escalator(alert)
    handler.reset_mock()
    advance(61.0)   # past grace
    advance(121.0)  # past repeat interval
    escalator.tick(alert)
    handler.assert_called_once_with(alert)


def test_escalation_respects_max(escalator, handler, now):
    _, advance = now
    alert = _alert()
    escalator(alert)
    handler.reset_mock()

    for _ in range(5):
        advance(200.0)  # past both grace and interval each time
        escalator.tick(alert)

    # max_escalations=2, so handler should only be called twice more
    assert handler.call_count == 2


def test_resolve_clears_state(escalator, handler, now):
    _, advance = now
    alert = _alert()
    escalator(alert)
    escalator.resolve("backup")
    handler.reset_mock()
    advance(300.0)
    escalator.tick(alert)  # state was cleared; should not escalate
    handler.assert_not_called()


def test_unknown_job_tick_is_noop(escalator, handler):
    escalator.tick(_alert("unknown"))
    handler.assert_not_called()
