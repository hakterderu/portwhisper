"""Tests for portwhisper.scheduler module."""
from __future__ import annotations

import asyncio
import pytest

from portwhisper.scheduler import (
    SchedulerConfig,
    make_scheduler_config,
    run_with_semaphore,
    schedule_scans,
)


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# SchedulerConfig
# ---------------------------------------------------------------------------

def test_scheduler_config_defaults():
    cfg = SchedulerConfig()
    assert cfg.max_concurrency == 500
    assert cfg.queue_timeout == 30.0


def test_scheduler_config_invalid_concurrency():
    with pytest.raises(ValueError, match="max_concurrency"):
        SchedulerConfig(max_concurrency=0)


def test_scheduler_config_invalid_timeout():
    with pytest.raises(ValueError, match="queue_timeout"):
        SchedulerConfig(queue_timeout=-1.0)


def test_make_scheduler_config_custom():
    cfg = make_scheduler_config(max_concurrency=100, queue_timeout=10.0)
    assert cfg.max_concurrency == 100
    assert cfg.queue_timeout == 10.0


# ---------------------------------------------------------------------------
# run_with_semaphore
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_with_semaphore_returns_value():
    sem = asyncio.Semaphore(1)

    async def coro() -> int:
        return 42

    result = await run_with_semaphore(sem, coro())
    assert result == 42


@pytest.mark.asyncio
async def test_run_with_semaphore_releases_on_exception():
    sem = asyncio.Semaphore(1)

    async def failing_coro():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await run_with_semaphore(sem, failing_coro())

    # Semaphore should be released; another acquire must not block.
    acquired = sem.locked()
    assert not acquired


# ---------------------------------------------------------------------------
# schedule_scans
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_schedule_scans_all_results_returned():
    async def identity(n: int) -> int:
        return n

    tasks = [identity(i) for i in range(10)]
    results = await schedule_scans(tasks, config=SchedulerConfig(max_concurrency=3))
    assert sorted(results) == list(range(10))


@pytest.mark.asyncio
async def test_schedule_scans_respects_concurrency():
    active: list[int] = []
    peak: list[int] = []

    async def probe(n: int) -> int:
        active.append(n)
        peak.append(len(active))
        await asyncio.sleep(0)
        active.remove(n)
        return n

    cfg = SchedulerConfig(max_concurrency=5)
    tasks = [probe(i) for i in range(20)]
    await schedule_scans(tasks, config=cfg)
    assert max(peak) <= 5


@pytest.mark.asyncio
async def test_schedule_scans_default_config():
    async def noop() -> str:
        return "ok"

    results = await schedule_scans([noop() for _ in range(5)])
    assert results == ["ok"] * 5
