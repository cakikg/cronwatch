"""Factory for building an AlertReplayBuffer from CronwatchConfig."""
from __future__ import annotations

from cronwatch.replay import AlertReplayBuffer, ReplayConfig


def build_replay_buffer(config=None) -> AlertReplayBuffer:
    """Build a replay buffer, reading max_size from config if available."""
    max_size = 50
    if config is not None:
        raw = getattr(config, "replay_buffer_size", None)
        if raw is not None:
            try:
                max_size = int(raw)
            except (TypeError, ValueError):
                pass
    return AlertReplayBuffer(config=ReplayConfig(max_size=max_size))
