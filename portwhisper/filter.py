"""Result filtering utilities for portwhisper."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from portwhisper.scanner import ScanResult


@dataclass
class FilterConfig:
    """Configuration for result filtering."""

    only_open: bool = False
    services: List[str] = field(default_factory=list)
    min_port: int = 1
    max_port: int = 65535
    banner_required: bool = False

    def __post_init__(self) -> None:
        if not (1 <= self.min_port <= 65535):
            raise ValueError(f"min_port must be 1-65535, got {self.min_port}")
        if not (1 <= self.max_port <= 65535):
            raise ValueError(f"max_port must be 1-65535, got {self.max_port}")
        if self.min_port > self.max_port:
            raise ValueError(
                f"min_port ({self.min_port}) must be <= max_port ({self.max_port})"
            )
        self.services = [s.lower() for s in self.services]


def apply_filter(
    results: Sequence[ScanResult], cfg: Optional[FilterConfig] = None
) -> List[ScanResult]:
    """Return a filtered list of ScanResult objects according to *cfg*."""
    if cfg is None:
        return list(results)

    filtered: List[ScanResult] = []
    for r in results:
        if cfg.only_open and r.state != "open":
            continue
        if not (cfg.min_port <= r.port <= cfg.max_port):
            continue
        if cfg.services and (r.service or "").lower() not in cfg.services:
            continue
        if cfg.banner_required and not r.banner:
            continue
        filtered.append(r)
    return filtered
