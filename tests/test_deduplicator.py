"""Tests for portwhisper.deduplicator."""

import pytest

from portwhisper.scanner import ScanResult
from portwhisper.deduplicator import DeduplicatorConfig, deduplicate_results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_result(host: str, port: int, state: str = "open", service: str | None = None) -> ScanResult:
    return ScanResult(host=host, port=port, state=state, service=service, banner=None)


# ---------------------------------------------------------------------------
# DeduplicatorConfig
# ---------------------------------------------------------------------------

def test_deduplicator_config_defaults():
    cfg = DeduplicatorConfig()
    assert cfg.keep == "first"


def test_deduplicator_config_last():
    cfg = DeduplicatorConfig(keep="last")
    assert cfg.keep == "last"


def test_deduplicator_config_invalid():
    with pytest.raises(ValueError, match="keep must be"):
        DeduplicatorConfig(keep="random")


# ---------------------------------------------------------------------------
# deduplicate_results — no duplicates
# ---------------------------------------------------------------------------

def test_deduplicate_no_duplicates():
    results = [make_result("127.0.0.1", 80), make_result("127.0.0.1", 443)]
    out = deduplicate_results(results)
    assert len(out) == 2


def test_deduplicate_empty_list():
    assert deduplicate_results([]) == []


# ---------------------------------------------------------------------------
# deduplicate_results — keep='first' (default)
# ---------------------------------------------------------------------------

def test_deduplicate_keep_first_preserves_first():
    r1 = make_result("10.0.0.1", 22, state="open", service="ssh")
    r2 = make_result("10.0.0.1", 22, state="closed", service=None)
    out = deduplicate_results([r1, r2])
    assert len(out) == 1
    assert out[0].state == "open"
    assert out[0].service == "ssh"


def test_deduplicate_keep_first_order_preserved():
    results = [
        make_result("host", 80),
        make_result("host", 443),
        make_result("host", 80),  # duplicate
    ]
    out = deduplicate_results(results)
    assert [r.port for r in out] == [80, 443]


# ---------------------------------------------------------------------------
# deduplicate_results — keep='last'
# ---------------------------------------------------------------------------

def test_deduplicate_keep_last_preserves_last():
    cfg = DeduplicatorConfig(keep="last")
    r1 = make_result("10.0.0.1", 22, state="open", service="ssh")
    r2 = make_result("10.0.0.1", 22, state="closed", service=None)
    out = deduplicate_results([r1, r2], config=cfg)
    assert len(out) == 1
    assert out[0].state == "closed"


def test_deduplicate_keep_last_order_preserved():
    cfg = DeduplicatorConfig(keep="last")
    results = [
        make_result("host", 80, service="http"),
        make_result("host", 443),
        make_result("host", 80, service="https"),  # duplicate — should win
    ]
    out = deduplicate_results(results, config=cfg)
    assert len(out) == 2
    port_map = {r.port: r for r in out}
    assert port_map[80].service == "https"


# ---------------------------------------------------------------------------
# deduplicate_results — multi-host
# ---------------------------------------------------------------------------

def test_deduplicate_different_hosts_not_merged():
    results = [
        make_result("192.168.1.1", 80),
        make_result("192.168.1.2", 80),
    ]
    out = deduplicate_results(results)
    assert len(out) == 2
