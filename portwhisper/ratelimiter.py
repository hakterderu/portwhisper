"""
Rate limiter utilities for controlling scan concurrency and connection rate.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RateLimiterConfig:
    """Configuration for the rate limiter."""
    max_concurrent: int = 100
    rate_limit: Optional[float] = None  # max connections per second, None = unlimited
    timeout: float = 2.0


class RateLimiter:
    """
    Async rate limiter that controls both concurrency (via semaphore)
    and optional per-second connection rate.
    """

    def __init__(self, config: RateLimiterConfig) -> None:
        self._config = config
        self._semaphore = asyncio.Semaphore(config.max_concurrent)
        self._rate_limit = config.rate_limit
        self._min_interval = 1.0 / config.rate_limit if config.rate_limit else 0.0
        self._last_acquire: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire the rate limiter, respecting concurrency and rate limits."""
        await self._semaphore.acquire()
        if self._rate_limit is not None:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_acquire
                wait = self._min_interval - elapsed
                if wait > 0:
                    await asyncio.sleep(wait)
                self._last_acquire = time.monotonic()

    def release(self) -> None:
        """Release the semaphore slot."""
        self._semaphore.release()

    async def __aenter__(self) -> "RateLimiter":
        await self.acquire()
        return self

    async def __aexit__(self, *args) -> None:
        self.release()


def make_rate_limiter(max_concurrent: int = 100, rate_limit: Optional[float] = None, timeout: float = 2.0) -> RateLimiter:
    """Factory helper to create a RateLimiter from individual parameters."""
    config = RateLimiterConfig(
        max_concurrent=max_concurrent,
        rate_limit=rate_limit,
        timeout=timeout,
    )
    return RateLimiter(config)
