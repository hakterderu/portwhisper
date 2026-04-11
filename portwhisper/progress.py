"""Progress tracking for async port scans."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProgressConfig:
    """Configuration for scan progress tracking."""
    total_ports: int
    host: str
    show_progress: bool = True
    update_interval: float = 0.5  # seconds between console updates

    def __post_init__(self) -> None:
        if self.total_ports < 1:
            raise ValueError("total_ports must be >= 1")
        if self.update_interval <= 0:
            raise ValueError("update_interval must be positive")


@dataclass
class ProgressTracker:
    """Thread-safe progress tracker for ongoing port scans."""
    config: ProgressConfig
    _scanned: int = field(default=0, init=False)
    _open_count: int = field(default=0, init=False)
    _start_time: float = field(default_factory=time.monotonic, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    async def increment(self, is_open: bool = False) -> None:
        """Record one completed port scan."""
        async with self._lock:
            self._scanned += 1
            if is_open:
                self._open_count += 1

    @property
    def scanned(self) -> int:
        return self._scanned

    @property
    def open_count(self) -> int:
        return self._open_count

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self._start_time

    @property
    def percent(self) -> float:
        if self.config.total_ports == 0:
            return 0.0
        return (self._scanned / self.config.total_ports) * 100.0

    def summary(self) -> str:
        """Return a human-readable progress summary line."""
        return (
            f"[{self.config.host}] "
            f"{self._scanned}/{self.config.total_ports} ports "
            f"({self.percent:.1f}%) — "
            f"{self._open_count} open — "
            f"{self.elapsed:.1f}s elapsed"
        )


def make_progress_tracker(
    host: str,
    total_ports: int,
    show_progress: bool = True,
    update_interval: float = 0.5,
) -> ProgressTracker:
    """Factory for creating a ProgressTracker with sensible defaults."""
    cfg = ProgressConfig(
        total_ports=total_ports,
        host=host,
        show_progress=show_progress,
        update_interval=update_interval,
    )
    return ProgressTracker(config=cfg)
