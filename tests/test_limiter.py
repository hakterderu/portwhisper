"""Tests for portwhisper.limiter."""

from __future__ import annotations

import pytest

from portwhisper.limiter import LimiterConfig, limit_ports, MIN_PORT, MAX_PORT


# ---------------------------------------------------------------------------
# LimiterConfig
# ---------------------------------------------------------------------------


def test_limiter_config_defaults() -> None:
    cfg = LimiterConfig()
    assert cfg.min_port == MIN_PORT
    assert cfg.max_port == MAX_PORT
    assert cfg.allow_privileged is True


def test_limiter_config_custom() -> None:
    cfg = LimiterConfig(min_port=1024, max_port=9999, allow_privileged=False)
    assert cfg.min_port == 1024
    assert cfg.max_port == 9999
    assert cfg.allow_privileged is False


def test_limiter_config_invalid_min_port() -> None:
    with pytest.raises(ValueError, match="min_port"):
        LimiterConfig(min_port=0)


def test_limiter_config_invalid_max_port() -> None:
    with pytest.raises(ValueError, match="max_port"):
        LimiterConfig(max_port=65536)


def test_limiter_config_min_greater_than_max() -> None:
    with pytest.raises(ValueError, match="min_port"):
        LimiterConfig(min_port=9000, max_port=8000)


# ---------------------------------------------------------------------------
# limit_ports
# ---------------------------------------------------------------------------


def test_limit_ports_default_config_passthrough() -> None:
    ports = [22, 80, 443, 8080]
    assert limit_ports(ports) == [22, 80, 443, 8080]


def test_limit_ports_clamps_to_range() -> None:
    cfg = LimiterConfig(min_port=100, max_port=500)
    ports = [22, 100, 200, 500, 501, 65535]
    assert limit_ports(ports, cfg) == [100, 200, 500]


def test_limit_ports_removes_privileged() -> None:
    cfg = LimiterConfig(allow_privileged=False)
    ports = [22, 80, 443, 1024, 8080]
    result = limit_ports(ports, cfg)
    assert 22 not in result
    assert 80 not in result
    assert 443 not in result
    assert 1024 in result
    assert 8080 in result


def test_limit_ports_deduplicates() -> None:
    ports = [80, 80, 443, 443, 8080]
    assert limit_ports(ports) == [80, 443, 8080]


def test_limit_ports_returns_sorted() -> None:
    ports = [8080, 22, 443, 80]
    assert limit_ports(ports) == [22, 80, 443, 8080]


def test_limit_ports_empty_input() -> None:
    assert limit_ports([]) == []


def test_limit_ports_all_filtered() -> None:
    cfg = LimiterConfig(min_port=9000, max_port=9999)
    ports = [22, 80, 443]
    assert limit_ports(ports, cfg) == []


def test_limit_ports_uses_default_config_when_none() -> None:
    """Passing config=None should behave identically to LimiterConfig()."""
    ports = [1, 1024, 65535]
    assert limit_ports(ports, None) == limit_ports(ports, LimiterConfig())
