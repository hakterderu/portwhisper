"""High-level scan pipeline combining scheduler, progress, and rate limiter."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Sequence

from portwhisper.progress import ProgressTracker, make_progress_tracker
from portwhisper.ratelimiter import RateLimiter, make_rate_limiter
from portwhisper.scheduler import SchedulerConfig, schedule_scans
from portwhisper.scanner import ScanConfig, ScanResult


@dataclass
class PipelineConfig:
    """Aggregate config for a complete scan pipeline run."""
    scan: ScanConfig
    scheduler: SchedulerConfig
    max_rate: float = 0.0          # 0 means unlimited
    show_progress: bool = True


async def _probe_port(
    host: str,
    port: int,
    scan_cfg: ScanConfig,
    tracker: ProgressTracker,
    limiter: RateLimiter | None,
) -> ScanResult:
    """Probe a single port, updating progress and honouring rate limits."""
    if limiter is not None:
        await limiter.acquire()
    try:
        future = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(
            future, timeout=scan_cfg.timeout
        )
        writer.close()
        await writer.wait_closed()
        result = ScanResult(host=host, port=port, open=True)
    except Exception:
        result = ScanResult(host=host, port=port, open=False)
    finally:
        if limiter is not None:
            limiter.release()
    await tracker.increment(is_open=result.open)
    return result


async def run_pipeline(
    host: str,
    ports: Sequence[int],
    config: PipelineConfig,
) -> List[ScanResult]:
    """
    Execute a full scan pipeline for *host* over *ports*.

    Returns a list of ScanResult objects sorted by port number.
    """
    tracker = make_progress_tracker(
        host=host,
        total_ports=len(ports),
        show_progress=config.show_progress,
    )
    limiter: RateLimiter | None = (
        make_rate_limiter(rate=config.max_rate) if config.max_rate > 0 else None
    )

    tasks = [
        _probe_port(host, port, config.scan, tracker, limiter)
        for port in ports
    ]
    results = await schedule_scans(tasks, config=config.scheduler)
    return sorted(results, key=lambda r: r.port)
