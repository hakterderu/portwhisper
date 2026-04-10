"""Tests for portwhisper.exporter module."""

import csv
import io
import json
import tempfile
from pathlib import Path

import pytest

from portwhisper.scanner import ScanResult
from portwhisper.exporter import export_json, export_csv, results_to_dict


@pytest.fixture
def sample_results():
    return [
        ScanResult(host="127.0.0.1", port=22, open=True, service="ssh", banner="OpenSSH", latency_ms=3.5),
        ScanResult(host="127.0.0.1", port=80, open=True, service="http", banner=None, latency_ms=1.2),
        ScanResult(host="127.0.0.1", port=9999, open=False, service=None, banner=None, latency_ms=None),
    ]


def test_results_to_dict_length(sample_results):
    dicts = results_to_dict(sample_results)
    assert len(dicts) == 3


def test_results_to_dict_fields(sample_results):
    d = results_to_dict(sample_results)[0]
    assert d["host"] == "127.0.0.1"
    assert d["port"] == 22
    assert d["open"] is True
    assert d["service"] == "ssh"
    assert d["banner"] == "OpenSSH"
    assert d["latency_ms"] == 3.5


def test_results_to_dict_none_values(sample_results):
    d = results_to_dict(sample_results)[2]
    assert d["service"] == ""
    assert d["banner"] == ""
    assert d["latency_ms"] is None


def test_export_json_returns_valid_json(sample_results):
    output = export_json(sample_results)
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 3
    assert parsed[0]["port"] == 22


def test_export_json_writes_file(sample_results, tmp_path):
    dest = tmp_path / "results.json"
    export_json(sample_results, destination=dest)
    assert dest.exists()
    data = json.loads(dest.read_text())
    assert len(data) == 3


def test_export_csv_returns_string(sample_results):
    output = export_csv(sample_results)
    assert isinstance(output, str)
    assert "host" in output
    assert "22" in output


def test_export_csv_has_header(sample_results):
    output = export_csv(sample_results)
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 3
    assert rows[0]["service"] == "ssh"


def test_export_csv_writes_file(sample_results, tmp_path):
    dest = tmp_path / "results.csv"
    export_csv(sample_results, destination=dest)
    assert dest.exists()
    content = dest.read_text()
    assert "80" in content
