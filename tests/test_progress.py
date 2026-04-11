"""Tests for portwhisper.progress module."""
from __future__ import annotations

import asyncio
import pytest

from portwhisper.progress import (
    ProgressConfig,
    ProgressTracker,
    make_progress_tracker,
)


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# ProgressConfig
# ---------------------------------------------------------------------------

def test_progress_config_defaults():
    cfg = ProgressConfig(total_ports=100, host="127.0.0.1")
    assert cfg.show_progress is True
    assert cfg.update_interval == 0.5


def test_progress_config_invalid_total_ports():
    with pytest.raises(ValueError, match="total_ports"):
        ProgressConfig(total_ports=0, host="localhost")


def test_progress_config_invalid_interval():
    with pytest.raises(ValueError, match="update_interval"):
        ProgressConfig(total_ports=10, host="localhost", update_interval=0.0)


# ---------------------------------------------------------------------------
# ProgressTracker
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tracker_initial_state():
    tracker = make_progress_tracker(host="192.168.1.1", total_ports=50)
    assert tracker.scanned == 0
    assert tracker.open_count == 0
    assert tracker.percent == 0.0


@pytest.mark.asyncio
async def test_tracker_increment_closed():
    tracker = make_progress_tracker(host="localhost", total_ports=10)
    await tracker.increment(is_open=False)
    assert tracker.scanned == 1
    assert tracker.open_count == 0


@pytest.mark.asyncio
async def test_tracker_increment_open():
    tracker = make_progress_tracker(host="localhost", total_ports=10)
    await tracker.increment(is_open=True)
    assert tracker.scanned == 1
    assert tracker.open_count == 1


@pytest.mark.asyncio
async def test_tracker_percent_calculation():
    tracker = make_progress_tracker(host="localhost", total_ports=4)
    await tracker.increment()
    await tracker.increment()
    assert tracker.percent == pytest.approx(50.0)


@pytest.mark.asyncio
async def test_tracker_summary_contains_host():
    tracker = make_progress_tracker(host="scanme.example.com", total_ports=100)
    await tracker.increment(is_open=True)
    summary = tracker.summary()
    assert "scanme.example.com" in summary
    assert "1" in summary


@pytest.mark.asyncio
async def test_tracker_concurrent_increments():
    tracker = make_progress_tracker(host="localhost", total_ports=100)
    await asyncio.gather(*[tracker.increment(is_open=(i % 2 == 0)) for i in range(20)])
    assert tracker.scanned == 20
    assert tracker.open_count == 10


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def test_make_progress_tracker_returns_tracker():
    tracker = make_progress_tracker(host="10.0.0.1", total_ports=65535)
    assert isinstance(tracker, ProgressTracker)
    assert tracker.config.host == "10.0.0.1"
    assert tracker.config.total_ports == 65535
