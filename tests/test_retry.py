"""Tests for portwhisper.retry module."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from portwhisper.retry import RetryConfig, with_retry


# ---------------------------------------------------------------------------
# RetryConfig
# ---------------------------------------------------------------------------

def test_retry_config_defaults() -> None:
    cfg = RetryConfig()
    assert cfg.max_attempts == 3
    assert cfg.base_delay == 0.1
    assert cfg.backoff_factor == 2.0


def test_retry_config_invalid_attempts() -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        RetryConfig(max_attempts=0)


def test_retry_config_invalid_delay() -> None:
    with pytest.raises(ValueError, match="base_delay"):
        RetryConfig(base_delay=-1.0)


def test_retry_config_invalid_backoff() -> None:
    with pytest.raises(ValueError, match="backoff_factor"):
        RetryConfig(backoff_factor=0.5)


# ---------------------------------------------------------------------------
# with_retry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_with_retry_succeeds_first_attempt() -> None:
    calls = 0

    async def coro() -> str:
        nonlocal calls
        calls += 1
        return "ok"

    result = await with_retry(coro, RetryConfig(max_attempts=3))
    assert result == "ok"
    assert calls == 1


@pytest.mark.asyncio
async def test_with_retry_succeeds_after_failures() -> None:
    calls = 0

    async def coro() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionRefusedError("nope")
        return "ok"

    with patch("portwhisper.retry.asyncio.sleep", new_callable=AsyncMock):
        result = await with_retry(coro, RetryConfig(max_attempts=3, base_delay=0.0))

    assert result == "ok"
    assert calls == 3


@pytest.mark.asyncio
async def test_with_retry_raises_after_all_attempts() -> None:
    async def coro() -> None:
        raise TimeoutError("timed out")

    with patch("portwhisper.retry.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(TimeoutError, match="timed out"):
            await with_retry(coro, RetryConfig(max_attempts=3, base_delay=0.0))


@pytest.mark.asyncio
async def test_with_retry_non_retryable_raises_immediately() -> None:
    calls = 0

    async def coro() -> None:
        nonlocal calls
        calls += 1
        raise ValueError("bad value")

    with pytest.raises(ValueError):
        await with_retry(coro, RetryConfig(max_attempts=3))

    assert calls == 1


@pytest.mark.asyncio
async def test_with_retry_uses_default_config() -> None:
    async def coro() -> int:
        return 42

    result = await with_retry(coro)
    assert result == 42
