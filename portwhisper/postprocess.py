"""Post-processing pipeline: filter, deduplicate, sort, and limit results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from portwhisper.scanner import ScanResult
from portwhisper.filter import FilterConfig, apply_filter
from portwhisper.deduplicator import DeduplicatorConfig, deduplicate_results
from portwhisper.sorter import SortKey, sort_results
from portwhisper.limiter import LimiterConfig, limit_ports


@dataclass
class PostprocessConfig:
    """Aggregate configuration for the post-processing pipeline."""

    filter: FilterConfig = field(default_factory=FilterConfig)
    deduplicator: DeduplicatorConfig = field(default_factory=DeduplicatorConfig)
    sort_key: SortKey = SortKey.PORT
    sort_descending: bool = False
    limiter: Optional[LimiterConfig] = None  # None → no port-range clamping


def postprocess(
    results: List[ScanResult],
    config: PostprocessConfig | None = None,
) -> List[ScanResult]:
    """Apply the full post-processing pipeline to a list of ScanResults.

    Steps (in order):
    1. Clamp to port range via LimiterConfig (if provided).
    2. Apply FilterConfig rules.
    3. Deduplicate via DeduplicatorConfig.
    4. Sort via SortKey.

    Args:
        results: Raw scan results.
        config: PostprocessConfig; defaults to PostprocessConfig().

    Returns:
        Processed list of ScanResult.
    """
    if config is None:
        config = PostprocessConfig()

    # Step 1 – optional port-range limiter
    if config.limiter is not None:
        allowed = set(limit_ports([r.port for r in results], config.limiter))
        results = [r for r in results if r.port in allowed]

    # Step 2 – filter
    results = apply_filter(results, config.filter)

    # Step 3 – deduplicate
    results = deduplicate_results(results, config.deduplicator)

    # Step 4 – sort
    results = sort_results(results, config.sort_key, config.sort_descending)

    return results
