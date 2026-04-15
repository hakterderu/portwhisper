"""Tests for portwhisper.postprocess (pipeline integration)."""

from __future__ import annotations

from typing import List

import pytest

from portwhisper.scanner import ScanResult
from portwhisper.filter import FilterConfig
from portwhisper.deduplicator import DeduplicatorConfig
from portwhisper.sorter import SortKey
from portwhisper.limiter import LimiterConfig
from portwhisper.postprocess import PostprocessConfig, postprocess


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_result(
    port: int,
    state: str = "open",
    service: str | None = None,
    banner: str | None = None,
) -> ScanResult:
    return ScanResult(host="127.0.0.1", port=port, state=state, service=service, banner=banner)


# ---------------------------------------------------------------------------
# PostprocessConfig defaults
# ---------------------------------------------------------------------------


def test_postprocess_config_defaults() -> None:
    cfg = PostprocessConfig()
    assert cfg.sort_key == SortKey.PORT
    assert cfg.sort_descending is False
    assert cfg.limiter is None


# ---------------------------------------------------------------------------
# postprocess – default pipeline
# ---------------------------------------------------------------------------


def test_postprocess_empty_input() -> None:
    assert postprocess([]) == []


def test_postprocess_default_config_passthrough() -> None:
    results = [make_result(80), make_result(443), make_result(22)]
    processed = postprocess(results)
    # Default filter keeps all; sorted by port ascending
    assert [r.port for r in processed] == [22, 80, 443]


def test_postprocess_filter_open_only() -> None:
    results = [
        make_result(22, state="open"),
        make_result(23, state="closed"),
        make_result(80, state="open"),
    ]
    cfg = PostprocessConfig(filter=FilterConfig(states=["open"]))
    processed = postprocess(results, cfg)
    assert all(r.state == "open" for r in processed)
    assert len(processed) == 2


def test_postprocess_deduplication_keeps_first() -> None:
    results = [
        make_result(80, banner="apache"),
        make_result(80, banner="nginx"),
    ]
    cfg = PostprocessConfig(deduplicator=DeduplicatorConfig(strategy="first"))
    processed = postprocess(results, cfg)
    assert len(processed) == 1
    assert processed[0].banner == "apache"


def test_postprocess_sort_descending() -> None:
    results = [make_result(p) for p in [22, 443, 80]]
    cfg = PostprocessConfig(sort_descending=True)
    processed = postprocess(results, cfg)
    assert [r.port for r in processed] == [443, 80, 22]


def test_postprocess_limiter_clamps_ports() -> None:
    results = [make_result(p) for p in [22, 80, 443, 8080, 9090]]
    cfg = PostprocessConfig(limiter=LimiterConfig(min_port=80, max_port=1000))
    processed = postprocess(results, cfg)
    assert all(80 <= r.port <= 1000 for r in processed)
    assert {r.port for r in processed} == {80, 443}


def test_postprocess_none_config_uses_defaults() -> None:
    results = [make_result(443), make_result(80)]
    assert postprocess(results, None) == postprocess(results, PostprocessConfig())
