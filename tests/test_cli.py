"""Tests for portwhisper.cli module."""

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from portwhisper.scanner import ScanResult
from portwhisper.cli import build_parser, parse_ports, run


@pytest.fixture
def open_results():
    return [
        ScanResult(host="127.0.0.1", port=22, open=True, service="ssh", banner=None, latency_ms=2.0),
        ScanResult(host="127.0.0.1", port=9999, open=False, service=None, banner=None, latency_ms=None),
    ]


def test_parse_ports_single():
    assert parse_ports("80") == [80]


def test_parse_ports_range():
    assert parse_ports("20-22") == [20, 21, 22]


def test_parse_ports_mixed():
    result = parse_ports("22,80,443")
    assert result == [22, 80, 443]


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["localhost"])
    assert args.host == "localhost"
    assert args.ports == "1-1024"
    assert args.timeout == 1.0
    assert args.concurrency == 200
    assert args.format == "json"
    assert args.no_fingerprint is False


def test_build_parser_custom_flags():
    parser = build_parser()
    args = parser.parse_args([
        "10.0.0.1", "-p", "80,443", "-t", "0.5", "-c", "50",
        "--format", "csv", "--no-fingerprint",
    ])
    assert args.ports == "80,443"
    assert args.timeout == 0.5
    assert args.concurrency == 50
    assert args.format == "csv"
    assert args.no_fingerprint is True


@pytest.mark.asyncio
async def test_run_no_output(open_results, capsys):
    parser = build_parser()
    args = parser.parse_args(["127.0.0.1", "-p", "22", "--no-fingerprint"])

    with patch("portwhisper.cli.scan", new=AsyncMock(return_value=open_results)):
        code = await run(args)

    assert code == 0
    captured = capsys.readouterr()
    assert "1 open port" in captured.out
    assert "22" in captured.out


@pytest.mark.asyncio
async def test_run_json_output(open_results, tmp_path, capsys):
    dest = tmp_path / "out.json"
    parser = build_parser()
    args = parser.parse_args([
        "127.0.0.1", "-p", "22", "--no-fingerprint", "-o", str(dest),
    ])

    with patch("portwhisper.cli.scan", new=AsyncMock(return_value=open_results)):
        await run(args)

    assert dest.exists()
    data = json.loads(dest.read_text())
    assert any(r["port"] == 22 for r in data)


@pytest.mark.asyncio
async def test_run_csv_output(open_results, tmp_path):
    dest = tmp_path / "out.csv"
    parser = build_parser()
    args = parser.parse_args([
        "127.0.0.1", "-p", "22", "--no-fingerprint", "-o", str(dest),
    ])

    with patch("portwhisper.cli.scan", new=AsyncMock(return_value=open_results)):
        await run(args)

    assert dest.exists()
    content = dest.read_text()
    assert "host" in content
    assert "22" in content
