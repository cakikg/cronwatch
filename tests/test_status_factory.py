"""Tests for cronwatch.status_factory."""

from unittest.mock import MagicMock

from cronwatch.status import StatusBuilder
from cronwatch.status_factory import build_status_builder


def test_build_status_builder_returns_builder():
    config = MagicMock()
    tracker = MagicMock()
    recorder = MagicMock()
    scheduler = MagicMock()

    builder = build_status_builder(
        config=config,
        tracker=tracker,
        recorder=recorder,
        scheduler=scheduler,
    )

    assert isinstance(builder, StatusBuilder)


def test_build_status_builder_wires_components():
    config = MagicMock()
    tracker = MagicMock()
    recorder = MagicMock()
    scheduler = MagicMock()

    builder = build_status_builder(
        config=config,
        tracker=tracker,
        recorder=recorder,
        scheduler=scheduler,
    )

    assert builder._tracker is tracker
    assert builder._recorder is recorder
    assert builder._scheduler is scheduler
