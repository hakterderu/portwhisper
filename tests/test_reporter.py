"""Tests for portwhisper.reporter."""

from __future__ import annotations

import pytest
from portwhisper.scanner import ScanResult
from portwhisper.reporter import format_result_line, build_report


@pytest.fixture()
def sample_results() -> list[ScanResult]:
    return [
        ScanResult(port=22, status="open", service="ssh", banner="OpenSSH_8.9"),
        ScanResult(port=80, status="open", service="http", banner=None),
        ScanResult(port=443, status="closed", service="https", banner=None),
        ScanResult(port=9999, status="filtered", service=None, banner=None),
    ]


def test_format_result_line_open_with_banner():
    r = ScanResult(port=22, status="open", service="ssh", banner="OpenSSH_8.9")
    line = format_result_line(r, use_color=False)
    assert "22" in line
    assert "OPEN" in line
    assert "ssh" in line
    assert "OpenSSH_8.9" in line


def test_format_result_line_closed_no_banner():
    r = ScanResult(port=443, status="closed", service="https", banner=None)
    line = format_result_line(r, use_color=False)
    assert "443" in line
    assert "CLOSED" in line
    assert "https" in line
    assert "|" not in line


def test_format_result_line_unknown_service():
    r = ScanResult(port=9999, status="filtered", service=None, banner=None)
    line = format_result_line(r, use_color=False)
    assert "unknown" in line


def test_build_report_contains_host(sample_results):
    report = build_report(sample_results, host="192.168.1.1", use_color=False)
    assert "192.168.1.1" in report


def test_build_report_open_ports_visible(sample_results):
    report = build_report(sample_results, host="localhost", use_color=False)
    assert "22" in report
    assert "80" in report


def test_build_report_closed_hidden_by_default(sample_results):
    report = build_report(sample_results, host="localhost", use_color=False)
    assert "443" not in report


def test_build_report_show_closed(sample_results):
    report = build_report(
        sample_results, host="localhost", use_color=False, show_closed=True
    )
    assert "443" in report


def test_build_report_summary_line(sample_results):
    report = build_report(sample_results, host="localhost", use_color=False)
    assert "2 open port(s) out of 4 scanned" in report


def test_build_report_no_open_ports():
    results = [
        ScanResult(port=80, status="closed", service="http", banner=None),
    ]
    report = build_report(results, host="localhost", use_color=False)
    assert "No open ports found" in report


def test_build_report_custom_title(sample_results):
    report = build_report(
        sample_results, host="localhost", use_color=False, title="My Custom Scan"
    )
    assert "My Custom Scan" in report
