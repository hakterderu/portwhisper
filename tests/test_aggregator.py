"""Tests for portwhisper.aggregator."""
from __future__ import annotations

import pytest

from portwhisper.scanner import ScanResult
from portwhisper.aggregator import AggregateStats, aggregate_results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_result(port: int, state: str = "open", service: str | None = None) -> ScanResult:
    return ScanResult(port=port, state=state, service=service, banner=None)


# ---------------------------------------------------------------------------
# AggregateStats unit tests
# ---------------------------------------------------------------------------

def test_aggregate_stats_defaults():
    stats = AggregateStats()
    assert stats.total == 0
    assert stats.open_count == 0
    assert stats.closed_count == 0
    assert stats.filtered_count == 0
    assert stats.service_counts == {}
    assert stats.open_ports == []


def test_open_ratio_zero_total():
    stats = AggregateStats(total=0)
    assert stats.open_ratio == 0.0


def test_open_ratio_computed():
    stats = AggregateStats(total=10, open_count=3)
    assert abs(stats.open_ratio - 0.3) < 1e-9


def test_to_dict_keys():
    stats = AggregateStats(total=5, open_count=2, closed_count=3)
    d = stats.to_dict()
    assert set(d.keys()) == {"total", "open", "closed", "filtered", "open_ratio", "service_counts", "open_ports"}


# ---------------------------------------------------------------------------
# aggregate_results tests
# ---------------------------------------------------------------------------

def test_aggregate_empty():
    stats = aggregate_results([])
    assert stats.total == 0
    assert stats.open_count == 0


def test_aggregate_counts_open_closed():
    results = [
        make_result(80, "open"),
        make_result(443, "open"),
        make_result(22, "closed"),
    ]
    stats = aggregate_results(results)
    assert stats.total == 3
    assert stats.open_count == 2
    assert stats.closed_count == 1
    assert stats.filtered_count == 0


def test_aggregate_filtered_counted():
    results = [make_result(8080, "filtered")]
    stats = aggregate_results(results)
    assert stats.filtered_count == 1
    assert stats.open_count == 0


def test_aggregate_open_ports_sorted():
    results = [
        make_result(443, "open"),
        make_result(80, "open"),
        make_result(22, "open"),
    ]
    stats = aggregate_results(results)
    assert stats.open_ports == [22, 80, 443]


def test_aggregate_service_counts():
    results = [
        make_result(80, "open", service="http"),
        make_result(8080, "open", service="http"),
        make_result(22, "open", service="ssh"),
        make_result(9999, "open", service=None),
    ]
    stats = aggregate_results(results)
    assert stats.service_counts["http"] == 2
    assert stats.service_counts["ssh"] == 1
    assert stats.service_counts["unknown"] == 1


def test_aggregate_to_dict_values():
    results = [make_result(80, "open", service="http"), make_result(22, "closed")]
    d = aggregate_results(results).to_dict()
    assert d["total"] == 2
    assert d["open"] == 1
    assert d["closed"] == 1
    assert d["open_ports"] == [80]
