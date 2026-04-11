"""Tests for portwhisper.timeout module."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from portwhisper.timeout import TimeoutConfig, try_connect


# ---------------------------------------------------------------------------
# TimeoutConfig tests
# ---------------------------------------------------------------------------

def test_timeout_config_defaults():
    cfg = TimeoutConfig()
    assert cfg.connect_timeout == 1.5
    assert cfg.banner_timeout == 2.0
    assert cfg.max_retries == 1


def test_timeout_config_custom():
    cfg = TimeoutConfig(connect_timeout=0.5, banner_timeout=1.0, max_retries=3)
    assert cfg.connect_timeout == 0.5
    assert cfg.max_retries == 3


def test_timeout_config_invalid_connect():
    with pytest.raises(ValueError, match="connect_timeout"):
        TimeoutConfig(connect_timeout=0)


def test_timeout_config_invalid_banner():
    with pytest.raises(ValueError, match="banner_timeout"):
        TimeoutConfig(banner_timeout=-1.0)


def test_timeout_config_invalid_retries():
    with pytest.raises(ValueError, match="max_retries"):
        TimeoutConfig(max_retries=-1)


# ---------------------------------------------------------------------------
# try_connect tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_try_connect_open_with_banner():
    reader = AsyncMock()
    reader.read = AsyncMock(return_value=b"SSH-2.0-OpenSSH_8.9\r\n")
    writer = MagicMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()

    cfg = TimeoutConfig(connect_timeout=1.0, banner_timeout=1.0, max_retries=0)

    with patch("portwhisper.timeout.asyncio.open_connection", return_value=(reader, writer)):
        open_flag, banner = await try_connect("127.0.0.1", 22, cfg)

    assert open_flag is True
    assert banner is not None
    assert "SSH" in banner


@pytest.mark.asyncio
async def test_try_connect_open_no_banner():
    reader = AsyncMock()
    reader.read = AsyncMock(side_effect=asyncio.TimeoutError)
    writer = MagicMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()

    cfg = TimeoutConfig(connect_timeout=1.0, banner_timeout=0.1, max_retries=0)

    with patch("portwhisper.timeout.asyncio.open_connection", return_value=(reader, writer)):
        open_flag, banner = await try_connect("127.0.0.1", 80, cfg)

    assert open_flag is True
    assert banner is None


@pytest.mark.asyncio
async def test_try_connect_closed_port():
    cfg = TimeoutConfig(connect_timeout=0.1, banner_timeout=0.1, max_retries=0)

    with patch(
        "portwhisper.timeout.asyncio.open_connection",
        side_effect=ConnectionRefusedError,
    ):
        open_flag, banner = await try_connect("127.0.0.1", 9999, cfg)

    assert open_flag is False
    assert banner is None


@pytest.mark.asyncio
async def test_try_connect_uses_default_config():
    with patch(
        "portwhisper.timeout.asyncio.open_connection",
        side_effect=asyncio.TimeoutError,
    ):
        open_flag, banner = await try_connect("127.0.0.1", 1234)

    assert open_flag is False
    assert banner is None
