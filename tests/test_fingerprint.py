"""Tests for service fingerprinting logic."""

import pytest

from portwhisper.fingerprint import annotate_results, fingerprint_service
from portwhisper.scanner import ScanResult


def make_result(port: int, state: str = "open", banner: str = None) -> ScanResult:
    return ScanResult(host="127.0.0.1", port=port, state=state, banner=banner)


def test_fingerprint_closed_port_returns_none():
    result = make_result(22, state="closed")
    assert fingerprint_service(result) is None


def test_fingerprint_known_port_no_banner():
    assert fingerprint_service(make_result(22)) == "ssh"
    assert fingerprint_service(make_result(80)) == "http"
    assert fingerprint_service(make_result(3306)) == "mysql"
    assert fingerprint_service(make_result(6379)) == "redis"


def test_fingerprint_unknown_port_no_banner():
    assert fingerprint_service(make_result(12345)) is None


def test_fingerprint_banner_takes_priority():
    # Port 80 would normally be 'http', but banner says SSH
    result = make_result(80, banner="SSH-2.0-OpenSSH_8.9")
    assert fingerprint_service(result) == "ssh"


def test_fingerprint_redis_banner():
    result = make_result(12345, banner="redis_version:7.0.0")
    assert fingerprint_service(result) == "redis"


def test_fingerprint_postgresql_banner():
    result = make_result(5432, banner="PostgreSQL 15.1")
    assert fingerprint_service(result) == "postgresql"


def test_annotate_results_mutates_in_place():
    results = [
        make_result(22),
        make_result(80),
        make_result(9999, state="closed"),
    ]
    annotated = annotate_results(results)
    assert annotated[0].service == "ssh"
    assert annotated[1].service == "http"
    assert annotated[2].service is None
    # same list returned
    assert annotated is results
