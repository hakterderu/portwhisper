"""Tests for portwhisper.enricher."""
from __future__ import annotations

import pytest

from portwhisper.scanner import ScanResult
from portwhisper.enricher import (
    EnricherConfig,
    EnrichedResult,
    enrich_results,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_result(port: int, state: str = "open", service: str | None = None) -> ScanResult:
    return ScanResult(host="127.0.0.1", port=port, state=state, service=service, banner=None)


# ---------------------------------------------------------------------------
# EnricherConfig
# ---------------------------------------------------------------------------

def test_enricher_config_defaults():
    cfg = EnricherConfig()
    assert cfg.add_description is True
    assert cfg.add_risk_flag is True
    assert isinstance(cfg.risky_ports, list)
    assert 23 in cfg.risky_ports


def test_enricher_config_invalid_risky_ports():
    with pytest.raises(TypeError):
        EnricherConfig(risky_ports="not-a-list")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# enrich_results – descriptions
# ---------------------------------------------------------------------------

def test_known_port_gets_description():
    results = enrich_results([make_result(80)])
    assert results[0].description is not None
    assert "HTTP" in results[0].description


def test_unknown_port_description_is_none():
    results = enrich_results([make_result(9999)])
    assert results[0].description is None


def test_description_disabled():
    cfg = EnricherConfig(add_description=False)
    results = enrich_results([make_result(80)], config=cfg)
    assert results[0].description is None


# ---------------------------------------------------------------------------
# enrich_results – risk flag
# ---------------------------------------------------------------------------

def test_risky_open_port_flagged():
    results = enrich_results([make_result(23, state="open")])
    assert results[0].is_risky is True


def test_risky_closed_port_not_flagged():
    results = enrich_results([make_result(23, state="closed")])
    assert results[0].is_risky is False


def test_safe_port_not_flagged():
    results = enrich_results([make_result(443, state="open")])
    assert results[0].is_risky is False


def test_risk_flag_disabled():
    cfg = EnricherConfig(add_risk_flag=False)
    results = enrich_results([make_result(23, state="open")], config=cfg)
    assert results[0].is_risky is False


# ---------------------------------------------------------------------------
# EnrichedResult.to_dict
# ---------------------------------------------------------------------------

def test_to_dict_contains_extra_keys():
    enriched = enrich_results([make_result(22)])
    d = enriched[0].to_dict()
    assert "description" in d
    assert "is_risky" in d


def test_to_dict_preserves_base_fields():
    enriched = enrich_results([make_result(22, service="ssh")])
    d = enriched[0].to_dict()
    assert d["port"] == 22
    assert d["state"] == "open"
    assert d["service"] == "ssh"


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------

def test_enrich_empty_list():
    assert enrich_results([]) == []
