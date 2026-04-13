"""Result aggregation: summarise scan output into counts and statistics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from portwhisper.scanner import ScanResult


@dataclass
class AggregateStats:
    """Summary statistics derived from a collection of ScanResults."""

    total: int = 0
    open_count: int = 0
    closed_count: int = 0
    filtered_count: int = 0
    service_counts: Dict[str, int] = field(default_factory=dict)
    open_ports: List[int] = field(default_factory=list)

    @property
    def open_ratio(self) -> float:
        """Fraction of scanned ports that are open (0.0 – 1.0)."""
        if self.total == 0:
            return 0.0
        return self.open_count / self.total

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "open": self.open_count,
            "closed": self.closed_count,
            "filtered": self.filtered_count,
            "open_ratio": round(self.open_ratio, 4),
            "service_counts": self.service_counts,
            "open_ports": self.open_ports,
        }


def aggregate_results(results: Sequence[ScanResult]) -> AggregateStats:
    """Compute aggregate statistics from *results*.

    Args:
        results: Iterable of :class:`~portwhisper.scanner.ScanResult` objects.

    Returns:
        An :class:`AggregateStats` instance populated with counts and
        per-service breakdowns.
    """
    stats = AggregateStats(total=len(results))

    for r in results:
        state = r.state.lower() if hasattr(r.state, "lower") else str(r.state).lower()

        if state == "open":
            stats.open_count += 1
            stats.open_ports.append(r.port)
        elif state == "closed":
            stats.closed_count += 1
        else:
            stats.filtered_count += 1

        service = r.service or "unknown"
        stats.service_counts[service] = stats.service_counts.get(service, 0) + 1

    stats.open_ports.sort()
    return stats
