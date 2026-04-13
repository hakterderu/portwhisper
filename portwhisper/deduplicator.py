"""Result deduplication utilities for portwhisper."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from portwhisper.scanner import ScanResult


@dataclass
class DeduplicatorConfig:
    """Configuration for result deduplication."""

    keep: str = "first"  # 'first' or 'last'

    def __post_init__(self) -> None:
        if self.keep not in ("first", "last"):
            raise ValueError("keep must be 'first' or 'last'")


def deduplicate_results(
    results: List[ScanResult],
    config: DeduplicatorConfig | None = None,
) -> List[ScanResult]:
    """Remove duplicate (host, port) entries from a list of ScanResults.

    When duplicates exist the *keep* strategy in *config* determines which
    entry survives:
    - ``'first'``: keep the first occurrence (default)
    - ``'last'``:  keep the last occurrence

    The relative order of surviving results is preserved.

    Args:
        results: Flat list of scan results, potentially containing duplicates.
        config:  Deduplication configuration.  Defaults to
                 ``DeduplicatorConfig()`` when *None*.

    Returns:
        A new list with duplicates removed according to the chosen strategy.
    """
    if config is None:
        config = DeduplicatorConfig()

    seen: Dict[Tuple[str, int], int] = {}

    if config.keep == "first":
        for idx, result in enumerate(results):
            key = (result.host, result.port)
            if key not in seen:
                seen[key] = idx
    else:  # 'last'
        for idx, result in enumerate(results):
            key = (result.host, result.port)
            seen[key] = idx

    # Rebuild list in original order using the surviving indices.
    surviving = set(seen.values())
    return [r for i, r in enumerate(results) if i in surviving]
