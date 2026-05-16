"""Tests for cronwatch.audit_factory."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from cronwatch.audit import AuditLog
from cronwatch.audit_factory import _DEFAULT_AUDIT_PATH, _ENV_VAR, build_audit_log


class _ConfigWithPath:
    def __init__(self, path: Path) -> None:
        self.audit_log_path = path


class _ConfigWithoutPath:
    """Simulates a CronwatchConfig that has no audit_log_path attribute."""


def test_build_uses_config_path(tmp_path: Path) -> None:
    expected = tmp_path / "custom_audit.jsonl"
    config = _ConfigWithPath(expected)
    log = build_audit_log(config)  # type: ignore[arg-type]
    assert isinstance(log, AuditLog)
    assert log._path == expected


def test_build_falls_back_to_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_path = tmp_path / "env_audit.jsonl"
    monkeypatch.setenv(_ENV_VAR, str(env_path))
    log = build_audit_log(_ConfigWithoutPath())  # type: ignore[arg-type]
    assert log._path == env_path


def test_build_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_ENV_VAR, raising=False)
    log = build_audit_log(_ConfigWithoutPath())  # type: ignore[arg-type]
    assert log._path == _DEFAULT_AUDIT_PATH


def test_env_takes_priority_over_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_path = tmp_path / "priority.jsonl"
    monkeypatch.setenv(_ENV_VAR, str(env_path))
    log = build_audit_log(_ConfigWithoutPath())  # type: ignore[arg-type]
    assert log._path != _DEFAULT_AUDIT_PATH
    assert log._path == env_path
