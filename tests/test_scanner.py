"""
Tests for portwhisper.scanner module.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from portwhisper.scanner import ScanConfig, ScanResult, run_scan, scan_port
from portwhisper.ratelimiter import make_rate_limiter


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_scan_port_open():
    limiter = make_rate_limiter(max_concurrent=10)
    with patch("portwhisper.scanner._probe_port", new_callable=AsyncMock) as mock_probe:
        mock_probe.return_value = (True, "SSH-2.0-OpenSSH")
        result = await scan_port("127.0.0.1", 22, 2.0, limiter)
    assert result.open is True
    assert result.banner == "SSH-2.0-OpenSSH"
    assert result.port == 22


@pytest.mark.asyncio
async def test_scan_port_closed():
    limiter = make_rate_limiter(max_concurrent=10)
    with patch("portwhisper.scanner._probe_port", new_callable=AsyncMock) as mock_probe:
        mock_probe.return_value = (False, None)
        result = await scan_port("127.0.0.1", 9999, 2.0, limiter)
    assert result.open is False
    assert result.banner is None


@pytest.mark.asyncio
async def test_run_scan_returns_sorted_results():
    async def fake_probe(host, port, timeout):
        return (port % 2 == 0, None)

    with patch("portwhisper.scanner._probe_port", side_effect=fake_probe):
        config = ScanConfig(
            host="127.0.0.1",
            ports=[443, 80, 22, 8080],
            timeout=1.0,
            fingerprint=False,
        )
        results = await run_scan(config)

    ports = [r.port for r in results]
    assert ports == sorted(ports)


@pytest.mark.asyncio
async def test_run_scan_calls_fingerprint_when_enabled():
    async def fake_probe(host, port, timeout):
        return (True, None)

    with patch("portwhisper.scanner._probe_port", side_effect=fake_probe):
        with patch("portwhisper.fingerprint.annotate_results", side_effect=lambda r: r) as mock_ann:
            config = ScanConfig(
                host="127.0.0.1",
                ports=[80],
                fingerprint=True,
            )
            await run_scan(config)
    mock_ann.assert_called_once()


@pytest.mark.asyncio
async def test_run_scan_skips_fingerprint_when_disabled():
    async def fake_probe(host, port, timeout):
        return (True, None)

    with patch("portwhisper.scanner._probe_port", side_effect=fake_probe):
        with patch("portwhisper.fingerprint.annotate_results") as mock_ann:
            config = ScanConfig(
                host="127.0.0.1",
                ports=[80],
                fingerprint=False,
            )
            await run_scan(config)
    mock_ann.assert_not_called()
