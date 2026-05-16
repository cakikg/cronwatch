"""Factory for building a Heartbeat instance from CronwatchConfig."""

from __future__ import annotations

import os
from pathlib import Path

from cronwatch.heartbeat import Heartbeat, HeartbeatConfig

_DEFAULT_HEARTBEAT_PATH = Path("/tmp/cronwatch/heartbeat")
_ENV_HEARTBEAT_PATH = "CRONWATCH_HEARTBEAT_PATH"
_ENV_HEARTBEAT_INTERVAL = "CRONWATCH_HEARTBEAT_INTERVAL"
_DEFAULT_INTERVAL = 60.0


def build_heartbeat(config=None) -> Heartbeat:
    """Build a Heartbeat from config, environment variables, or defaults.

    Resolution order for path:
      1. config.heartbeat_path (if the config object exposes it)
      2. CRONWATCH_HEARTBEAT_PATH environment variable
      3. /tmp/cronwatch/heartbeat

    Resolution order for interval:
      1. config.heartbeat_interval (if the config object exposes it)
      2. CRONWATCH_HEARTBEAT_INTERVAL environment variable
      3. 60 seconds
    """
    path: Path
    if config is not None and getattr(config, "heartbeat_path", None):
        path = Path(config.heartbeat_path)
    elif os.environ.get(_ENV_HEARTBEAT_PATH):
        path = Path(os.environ[_ENV_HEARTBEAT_PATH])
    else:
        path = _DEFAULT_HEARTBEAT_PATH

    interval: float
    if config is not None and getattr(config, "heartbeat_interval", None) is not None:
        interval = float(config.heartbeat_interval)
    elif os.environ.get(_ENV_HEARTBEAT_INTERVAL):
        interval = float(os.environ[_ENV_HEARTBEAT_INTERVAL])
    else:
        interval = _DEFAULT_INTERVAL

    hb_config = HeartbeatConfig(path=path, interval_seconds=interval)
    return Heartbeat(hb_config)
