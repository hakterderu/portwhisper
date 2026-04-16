"""Tests for portwhisper.profiler."""

import time
import pytest
from portwhisper.profiler import ProfilerConfig, ScanProfile, Profiler


# ---------------------------------------------------------------------------
# ProfilerConfig
# ---------------------------------------------------------------------------

def test_profiler_config_defaults():
    cfg = ProfilerConfig()
    assert cfg.enabled is True
    assert cfg.precision == 3


def test_profiler_config_custom():
    cfg = ProfilerConfig(enabled=False, precision=5)
    assert cfg.enabled is False
    assert cfg.precision == 5


def test_profiler_config_invalid_precision_negative():
    with pytest.raises(ValueError, match="precision"):
        ProfilerConfig(precision=-1)


def test_profiler_config_invalid_precision_too_high():
    with pytest.raises(ValueError, match="precision"):
        ProfilerConfig(precision=10)


# ---------------------------------------------------------------------------
# ScanProfile
# ---------------------------------------------------------------------------

def make_profile(total=100, open_=10, elapsed=2.0, precision=3):
    return ScanProfile(total_ports=total, open_ports=open_,
                       elapsed_seconds=elapsed, precision=precision)


def test_scan_profile_closed_ports():
    p = make_profile(total=100, open_=10)
    assert p.closed_ports == 90


def test_scan_profile_ports_per_second():
    p = make_profile(total=100, elapsed=2.0)
    assert p.ports_per_second == pytest.approx(50.0)


def test_scan_profile_ports_per_second_zero_elapsed():
    p = make_profile(total=100, elapsed=0.0)
    assert p.ports_per_second == 0.0


def test_scan_profile_to_dict_keys():
    p = make_profile()
    d = p.to_dict()
    assert set(d.keys()) == {
        "total_ports", "open_ports", "closed_ports",
        "elapsed_seconds", "ports_per_second",
    }


def test_scan_profile_to_dict_values():
    p = make_profile(total=50, open_=5, elapsed=1.0, precision=2)
    d = p.to_dict()
    assert d["total_ports"] == 50
    assert d["open_ports"] == 5
    assert d["closed_ports"] == 45
    assert d["elapsed_seconds"] == 1.0
    assert d["ports_per_second"] == 50.0


def test_scan_profile_render_contains_key_info():
    p = make_profile(total=200, open_=20, elapsed=4.0)
    text = p.render()
    assert "200" in text
    assert "20" in text
    assert "ports/sec" in text


# ---------------------------------------------------------------------------
# Profiler
# ---------------------------------------------------------------------------

def test_profiler_elapsed_increases():
    prof = Profiler()
    prof.start()
    time.sleep(0.05)
    prof.stop()
    assert prof.elapsed >= 0.05


def test_profiler_context_manager():
    with Profiler() as prof:
        time.sleep(0.02)
    assert prof.elapsed >= 0.02


def test_profiler_build_profile():
    with Profiler() as prof:
        time.sleep(0.01)
    profile = prof.build_profile(total_ports=80, open_ports=3)
    assert profile.total_ports == 80
    assert profile.open_ports == 3
    assert profile.elapsed_seconds >= 0.01


def test_profiler_custom_config():
    cfg = ProfilerConfig(precision=1)
    prof = Profiler(config=cfg)
    prof.start()
    prof.stop()
    profile = prof.build_profile(total_ports=10, open_ports=2)
    assert profile.precision == 1
