"""Retry logic for transient connection failures during port scanning."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behaviour."""

    max_attempts: int = 3
    base_delay: float = 0.1  # seconds
    backoff_factor: float = 2.0
    retryable_exceptions: tuple[type[Exception], ...] = field(
        default_factory=lambda: (ConnectionRefusedError, TimeoutError, OSError)
    )

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if self.backoff_factor < 1.0:
            raise ValueError("backoff_factor must be >= 1.0")


async def with_retry(
    coro_fn: Callable[[], Awaitable[T]],
    config: RetryConfig | None = None,
) -> T:
    """Execute *coro_fn* with exponential-backoff retries.

    Raises the last exception if all attempts are exhausted.
    """
    cfg = config or RetryConfig()
    delay = cfg.base_delay
    last_exc: Exception | None = None

    for attempt in range(1, cfg.max_attempts + 1):
        try:
            return await coro_fn()
        except cfg.retryable_exceptions as exc:
            last_exc = exc
            if attempt < cfg.max_attempts:
                logger.debug(
                    "Attempt %d/%d failed (%s). Retrying in %.2fs.",
                    attempt,
                    cfg.max_attempts,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
                delay *= cfg.backoff_factor
            else:
                logger.debug(
                    "Attempt %d/%d failed (%s). No more retries.",
                    attempt,
                    cfg.max_attempts,
                    exc,
                )

    raise last_exc  # type: ignore[misc]
