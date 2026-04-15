"""Tests for portwhisper.formatter module."""

import pytest

from portwhisper.formatter import (
    FormatMode,
    FormatterConfig,
    format_results,
    _truncate,
)
from portwhisper.scanner import ScanResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_result(port: int, state: str = "open", service: str | None = None, banner: str | None = None) -> ScanResult:
    r = ScanResult(port=port)
    r._state = state
    r._service = service
    r._banner = banner
    return r


@pytest.fixture()
def mixed_results():
    return [
        make_result(22, "open", "ssh", "OpenSSH_8.9"),
        make_result(80, "open", "http", None),
        make_result(443, "closed", "https", None),
        make_result(8080, "open", None, None),
    ]


# ---------------------------------------------------------------------------
# FormatterConfig tests
# ---------------------------------------------------------------------------

def test_formatter_config_defaults():
    cfg = FormatterConfig()
    assert cfg.mode == FormatMode.TABLE
    assert cfg.show_closed is False
    assert cfg.max_banner_len == 60


def test_formatter_config_mode_from_string():
    cfg = FormatterConfig(mode="compact")
    assert cfg.mode == FormatMode.COMPACT


def test_formatter_config_invalid_banner_len():
    with pytest.raises(ValueError):
        FormatterConfig(max_banner_len=-1)


# ---------------------------------------------------------------------------
# _truncate tests
# ---------------------------------------------------------------------------

def test_truncate_short_string():
    assert _truncate("hello", 10) == "hello"


def test_truncate_exact_length():
    assert _truncate("hello", 5) == "hello"


def test_truncate_long_string():
    result = _truncate("hello world", 8)
    assert result.endswith("...")
    assert len(result) == 8


# ---------------------------------------------------------------------------
# format_results — TABLE mode
# ---------------------------------------------------------------------------

def test_table_contains_header(mixed_results):
    output = format_results(mixed_results)
    assert "PORT" in output
    assert "STATE" in output
    assert "SERVICE" in output


def test_table_hides_closed_by_default(mixed_results):
    output = format_results(mixed_results)
    assert "closed" not in output


def test_table_shows_closed_when_enabled(mixed_results):
    cfg = FormatterConfig(show_closed=True)
    output = format_results(mixed_results, cfg)
    assert "closed" in output


def test_table_shows_service(mixed_results):
    output = format_results(mixed_results)
    assert "ssh" in output


# ---------------------------------------------------------------------------
# format_results — COMPACT mode
# ---------------------------------------------------------------------------

def test_compact_format_open_ports(mixed_results):
    cfg = FormatterConfig(mode=FormatMode.COMPACT)
    output = format_results(mixed_results, cfg)
    assert "22/open" in output
    assert "80/open" in output


def test_compact_includes_service_in_parens(mixed_results):
    cfg = FormatterConfig(mode=FormatMode.COMPACT)
    output = format_results(mixed_results, cfg)
    assert "(ssh)" in output


def test_compact_includes_banner(mixed_results):
    cfg = FormatterConfig(mode=FormatMode.COMPACT)
    output = format_results(mixed_results, cfg)
    assert "OpenSSH_8.9" in output


# ---------------------------------------------------------------------------
# format_results — MINIMAL mode
# ---------------------------------------------------------------------------

def test_minimal_format_only_ports(mixed_results):
    cfg = FormatterConfig(mode=FormatMode.MINIMAL)
    lines = format_results(mixed_results, cfg).splitlines()
    assert all(line.isdigit() for line in lines)
    assert "22" in lines
    assert "443" not in lines


def test_minimal_shows_closed_when_enabled(mixed_results):
    cfg = FormatterConfig(mode=FormatMode.MINIMAL, show_closed=True)
    lines = format_results(mixed_results, cfg).splitlines()
    assert "443" in lines
