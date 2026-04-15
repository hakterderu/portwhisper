"""Tests for the updated portwhisper.postprocess (includes tagger integration)."""
import pytest
from portwhisper.scanner import ScanResult
from portwhisper.postprocess import PostprocessConfig, postprocess
from portwhisper.tagger import TaggerConfig, tag_results
from portwhisper.sorter import SortKey


def make_result(
    port: int,
    state: str = "open",
    service: str | None = None,
    host: str = "127.0.0.1",
) -> ScanResult:
    return ScanResult(host=host, port=port, state=state, service=service, banner=None)


def test_postprocess_config_defaults():
    cfg = PostprocessConfig()
    assert cfg.open_only is False
    assert cfg.sort_key == SortKey.PORT
    assert cfg.sort_reverse is False
    assert cfg.apply_tags is False


def test_postprocess_empty_input():
    assert postprocess([]) == []


def test_postprocess_default_config_passthrough():
    results = [make_result(80), make_result(443)]
    out = postprocess(results)
    assert len(out) == 2


def test_postprocess_filter_open_only():
    results = [make_result(80), make_result(22, state="closed")]
    cfg_only=True)
    out = postprocess(results, config=cfg)
    assert all(r.state == "open" for r in out)
    assert len(out) == 1


def test_postprocess_sort_descending():
    results = [make_result(80), make_result(22), make_result(443)]
    cfg = PostprocessConfig(sort_key=SortKey.PORT, sort_reverse=True)
    out = postprocess(results, config=cfg)
    ports = [r.port for r in out]
    assert ports == sorted(ports, reverse=True)


def test_postprocess_deduplication():
    results = [make(80), make_result(443)]
    out = postprocess(results)
    ports = [r.port for r in out]
    assert ports.count(80) == 1


def test_postprocess_returns_scan_results():
    results = [make_result(22)]
    out = postprocess(results)
    assert all(isinstance(r, ScanResult) for r in out)


def test_tagger_integration_via_tag_results():
    """Verify that tag_results can be chained after postprocess."""
    results = [make_result(80), make_result(22, state="closed")]
    cfg = PostprocessConfig(open_only=True)
    processed = postprocess(results, config=cfg)
    tagged = tag_results(processed, TaggerConfig(auto_tag=True, open_only=False))
    assert len(tagged) == 1
    assert tagged[0].tags == ["http"]
