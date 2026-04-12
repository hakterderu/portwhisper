"""Result sorting utilities for portwhisper."""
from __future__ import annotations

from enum import Enum
from typing import List, Sequence

from portwhisper.scanner import ScanResult


class SortKey(str, Enum):
    PORT = "port"
    STATE = "state"
    SERVICE = "service"
    HOST = "host"


def sort_results(
    results: Sequence[ScanResult],
    key: SortKey = SortKey.PORT,
    reverse: bool = False,
) -> List[ScanResult]:
    """Return a sorted copy of *results* by *key*.

    None values are sorted last regardless of *reverse*.
    """
    _NONE_HIGH = "\xff" * 8  # sentinel that sorts after any real string

    def _key_fn(r: ScanResult) -> str:
        if key is SortKey.PORT:
            # Zero-pad for lexicographic stability; return str so type is uniform.
            return f"{r.port:05d}"
        if key is SortKey.STATE:
            return r.state or _NONE_HIGH
        if key is SortKey.SERVICE:
            return (r.service or _NONE_HIGH).lower()
        if key is SortKey.HOST:
            return r.host or _NONE_HIGH
        return f"{r.port:05d}"  # fallback

    return sorted(results, key=_key_fn, reverse=reverse)
