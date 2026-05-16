"""Factory for building an AuditLog from CronwatchConfig."""
from __future__ import annotations

import os
from pathlib import Path

from cronwatch.audit import AuditLog
from cronwatch.config import CronwatchConfig

_DEFAULT_AUDIT_PATH = Path("/var/log/cronwatch/audit.jsonl")
_ENV_VAR = "CRONWATCH_AUDIT_LOG"


def build_audit_log(config: CronwatchConfig) -> AuditLog:
    """Return an AuditLog whose path is resolved from (in priority order):

    1. ``config.audit_log_path`` (if the config exposes such an attribute)
    2. The ``CRONWATCH_AUDIT_LOG`` environment variable
    3. The hard-coded default ``/var/log/cronwatch/audit.jsonl``
    """
    path: Path | None = getattr(config, "audit_log_path", None)
    if path is None:
        env_val = os.environ.get(_ENV_VAR)
        path = Path(env_val) if env_val else _DEFAULT_AUDIT_PATH
    return AuditLog(path=Path(path))
