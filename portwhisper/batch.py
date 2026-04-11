"""Batch scanning support: split port lists into chunks for parallel processing."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import List, Sequence

from portwhisper.scanner import ScanResult, ScanConfig


@dataclass
class BatchConfig:
    """Configuration for batched port scanning."""

    chunk_size: int = 100
    max_batches: int = 10

    def __post_init__(self) -> None:
        if self.chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        if self.max_batches < 1:
            raise ValueError("max_batches must be >= 1")


def split_ports(ports: Sequence[int], chunk_size: int) -> List[List[int]]:
    """Split a flat list of ports into chunks of at most *chunk_size*."""
    ports = list(ports)
    return [ports[i : i + chunk_size] for i in range(0, len(ports), chunk_size)]


async def scan_batch(
    host: str,
    ports: Sequence[int],
    scan_config: ScanConfig,
    batch_config: BatchConfig | None = None,
) -> List[ScanResult]:
    """Scan *ports* against *host* in parallel batches.

    Each batch is a ``chunk_size`` slice of the port list.  Batches run
    concurrently up to *max_batches* at a time.
    """
    if batch_config is None:
        batch_config = BatchConfig()

    chunks = split_ports(ports, batch_config.chunk_size)
    semaphore = asyncio.Semaphore(batch_config.max_batches)

    async def _run_chunk(chunk: List[int]) -> List[ScanResult]:
        async with semaphore:
            tasks = [
                asyncio.create_task(_probe(host, port, scan_config))
                for port in chunk
            ]
            return list(await asyncio.gather(*tasks))

    batch_tasks = [asyncio.create_task(_run_chunk(c)) for c in chunks]
    nested = await asyncio.gather(*batch_tasks)
    return [result for batch in nested for result in batch]


async def _probe(host: str, port: int, config: ScanConfig) -> ScanResult:
    """Attempt a TCP connection and return a ScanResult."""
    try:
        conn = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(conn, timeout=config.timeout)
        writer.close()
        await writer.wait_closed()
        return ScanResult(host=host, port=port, open=True)
    except Exception:
        return ScanResult(host=host, port=port, open=False)
