"""Concurrency scheduler — controls how many ports are probed simultaneously."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Iterable, List, TypeVar

T = TypeVar("T")


@dataclass
class SchedulerConfig:
    """Configuration for the scan concurrency scheduler."""
    max_concurrency: int = 500
    queue_timeout: float = 30.0  # max seconds to wait for a slot

    def __post_init__(self) -> None:
        if self.max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")
        if self.queue_timeout <= 0:
            raise ValueError("queue_timeout must be positive")


async def run_with_semaphore(
    semaphore: asyncio.Semaphore,
    coro: Awaitable[T],
) -> T:
    """Acquire *semaphore*, run *coro*, then release."""
    async with semaphore:
        return await coro


async def schedule_scans(
    tasks: Iterable[Awaitable[T]],
    config: SchedulerConfig | None = None,
) -> List[T]:
    """
    Run all *tasks* with bounded concurrency defined by *config*.

    Returns results in completion order (same as asyncio.gather order).
    """
    if config is None:
        config = SchedulerConfig()
    sem = asyncio.Semaphore(config.max_concurrency)
    wrapped = [run_with_semaphore(sem, t) for t in tasks]
    return list(await asyncio.gather(*wrapped))


def make_scheduler_config(
    max_concurrency: int = 500,
    queue_timeout: float = 30.0,
) -> SchedulerConfig:
    """Factory helper for SchedulerConfig."""
    return SchedulerConfig(
        max_concurrency=max_concurrency,
        queue_timeout=queue_timeout,
    )
