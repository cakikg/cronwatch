"""Tests for cronwatch.replay_factory.build_replay_buffer."""
from __future__ import annotations

import pytest

from cronwatch.replay import AlertReplayBuffer
from cronwatch.replay_factory import build_replay_buffer


class _Cfg:
    def __init__(self, size=None):
        if size is not None:
            self.replay_buffer_size = size


def test_returns_replay_buffer():
    buf = build_replay_buffer()
    assert isinstance(buf, AlertReplayBuffer)


def test_default_max_size():
    buf = build_replay_buffer()
    assert buf.config.max_size == 50


def test_config_sets_max_size():
    buf = build_replay_buffer(_Cfg(size=10))
    assert buf.config.max_size == 10


def test_no_config_uses_default():
    buf = build_replay_buffer(None)
    assert buf.config.max_size == 50


def test_invalid_size_falls_back_to_default():
    cfg = _Cfg()
    cfg.replay_buffer_size = "bad"
    buf = build_replay_buffer(cfg)
    assert buf.config.max_size == 50


def test_config_without_attribute_uses_default():
    buf = build_replay_buffer(_Cfg())  # no replay_buffer_size attr
    assert buf.config.max_size == 50
