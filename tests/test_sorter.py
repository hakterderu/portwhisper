"""Tests for portwhisper.sorter module."""
from portwhisper.scanner import ScanResult
from portwhisper.sorter import SortKey, sort_results


def make_result(
    port: int,
    state: str = "open",
    service: str | None = None,
    host: str = "127.0.0.1",
) -> ScanResult:
    return ScanResult(host=host, port=port, state=state, service=service)


def test_sort_by_port_ascending():
    results = [make_result(443), make_result(22), make_result(80)]
    out = sort_results(results, key=SortKey.PORT)
    assert [r.port for r in out] == [22, 80, 443]


def test_sort_by_port_descending():
    results = [make_result(22), make_result(443), make_result(80)]
    out = sort_results(results, key=SortKey.PORT, reverse=True)
    assert [r.port for r in out] == [443, 80, 22]


def test_sort_by_state():
    results = [
        make_result(80, state="open"),
        make_result(22, state="closed"),
        make_result(443, state="filtered"),
    ]
    out = sort_results(results, key=SortKey.STATE)
    assert [r.state for r in out] == ["closed", "filtered", "open"]


def test_sort_by_service_none_last():
    results = [
        make_result(80, service="http"),
        make_result(22, service=None),
        make_result(443, service="https"),
    ]
    out = sort_results(results, key=SortKey.SERVICE)
    services = [r.service for r in out]
    assert services[-1] is None
    assert services[0] == "http"
    assert services[1] == "https"


def test_sort_by_host():
    results = [
        make_result(80, host="192.168.1.2"),
        make_result(80, host="10.0.0.1"),
        make_result(80, host="172.16.0.1"),
    ]
    out = sort_results(results, key=SortKey.HOST)
    assert out[0].host == "10.0.0.1"


def test_sort_does_not_mutate_original():
    results = [make_result(443), make_result(22)]
    _ = sort_results(results, key=SortKey.PORT)
    assert results[0].port == 443


def test_sort_empty_list():
    assert sort_results([], key=SortKey.PORT) == []
