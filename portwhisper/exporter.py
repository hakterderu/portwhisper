"""Export scan results to JSON or CSV formats."""

import csv
import json
import io
from typing import List, Union
from pathlib import Path

from portwhisper.scanner import ScanResult


def results_to_dict(results: List[ScanResult]) -> List[dict]:
    """Convert ScanResult objects to plain dictionaries."""
    return [
        {
            "host": r.host,
            "port": r.port,
            "open": r.open,
            "service": r.service or "",
            "banner": r.banner or "",
            "latency_ms": round(r.latency_ms, 3) if r.latency_ms is not None else None,
        }
        for r in results
    ]


def export_json(
    results: List[ScanResult],
    destination: Union[str, Path, None] = None,
    indent: int = 2,
) -> str:
    """Serialize results to JSON.

    Args:
        results: List of ScanResult objects.
        destination: Optional file path to write output to.
        indent: JSON indentation level.

    Returns:
        JSON string representation.
    """
    data = results_to_dict(results)
    output = json.dumps(data, indent=indent)

    if destination is not None:
        Path(destination).write_text(output, encoding="utf-8")

    return output


def export_csv(
    results: List[ScanResult],
    destination: Union[str, Path, None] = None,
) -> str:
    """Serialize results to CSV.

    Args:
        results: List of ScanResult objects.
        destination: Optional file path to write output to.

    Returns:
        CSV string representation.
    """
    fieldnames = ["host", "port", "open", "service", "banner", "latency_ms"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(results_to_dict(results))
    output = buf.getvalue()

    if destination is not None:
        Path(destination).write_text(output, encoding="utf-8")

    return output
