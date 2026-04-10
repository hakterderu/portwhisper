"""Human-readable report generation for scan results."""

from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from portwhisper.scanner import ScanResult


_STATUS_ICON = {"open": "✔", "closed": "✘", "filtered": "?"}
_STATUS_COLOR = {"open": "\033[32m", "closed": "\033[31m", "filtered": "\033[33m"}
_RESET = "\033[0m"


def _colorize(text: str, color_code: str, *, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"{color_code}{text}{_RESET}"


def format_result_line(result: ScanResult, *, use_color: bool = True) -> str:
    """Format a single ScanResult as a human-readable line."""
    icon = _STATUS_ICON.get(result.status, "?")
    color = _STATUS_COLOR.get(result.status, "")
    status_str = _colorize(f"{icon} {result.status.upper():<8}", color, use_color=use_color)
    service = result.service or "unknown"
    banner = f" | {result.banner}" if result.banner else ""
    return f"  {result.port:<6} {status_str}  {service}{banner}"


def build_report(
    results: List[ScanResult],
    host: str,
    *,
    use_color: bool = True,
    show_closed: bool = False,
    title: Optional[str] = None,
) -> str:
    """Build a full report string from a list of ScanResults."""
    lines: List[str] = []
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    header_title = title or "PortWhisper Scan Report"
    lines.append(f"{'─' * 50}")
    lines.append(f" {header_title}")
    lines.append(f" Host   : {host}")
    lines.append(f" Time   : {ts}")
    lines.append(f"{'─' * 50}")
    lines.append(f"  {'PORT':<6} {'STATUS':<14}  SERVICE")
    lines.append(f"  {'─'*5}  {'─'*12}  {'─'*20}")

    visible = [r for r in results if show_closed or r.status == "open"]
    if not visible:
        lines.append("  No open ports found.")
    else:
        for result in sorted(visible, key=lambda r: r.port):
            lines.append(format_result_line(result, use_color=use_color))

    open_count = sum(1 for r in results if r.status == "open")
    lines.append(f"{'─' * 50}")
    lines.append(f" {open_count} open port(s) out of {len(results)} scanned.")
    lines.append(f"{'─' * 50}")
    return "\n".join(lines)


def print_report(
    results: List[ScanResult],
    host: str,
    *,
    use_color: bool = True,
    show_closed: bool = False,
) -> None:
    """Print the scan report to stdout."""
    print(build_report(results, host, use_color=use_color, show_closed=show_closed))
