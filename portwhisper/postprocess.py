"""Post-processing pipeline: filter → deduplicate → sort → tag → enrich."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from portwhisper.scanner import ScanResult
from portwhisper.filter import FilterConfig, apply_filter
from portwhisper.deduplicator import DeduplicatorConfig, deduplicate_results
from portwhisper.sorter import SortKey, sort_results
from portwhisper.tagger import TaggerConfig, TaggedResult, tag_results


@dataclass
class PostprocessConfig:
    """Unified configuration for the post-processing pipeline."""

    filter: FilterConfig = field(default_factory=FilterConfig)
    deduplicator: DeduplicatorConfig = field(default_factory=DeduplicatorConfig)
    sort_key: SortKey = SortKey.PORT
    sort_reverse: bool = False
    open_only: bool = False
    tagger: TaggerConfig = field(default_factory=TaggerConfig)
    apply_tags: bool = False


def postprocess(
    results: List[ScanResult],
    config: Optional[PostprocessConfig] = None,
) -> List[ScanResult]:
    """Run the full post-processing pipeline and return filtered ScanResults.

    Tagging is applied internally but the returned list is plain ScanResults
    so downstream consumers remain decoupled from TaggedResult.  Use
    ``tag_results`` directly when tagged output is required.
    """
    if config is None:
        config = PostprocessConfig()

    processed = list(results)

    if config.open_only:
        processed = [r for r in processed if r.state == "open"]

    processed = apply_filter(processed, config.filter)
    processed = deduplicate_results(processed, config.deduplicator)
    processed = sort_results(processed, config.sort_key, reverse=config.sort_reverse)

    return processed
