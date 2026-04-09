"""Tests for the async port scanner core."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from portwhisper.scanner import ScanConfig, ScanResult, _probe_port, run_scan


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_probe_open_port_no_banner():
    mock_reader = AsyncMock()
    mock_reader.read = AsyncMock(return_value=b"")
    mock_writer = AsyncMock()

    with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
        result = await _probe_port("127.0.0.1", 80, timeout=1.0, grab_banner=True)

    assert result.state == "open"
    assert result.port == 80
    assert result.host == "127.0.0.1"
    assert result.banner is None


@pytest.mark.asyncio
async def test_probe_open_port_with_banner():
    mock_reader = AsyncMock()
    mock_reader.read = AsyncMock(return_value=b"SSH-2.0-OpenSSH_8.9")
    mock_writer = AsyncMock()

    with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
        result = await _probe_port("127.0.0.1", 22, timeout=1.0, grab_banner=True)

    assert result.state == "open"
    assert result.banner == "SSH-2.0-OpenSSH_8.9"


@pytest.mark.asyncio
async def test_probe_closed_port():
    with patch("asyncio.open_connection", side_effect=ConnectionRefusedError):
        result = await _probe_port("127.0.0.1", 9999, timeout=1.0, grab_banner=False)

    assert result.state == "closed"


@pytest.mark.asyncio
async def test_probe_filtered_port():
    with patch("asyncio.open_connection", side_effect=asyncio.TimeoutError):
        result = await _probe_port("127.0.0.1", 9998, timeout=0.1, grab_banner=False)

    assert result.state == "filtered"


@pytest.mark.asyncio
async def test_run_scan_returns_sorted_results():
    async def fake_probe(host, port, timeout, grab_banner):
        return ScanResult(host=host, port=port, state="open")

    config = ScanConfig(host="127.0.0.1", ports=[443, 80, 22], timeout=1.0)

    with patch("portwhisper.scanner._probe_port", side_effect=fake_probe):
        results = await run_scan(config)

    assert [r.port for r in results] == [22, 80, 443]
