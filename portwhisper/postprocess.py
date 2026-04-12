"""High-level post-processing pipeline: filter then sort scan results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from portwhisper.scanner import ScanResult
from portwhisper.filter import FilterConfig, apply_filter
from portwhisper.sorter import SortKey, sort_results


@dataclass
class PostprocessConfig:
    """Combined configuration for filtering and sorting."""

    filter: Optional[FilterConfig] = None
    sort_key: SortKey = SortKey.PORT
    sort_reverse: bool = False


def postprocess(
    results: Sequence[ScanResult],
    cfg: Optional[PostprocessConfig] = None,
) -> List[ScanResult]:
    """Apply filtering and sorting to *results*.

    If *cfg* is ``None`` results are returned as-is (as a new list).
    """
    if cfg is None:
        return list(results)

    filtered = apply_filter(results, cfg.filter)
    return sort_results(filtered, key=cfg.sort_key, reverse=cfg.sort_reverse)
