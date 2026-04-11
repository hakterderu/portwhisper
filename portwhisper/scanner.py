"""
Core async port scanner with service fingerprinting integration.
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Optional

from portwhisper.ratelimiter import RateLimiter, make_rate_limiter


@dataclass
class ScanResult:
    host: str
    port: int
    open: bool
    banner: Optional[str] = None
    service: Optional[str] = None


@dataclass
class ScanConfig:
    host: str
    ports: List[int]
    timeout: float = 2.0
    max_concurrent: int = 100
    rate_limit: Optional[float] = None  # connections per second
    fingerprint: bool = True


async def _probe_port(host: str, port: int, timeout: float) -> tuple[bool, Optional[str]]:
    """Attempt to connect to host:port and optionally grab a banner."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        banner: Optional[str] = None
        try:
            data = await asyncio.wait_for(reader.read(1024), timeout=timeout)
            if data:
                banner = data.decode(errors="replace").strip()
        except (asyncio.TimeoutError, ConnectionResetError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
        return True, banner
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False, None


async def scan_port(host: str, port: int, timeout: float, limiter: RateLimiter) -> ScanResult:
    """Scan a single port using the provided rate limiter."""
    async with limiter:
        is_open, banner = await _probe_port(host, port, timeout)
    return ScanResult(host=host, port=port, open=is_open, banner=banner)


async def run_scan(config: ScanConfig) -> List[ScanResult]:
    """Run a full scan against all configured ports concurrently."""
    limiter = make_rate_limiter(
        max_concurrent=config.max_concurrent,
        rate_limit=config.rate_limit,
        timeout=config.timeout,
    )
    tasks = [
        scan_port(config.host, port, config.timeout, limiter)
        for port in config.ports
    ]
    results: List[ScanResult] = await asyncio.gather(*tasks)

    if config.fingerprint:
        from portwhisper.fingerprint import annotate_results
        results = annotate_results(results)

    return sorted(results, key=lambda r: r.port)
