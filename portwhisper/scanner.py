"""Core async port scanner module for portwhisper."""

import asyncio
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ScanResult:
    host: str
    port: int
    state: str  # 'open' | 'closed' | 'filtered'
    service: Optional[str] = None
    banner: Optional[str] = None
    latency_ms: Optional[float] = None


@dataclass
class ScanConfig:
    host: str
    ports: List[int]
    timeout: float = 1.0
    concurrency: int = 100
    grab_banner: bool = True


async def _probe_port(host: str, port: int, timeout: float, grab_banner: bool) -> ScanResult:
    """Attempt a TCP connection to host:port and optionally grab a banner."""
    import time

    start = time.monotonic()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        latency_ms = (time.monotonic() - start) * 1000

        banner = None
        if grab_banner:
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=timeout)
                banner = data.decode(errors="replace").strip() or None
            except (asyncio.TimeoutError, ConnectionResetError):
                pass

        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

        return ScanResult(
            host=host,
            port=port,
            state="open",
            banner=banner,
            latency_ms=round(latency_ms, 2),
        )
    except (asyncio.TimeoutError, asyncio.CancelledError):
        return ScanResult(host=host, port=port, state="filtered")
    except (ConnectionRefusedError, OSError):
        return ScanResult(host=host, port=port, state="closed")


async def run_scan(config: ScanConfig) -> List[ScanResult]:
    """Run an async port scan according to the provided ScanConfig."""
    semaphore = asyncio.Semaphore(config.concurrency)

    async def bounded_probe(port: int) -> ScanResult:
        async with semaphore:
            return await _probe_port(
                config.host, port, config.timeout, config.grab_banner
            )

    tasks = [bounded_probe(port) for port in config.ports]
    results = await asyncio.gather(*tasks)
    return sorted(results, key=lambda r: r.port)
