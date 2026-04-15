"""Tests for portwhisper.tagger."""
import pytest
from portwhisper.scanner import ScanResult
from portwhisper.tagger import (
    TaggerConfig,
    TaggedResult,
    tag_results,
)


def make_result(port: int, state: str = "open", service: str | None = None) -> ScanResult:
    return ScanResult(host="127.0.0.1", port=port, state=state, service=service, banner=None)


# ---------------------------------------------------------------------------
# TaggerConfig
# ---------------------------------------------------------------------------

def test_tagger_config_defaults():
    cfg = TaggerConfig()
    assert cfg.auto_tag is True
    assert cfg.extra_tags == {}
    assert cfg.open_only is True


def test_tagger_config_invalid_extra_tags():
    with pytest.raises(TypeError):
        TaggerConfig(extra_tags="bad")  # type: ignore


# ---------------------------------------------------------------------------
# TaggedResult
# ---------------------------------------------------------------------------

def test_tagged_result_to_dict_includes_tags():
    r = make_result(80)
    tr = TaggedResult(result=r, tags=["http"])
    d = tr.to_dict()
    assert "tags" in d
    assert d["tags"] == ["http"]
    assert d["port"] == 80


def test_tagged_result_empty_tags():
    r = make_result(9999)
    tr = TaggedResult(result=r, tags=[])
    assert tr.to_dict()["tags"] == []


# ---------------------------------------------------------------------------
# tag_results
# ---------------------------------------------------------------------------

def test_tag_results_known_port_auto_tagged():
    results = [make_result(80)]
    tagged = tag_results(results)
    assert len(tagged) == 1
    assert tagged[0].tags == ["http"]


def test_tag_results_unknown_port_no_tag():
    results = [make_result(9999)]
    tagged = tag_results(results)
    assert len(tagged) == 1
    assert tagged[0].tags == []


def test_tag_results_closed_excluded_by_default():
    results = [make_result(22, state="closed")]
    tagged = tag_results(results)
    assert tagged == []


def test_tag_results_closed_included_when_open_only_false():
    cfg = TaggerConfig(open_only=False)
    results = [make_result(22, state="closed")]
    tagged = tag_results(results, config=cfg)
    assert len(tagged) == 1


def test_tag_results_extra_tags_override():
    cfg = TaggerConfig(extra_tags={9999: "custom-service"})
    results = [make_result(9999)]
    tagged = tag_results(results, config=cfg)
    assert tagged[0].tags == ["custom-service"]


def test_tag_results_auto_tag_disabled_ignores_known_ports():
    cfg = TaggerConfig(auto_tag=False)
    results = [make_result(80)]
    tagged = tag_results(results, config=cfg)
    assert tagged[0].tags == []


def test_tag_results_multiple_ports():
    results = [make_result(22), make_result(443), make_result(9999)]
    tagged = tag_results(results)
    tag_map = {t.result.port: t.tags for t in tagged}
    assert tag_map[22] == ["ssh"]
    assert tag_map[443] == ["https"]
    assert tag_map[9999] == []


def test_tag_results_none_config_uses_defaults():
    results = [make_result(53)]
    tagged = tag_results(results, config=None)
    assert tagged[0].tags == ["dns"]
