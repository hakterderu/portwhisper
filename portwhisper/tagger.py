"""Tag scan results with user-defined or automatic labels."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from portwhisper.scanner import ScanResult

# Well-known port → tag mapping used when auto-tagging is enabled
_AUTO_TAGS: Dict[int, str] = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    80: "http",
    110: "pop3",
    143: "imap",
    443: "https",
    445: "smb",
    3306: "mysql",
    5432: "postgres",
    6379: "redis",
    8080: "http-alt",
    27017: "mongodb",
}


@dataclass
class TaggerConfig:
    """Configuration for the result tagger."""

    auto_tag: bool = True
    extra_tags: Dict[int, str] = field(default_factory=dict)
    open_only: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.extra_tags, dict):
            raise TypeError("extra_tags must be a dict mapping port -> tag")


@dataclass
class TaggedResult:
    """A ScanResult decorated with a list of string tags."""

    result: ScanResult
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        base = self.result.to_dict()
        base["tags"] = self.tags
        return base


def tag_results(
    results: List[ScanResult],
    config: Optional[TaggerConfig] = None,
) -> List[TaggedResult]:
    """Apply tags to a list of ScanResults and return TaggedResults."""
    if config is None:
        config = TaggerConfig()

    tagged: List[TaggedResult] = []
    merged = {**_AUTO_TAGS, **config.extra_tags} if config.auto_tag else dict(config.extra_tags)

    for result in results:
        if config.open_only and result.state != "open":
            continue
        tag_label = merged.get(result.port)
        tags = [tag_label] if tag_label else []
        tagged.append(TaggedResult(result=result, tags=tags))

    return tagged
