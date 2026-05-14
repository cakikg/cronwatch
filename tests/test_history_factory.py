"""Tests for cronwatch.history_factory."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from cronwatch.history import DEFAULT_HISTORY_FILE, JobHistory
from cronwatch.history_factory import build_history, build_recorder
from cronwatch.history_recorder import HistoryRecorder


class _FakeConfig:
    def __init__(self, history_file=None, jobs=None):
        self.history_file = history_file
        self.jobs = jobs or []


def test_build_history_uses_config_path(tmp_path):
    path = str(tmp_path / "custom.json")
    cfg = _FakeConfig(history_file=path)
    h = build_history(cfg)
    assert isinstance(h, JobHistory)
    assert h._path.name == "custom.json"


def test_build_history_falls_back_to_env(tmp_path):
    path = str(tmp_path / "env.json")
    cfg = _FakeConfig(history_file=None)
    with patch.dict(os.environ, {"CRONWATCH_HISTORY_FILE": path}):
        h = build_history(cfg)
    assert str(h._path) == path


def test_build_history_falls_back_to_default(tmp_path):
    cfg = _FakeConfig(history_file=None)
    env = {k: v for k, v in os.environ.items() if k != "CRONWATCH_HISTORY_FILE"}
    with patch.dict(os.environ, env, clear=True):
        h = build_history(cfg)
    assert str(h._path) == DEFAULT_HISTORY_FILE


def test_build_recorder_returns_recorder(tmp_path):
    path = str(tmp_path / "rec.json")
    cfg = _FakeConfig(history_file=path)
    recorder = build_recorder(cfg)
    assert isinstance(recorder, HistoryRecorder)
