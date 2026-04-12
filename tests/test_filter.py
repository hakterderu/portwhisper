"""Tests for portwhisper.filter module."""
import pytest

from portwhisper.scanner import ScanResult
from portwhisper.filter import FilterConfig, apply_filter


def make_result(
    port: int,
    state: str = "open",
    service: str | None = None,
    banner: str | None = None,
) -> ScanResult:
    return ScanResult(host="127.0.0.1", port=port, state=state, service=service, banner=banner)


# ---------------------------------------------------------------------------
# FilterConfig validation
# ---------------------------------------------------------------------------

def test_filter_config_defaults():
    cfg = FilterConfig()
    assert cfg.only_open is False
    assert cfg.services == []
    assert cfg.min_port == 1
    assert cfg.max_port == 65535
    assert cfg.banner_required is False


def test_filter_config_invalid_min_port():
    with pytest.raises(ValueError, match="min_port"):
        FilterConfig(min_port=0)


def test_filter_config_invalid_max_port():
    with pytest.raises(ValueError, match="max_port"):
        FilterConfig(max_port=70000)


def test_filter_config_min_greater_than_max():
    with pytest.raises(ValueError, match="min_port"):
        FilterConfig(min_port=8080, max_port=80)


def test_filter_config_services_lowercased():
    cfg = FilterConfig(services=["HTTP", "SSH"])
    assert cfg.services == ["http", "ssh"]


# ---------------------------------------------------------------------------
# apply_filter
# ---------------------------------------------------------------------------

def test_apply_filter_none_config_returns_all():
    results = [make_result(80), make_result(443, state="closed")]
    assert apply_filter(results, None) == results


def test_apply_filter_only_open():
    results = [make_result(80), make_result(443, state="closed")]
    out = apply_filter(results, FilterConfig(only_open=True))
    assert len(out) == 1
    assert out[0].port == 80


def test_apply_filter_port_range():
    results = [make_result(22), make_result(80), make_result(8080)]
    out = apply_filter(results, FilterConfig(min_port=25, max_port=1000))
    assert len(out) == 1
    assert out[0].port == 80


def test_apply_filter_by_service():
    results = [
        make_result(22, service="ssh"),
        make_result(80, service="http"),
        make_result(443, service="https"),
    ]
    out = apply_filter(results, FilterConfig(services=["HTTP", "HTTPS"]))
    assert {r.port for r in out} == {80, 443}


def test_apply_filter_banner_required():
    results = [
        make_result(22, banner="OpenSSH 8.0"),
        make_result(80, banner=None),
    ]
    out = apply_filter(results, FilterConfig(banner_required=True))
    assert len(out) == 1
    assert out[0].port == 22


def test_apply_filter_empty_results():
    assert apply_filter([], FilterConfig(only_open=True)) == []
