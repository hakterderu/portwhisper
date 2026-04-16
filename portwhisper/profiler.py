"""Scan profiler: measures timing and throughput statistics for a scan run."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProfilerConfig:
    enabled: bool = True
    precision: int = 3  # decimal places for timing output

    def __post_init__(self) -> None:
        if self.precision < 0 or self.precision > 9:
            raise ValueError("precision must be between 0 and 9")


@dataclass
class ScanProfile:
    total_ports: int
    open_ports: int
    elapsed_seconds: float
    precision: int = 3
    _extra: dict = field(default_factory=dict, repr=False)

    @property
    def ports_per_second(self) -> float:
        if self.elapsed_seconds == 0:
            return 0.0
        return self.total_ports / self.elapsed_seconds

    @property
    def closed_ports(self) -> int:
        return self.total_ports - self.open_ports

    def to_dict(self) -> dict:
        p = self.precision
        return {
            "total_ports": self.total_ports,
            "open_ports": self.open_ports,
            "closed_ports": self.closed_ports,
            "elapsed_seconds": round(self.elapsed_seconds, p),
            "ports_per_second": round(self.ports_per_second, p),
        }

    def render(self) -> str:
        d = self.to_dict()
        return (
            f"Scanned {d['total_ports']} ports in {d['elapsed_seconds']}s "
            f"({d['ports_per_second']} ports/sec) — "
            f"{d['open_ports']} open, {d['closed_ports']} closed"
        )


class Profiler:
    """Context-manager based profiler for a scan session."""

    def __init__(self, config: Optional[ProfilerConfig] = None) -> None:
        self.config = config or ProfilerConfig()
        self._start: float = 0.0
        self._end: float = 0.0

    def start(self) -> None:
        self._start = time.monotonic()

    def stop(self) -> None:
        self._end = time.monotonic()

    @property
    def elapsed(self) -> float:
        if self._end == 0.0:
            return time.monotonic() - self._start
        return self._end - self._start

    def build_profile(self, total_ports: int, open_ports: int) -> ScanProfile:
        return ScanProfile(
            total_ports=total_ports,
            open_ports=open_ports,
            elapsed_seconds=self.elapsed,
            precision=self.config.precision,
        )

    def __enter__(self) -> "Profiler":
        self.start()
        return self

    def __exit__(self, *_) -> None:
        self.stop()
