"""Tests for the circuit breaker alert handler wrapper."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from cronwatch.alerts import Alert, AlertType
from cronwatch.circuit_breaker import BreakerState, CircuitBreaker, CircuitBreakerConfig


_NOW = 1_000.0


@pytest.fixture()
def clock():
    t = [_NOW]
    return lambda: t[0], t


@pytest.fixture()
def config():
    return CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30.0, success_threshold=2)


@pytest.fixture()
def handler():
    return MagicMock()


@pytest.fixture()
def breaker(handler, config, clock):
    fn, _ = clock
    return CircuitBreaker(handler, config, clock=fn)


@pytest.fixture()
def alert():
    return Alert(alert_type=AlertType.FAILURE, job_name="backup", message="failed")


def test_initial_state_is_closed(breaker):
    assert breaker.state == BreakerState.CLOSED


def test_passes_alert_when_closed(breaker, handler, alert):
    breaker(alert)
    handler.assert_called_once_with(alert)


def test_opens_after_threshold_failures(breaker, handler, alert, config):
    handler.side_effect = RuntimeError("smtp down")
    for _ in range(config.failure_threshold):
        with pytest.raises(RuntimeError):
            breaker(alert)
    assert breaker.state == BreakerState.OPEN


def test_suppresses_alert_when_open(breaker, handler, alert, config):
    handler.side_effect = RuntimeError("smtp down")
    for _ in range(config.failure_threshold):
        with pytest.raises(RuntimeError):
            breaker(alert)
    handler.reset_mock(side_effect=True)
    breaker(alert)  # Should be suppressed — no call, no exception.
    handler.assert_not_called()


def test_transitions_to_half_open_after_timeout(breaker, handler, alert, config, clock):
    _, t = clock
    handler.side_effect = RuntimeError()
    for _ in range(config.failure_threshold):
        with pytest.raises(RuntimeError):
            breaker(alert)
    t[0] += config.recovery_timeout + 1
    handler.side_effect = None
    breaker(alert)
    # After one success in HALF_OPEN with success_threshold=2, still HALF_OPEN.
    assert breaker.state == BreakerState.HALF_OPEN


def test_closes_after_enough_successes_in_half_open(breaker, handler, alert, config, clock):
    _, t = clock
    handler.side_effect = RuntimeError()
    for _ in range(config.failure_threshold):
        with pytest.raises(RuntimeError):
            breaker(alert)
    t[0] += config.recovery_timeout + 1
    handler.side_effect = None
    for _ in range(config.success_threshold):
        breaker(alert)
    assert breaker.state == BreakerState.CLOSED


def test_reset_returns_to_closed(breaker, handler, alert, config):
    handler.side_effect = RuntimeError()
    for _ in range(config.failure_threshold):
        with pytest.raises(RuntimeError):
            breaker(alert)
    assert breaker.state == BreakerState.OPEN
    breaker.reset()
    assert breaker.state == BreakerState.CLOSED
