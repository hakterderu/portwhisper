"""Tests for portwhisper.resolver."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from portwhisper.resolver import ResolveResult, resolve_host, resolve_host_sync


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# ResolveResult
# ---------------------------------------------------------------------------


def test_resolve_result_str_resolved():
    result = ResolveResult(host="example.com", ip_address="93.184.216.34", resolved=True)
    assert "example.com" in str(result)
    assert "93.184.216.34" in str(result)


def test_resolve_result_str_unresolved():
    result = ResolveResult(
        host="bad.invalid", ip_address=None, resolved=False, error="Name or service not known"
    )
    text = str(result)
    assert "bad.invalid" in text
    assert "unresolved" in text


def test_resolve_result_defaults():
    result = ResolveResult(host="localhost", ip_address="127.0.0.1", resolved=True)
    assert result.error is None


# ---------------------------------------------------------------------------
# resolve_host
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_host_success():
    with patch("socket.gethostbyname", return_value="1.2.3.4"):
        result = await resolve_host("example.com")
    assert result.resolved is True
    assert result.ip_address == "1.2.3.4"
    assert result.error is None


@pytest.mark.asyncio
async def test_resolve_host_timeout():
    import socket as _socket

    async def _slow(*_):
        await asyncio.sleep(10)

    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
        result = await resolve_host("slow.example.com", timeout=0.001)
    assert result.resolved is False
    assert result.ip_address is None
    assert "timed out" in (result.error or "")


@pytest.mark.asyncio
async def test_resolve_host_gaierror():
    import socket as _socket

    with patch(
        "socket.gethostbyname",
        side_effect=_socket.gaierror("Name or service not known"),
    ):
        result = await resolve_host("notareal.invalid")
    assert result.resolved is False
    assert result.ip_address is None
    assert result.error is not None


# ---------------------------------------------------------------------------
# resolve_host_sync
# ---------------------------------------------------------------------------


def test_resolve_host_sync_success():
    with patch("socket.gethostbyname", return_value="127.0.0.1"):
        result = resolve_host_sync("localhost")
    assert result.resolved is True
    assert result.ip_address == "127.0.0.1"
