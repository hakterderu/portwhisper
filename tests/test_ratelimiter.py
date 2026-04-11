"""
Tests for portwhisper.ratelimiter module.
"""

import asyncio
import time
import pytest

from portwhisper.ratelimiter import RateLimiter, RateLimiterConfig, make_rate_limiter


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_acquire_release_basic():
    rl = make_rate_limiter(max_concurrent=5)
    await rl.acquire()
    rl.release()
    # Should not raise


@pytest.mark.asyncio
async def test_context_manager():
    rl = make_rate_limiter(max_concurrent=5)
    async with rl:
        pass  # Should not raise


@pytest.mark.asyncio
async def test_concurrency_limit():
    max_concurrent = 3
    rl = make_rate_limiter(max_concurrent=max_concurrent)
    active = []
    peak = [0]

    async def task():
        async with rl:
            active.append(1)
            peak[0] = max(peak[0], len(active))
            await asyncio.sleep(0.02)
            active.pop()

    await asyncio.gather(*[task() for _ in range(9)])
    assert peak[0] <= max_concurrent


@pytest.mark.asyncio
async def test_rate_limit_enforces_delay():
    rate = 20.0  # 20 per second => 50ms between acquires
    rl = make_rate_limiter(max_concurrent=100, rate_limit=rate)
    times = []

    for _ in range(4):
        await rl.acquire()
        times.append(time.monotonic())
        rl.release()

    intervals = [times[i + 1] - times[i] for i in range(len(times) - 1)]
    for interval in intervals:
        assert interval >= 0.04, f"Interval {interval:.4f}s shorter than expected"


@pytest.mark.asyncio
async def test_no_rate_limit_is_fast():
    rl = make_rate_limiter(max_concurrent=50, rate_limit=None)
    start = time.monotonic()
    for _ in range(20):
        await rl.acquire()
        rl.release()
    elapsed = time.monotonic() - start
    assert elapsed < 0.5, "Unlimited rate limiter should complete quickly"


def test_make_rate_limiter_defaults():
    rl = make_rate_limiter()
    assert isinstance(rl, RateLimiter)


def test_rate_limiter_config_defaults():
    cfg = RateLimiterConfig()
    assert cfg.max_concurrent == 100
    assert cfg.rate_limit is None
    assert cfg.timeout == 2.0
