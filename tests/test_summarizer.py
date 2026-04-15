"""Tests for portwhisper.summarizer."""

import pytest

from portwhisper.aggregator import AggregateStats
from portwhisper.summarizer import SummaryConfig, ScanSummary, summarize


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_stats(
    total=10, open_count=3, closed_count=6, filtered_count=1,
    service_counts=None
) -> AggregateStats:
    return AggregateStats(
        total=total,
        open_count=open_count,
        closed_count=closed_count,
        filtered_count=filtered_count,
        service_counts=service_counts or {},
    )


# ---------------------------------------------------------------------------
# SummaryConfig
# ---------------------------------------------------------------------------

def test_summary_config_defaults():
    cfg = SummaryConfig()
    assert cfg.show_ratio is True
    assert cfg.show_top_services is True
    assert cfg.top_n == 5


def test_summary_config_invalid_top_n():
    with pytest.raises(ValueError):
        SummaryConfig(top_n=0)


# ---------------------------------------------------------------------------
# summarize()
# ---------------------------------------------------------------------------

def test_summarize_basic_counts():
    stats = make_stats()
    summary = summarize("127.0.0.1", stats)
    assert summary.host == "127.0.0.1"
    assert summary.total == 10
    assert summary.open_count == 3
    assert summary.closed_count == 6
    assert summary.filtered_count == 1


def test_summarize_open_ratio():
    stats = make_stats(total=10, open_count=5)
    summary = summarize("localhost", stats)
    assert abs(summary.open_ratio - 0.5) < 1e-6


def test_summarize_ratio_disabled():
    stats = make_stats()
    cfg = SummaryConfig(show_ratio=False)
    summary = summarize("localhost", stats, config=cfg)
    assert summary.open_ratio == 0.0


def test_summarize_top_services_sorted():
    stats = make_stats(
        service_counts={"http": 5, "ssh": 10, "ftp": 2}
    )
    summary = summarize("host", stats, config=SummaryConfig(top_n=2))
    assert summary.top_services == ["ssh", "http"]


def test_summarize_top_services_disabled():
    stats = make_stats(service_counts={"http": 5})
    cfg = SummaryConfig(show_top_services=False)
    summary = summarize("host", stats, config=cfg)
    assert summary.top_services == []


def test_summarize_no_services():
    stats = make_stats(service_counts={})
    summary = summarize("host", stats)
    assert summary.top_services == []


# ---------------------------------------------------------------------------
# ScanSummary.to_dict / render
# ---------------------------------------------------------------------------

def test_to_dict_keys():
    stats = make_stats()
    summary = summarize("10.0.0.1", stats)
    d = summary.to_dict()
    assert set(d.keys()) == {"host", "total", "open", "closed", "filtered", "open_ratio", "top_services"}


def test_render_contains_host():
    stats = make_stats()
    summary = summarize("scanme.example.com", stats)
    rendered = summary.render()
    assert "scanme.example.com" in rendered


def test_render_contains_open_ratio():
    stats = make_stats(total=4, open_count=1)
    summary = summarize("h", stats)
    rendered = summary.render()
    assert "25.00%" in rendered
