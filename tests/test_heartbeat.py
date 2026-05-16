"""Tests for cronwatch.heartbeat and cronwatch.heartbeat_factory."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.heartbeat import Heartbeat, HeartbeatConfig
from cronwatch.heartbeat_factory import build_heartbeat


@pytest.fixture
def heartbeat_path(tmp_path: Path) -> Path:
    return tmp_path / "heartbeat"


@pytest.fixture
def hb_config(heartbeat_path: Path) -> HeartbeatConfig:
    return HeartbeatConfig(path=heartbeat_path, interval_seconds=1.0)


@pytest.fixture
def fixed_clock():
    return lambda: 1_700_000_000.0


@pytest.fixture
def hb(hb_config: HeartbeatConfig, fixed_clock) -> Heartbeat:
    return Heartbeat(hb_config, clock=fixed_clock)


class TestHeartbeat:
    def test_beat_writes_timestamp(self, hb: Heartbeat, heartbeat_path: Path, fixed_clock):
        hb.beat()
        assert heartbeat_path.exists()
        assert float(heartbeat_path.read_text()) == fixed_clock()

    def test_last_beat_returns_none_before_first_beat(self, hb: Heartbeat):
        assert hb.last_beat() is None

    def test_last_beat_returns_written_timestamp(self, hb: Heartbeat, fixed_clock):
        hb.beat()
        assert hb.last_beat() == fixed_clock()

    def test_is_alive_true_when_recent(self, hb: Heartbeat):
        hb.beat()
        assert hb.is_alive(max_age_seconds=10.0)

    def test_is_alive_false_when_stale(self, hb_config: HeartbeatConfig):
        stale_time = time.time() - 999
        hb_config.path.parent.mkdir(parents=True, exist_ok=True)
        hb_config.path.write_text(str(stale_time))
        hb = Heartbeat(hb_config)
        assert not hb.is_alive(max_age_seconds=1.0)

    def test_is_alive_false_when_no_file(self, hb: Heartbeat):
        assert not hb.is_alive()

    def test_start_and_stop_do_not_raise(self, hb: Heartbeat):
        hb.start()
        hb.stop()

    def test_beat_creates_parent_dirs(self, tmp_path: Path, fixed_clock):
        deep_path = tmp_path / "a" / "b" / "c" / "heartbeat"
        cfg = HeartbeatConfig(path=deep_path, interval_seconds=1.0)
        hb = Heartbeat(cfg, clock=fixed_clock)
        hb.beat()
        assert deep_path.exists()


class TestHeartbeatFactory:
    def test_build_heartbeat_returns_instance(self, tmp_path: Path):
        hb = build_heartbeat()
        assert isinstance(hb, Heartbeat)

    def test_build_heartbeat_uses_env_path(self, tmp_path: Path, monkeypatch):
        expected = str(tmp_path / "hb")
        monkeypatch.setenv("CRONWATCH_HEARTBEAT_PATH", expected)
        hb = build_heartbeat()
        assert hb._config.path == Path(expected)

    def test_build_heartbeat_uses_env_interval(self, monkeypatch):
        monkeypatch.setenv("CRONWATCH_HEARTBEAT_INTERVAL", "30")
        hb = build_heartbeat()
        assert hb._config.interval_seconds == 30.0

    def test_build_heartbeat_uses_config_object(self, tmp_path: Path):
        class FakeConfig:
            heartbeat_path = str(tmp_path / "custom_hb")
            heartbeat_interval = 45.0

        hb = build_heartbeat(FakeConfig())
        assert hb._config.path == Path(FakeConfig.heartbeat_path)
        assert hb._config.interval_seconds == 45.0
