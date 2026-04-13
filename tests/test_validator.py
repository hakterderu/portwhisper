"""Tests for portwhisper.validator."""

from __future__ import annotations

import pytest

from portwhisper.validator import (
    ValidationResult,
    validate_host,
    validate_port,
    validate_port_list,
    validate_scan_input,
)


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

def test_validation_result_truthy_when_valid():
    assert ValidationResult(valid=True)


def test_validation_result_falsy_when_invalid():
    assert not ValidationResult(valid=False, errors=["oops"])


# ---------------------------------------------------------------------------
# validate_host
# ---------------------------------------------------------------------------

def test_validate_host_ipv4():
    assert validate_host("192.168.1.1")


def test_validate_host_ipv6():
    assert validate_host("::1")


def test_validate_host_localhost():
    assert validate_host("localhost")


def test_validate_host_valid_fqdn():
    assert validate_host("example.com")


def test_validate_host_subdomain():
    assert validate_host("scan.internal.example.org")


def test_validate_host_empty_string():
    result = validate_host("")
    assert not result
    assert result.errors


def test_validate_host_whitespace_only():
    result = validate_host("   ")
    assert not result


def test_validate_host_invalid_string():
    result = validate_host("not a host!")
    assert not result
    assert any("not a valid" in e for e in result.errors)


# ---------------------------------------------------------------------------
# validate_port
# ---------------------------------------------------------------------------

def test_validate_port_lower_bound():
    assert validate_port(1)


def test_validate_port_upper_bound():
    assert validate_port(65535)


def test_validate_port_common():
    assert validate_port(80)


def test_validate_port_zero():
    result = validate_port(0)
    assert not result
    assert result.errors


def test_validate_port_too_large():
    result = validate_port(65536)
    assert not result


def test_validate_port_non_integer():
    result = validate_port("80")  # type: ignore[arg-type]
    assert not result


def test_validate_port_bool_rejected():
    # bool is a subclass of int; we treat it as invalid.
    result = validate_port(True)  # type: ignore[arg-type]
    assert not result


# ---------------------------------------------------------------------------
# validate_port_list
# ---------------------------------------------------------------------------

def test_validate_port_list_all_valid():
    assert validate_port_list([22, 80, 443])


def test_validate_port_list_empty():
    result = validate_port_list([])
    assert not result


def test_validate_port_list_some_invalid():
    result = validate_port_list([80, 0, 99999])
    assert not result
    assert len(result.errors) == 2


# ---------------------------------------------------------------------------
# validate_scan_input
# ---------------------------------------------------------------------------

def test_validate_scan_input_valid():
    assert validate_scan_input("example.com", [22, 80, 443])


def test_validate_scan_input_bad_host():
    result = validate_scan_input("", [80])
    assert not result
    assert any("Host" in e for e in result.errors)


def test_validate_scan_input_bad_ports():
    result = validate_scan_input("example.com", [])
    assert not result


def test_validate_scan_input_both_invalid():
    result = validate_scan_input("", [])
    assert not result
    assert len(result.errors) >= 2
