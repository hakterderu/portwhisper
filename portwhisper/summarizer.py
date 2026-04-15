"""Summarizer module: produces a human-readable scan summary from aggregate stats."""

from dataclasses import dataclass, field
from typing import List, Optional

from portwhisper.aggregator import AggregateStats


@dataclass
class SummaryConfig:
    show_ratio: bool = True
    show_top_services: bool = True
    top_n: int = 5

    def __post_init__(self) -> None:
        if self.top_n < 1:
            raise ValueError("top_n must be at least 1")


@dataclass
class ScanSummary:
    host: str
    total: int
    open_count: int
    closed_count: int
    filtered_count: int
    open_ratio: float
    top_services: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "total": self.total,
            "open": self.open_count,
            "closed": self.closed_count,
            "filtered": self.filtered_count,
            "open_ratio": round(self.open_ratio, 4),
            "top_services": self.top_services,
        }

    def render(self) -> str:
        lines = [
            f"Host       : {self.host}",
            f"Total      : {self.total}",
            f"Open       : {self.open_count}",
            f"Closed     : {self.closed_count}",
            f"Filtered   : {self.filtered_count}",
            f"Open ratio : {self.open_ratio:.2%}",
        ]
        if self.top_services:
            lines.append("Top services: " + ", ".join(self.top_services))
        return "\n".join(lines)


def summarize(
    host: str,
    stats: AggregateStats,
    config: Optional[SummaryConfig] = None,
) -> ScanSummary:
    """Build a ScanSummary from an AggregateStats object."""
    if config is None:
        config = SummaryConfig()

    top_services: List[str] = []
    if config.show_top_services and stats.service_counts:
        sorted_services = sorted(
            stats.service_counts.items(), key=lambda kv: kv[1], reverse=True
        )
        top_services = [svc for svc, _ in sorted_services[: config.top_n]]

    return ScanSummary(
        host=host,
        total=stats.total,
        open_count=stats.open_count,
        closed_count=stats.closed_count,
        filtered_count=stats.filtered_count,
        open_ratio=stats.open_ratio() if config.show_ratio else 0.0,
        top_services=top_services,
    )
