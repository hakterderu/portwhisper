"""Tests for portwhisper.batch."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from portwhisper.batch import BatchConfig, split_ports, scan_batch
from portwhisper.scanner import ScanConfig, ScanResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# BatchConfig
# ---------------------------------------------------------------------------

def test_batch_config_defaults():
    cfg = BatchConfig()
    assert cfg.chunk_size == 100
    assert cfg.max_batches == 10


def test_batch_config_custom():
    cfg = BatchConfig(chunk_size=50, max_batches=4)
    assert cfg.chunk_size == 50
    assert cfg.max_batches == 4


def test_batch_config_invalid_chunk_size():
    with pytest.raises(ValueError, match="chunk_size"):
        BatchConfig(chunk_size=0)


def test_batch_config_invalid_max_batches():
    with pytest.raises(ValueError, match="max_batches"):
        BatchConfig(max_batches=0)


# ---------------------------------------------------------------------------
# split_ports
# ---------------------------------------------------------------------------

def test_split_ports_even():
    chunks = split_ports(list(range(10)), chunk_size=5)
    assert chunks == [list(range(5)), list(range(5, 10))]


def test_split_ports_remainder():
    chunks = split_ports(list(range(7)), chunk_size=3)
    assert len(chunks) == 3
    assert chunks[-1] == [6]


def test_split_ports_empty():
    assert split_ports([], chunk_size=10) == []


def test_split_ports_single_chunk():
    chunks = split_ports([80, 443], chunk_size=100)
    assert chunks == [[80, 443]]


# ---------------------------------------------------------------------------
# scan_batch
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scan_batch_returns_all_results():
    open_ports = {80, 443}

    async def fake_probe(host, port, config):
        return ScanResult(host=host, port=port, open=(port in open_ports))

    with patch("portwhisper.batch._probe", side_effect=fake_probe):
        results = await scan_batch(
            host="127.0.0.1",
            ports=[80, 443, 8080],
            scan_config=ScanConfig(timeout=1.0),
            batch_config=BatchConfig(chunk_size=2, max_batches=2),
        )

    assert len(results) == 3
    open_found = {r.port for r in results if r.open}
    assert open_found == {80, 443}


@pytest.mark.asyncio
async def test_scan_batch_uses_default_batch_config():
    async def fake_probe(host, port, config):
        return ScanResult(host=host, port=port, open=False)

    with patch("portwhisper.batch._probe", side_effect=fake_probe):
        results = await scan_batch(
            host="localhost",
            ports=list(range(5)),
            scan_config=ScanConfig(timeout=1.0),
        )

    assert len(results) == 5
