"""Output formatter for scan results supporting table and compact display modes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from portwhisper.scanner import ScanResult


class FormatMode(str, Enum):
    TABLE = "table"
    COMPACT = "compact"
    MINIMAL = "minimal"


@dataclass
class FormatterConfig:
    mode: FormatMode = FormatMode.TABLE
    show_closed: bool = False
    max_banner_len: int = 60
    col_widths: dict = field(default_factory=lambda: {"port": 8, "state": 10, "service": 18, "banner": 60})

    def __post_init__(self) -> None:
        if isinstance(self.mode, str):
            self.mode = FormatMode(self.mode)
        if self.max_banner_len < 0:
            raise ValueError("max_banner_len must be >= 0")


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[: max(0, max_len - 3)] + "..."


def format_table(results: List[ScanResult], config: FormatterConfig) -> str:
    w = config.col_widths
    header = (
        f"{'PORT':<{w['port']}} {'STATE':<{w['state']}} "
        f"{'SERVICE':<{w['service']}} {'BANNER':<{w['banner']}}"
    )
    separator = "-" * len(header)
    lines = [header, separator]
    for r in results:
        if not config.show_closed and r.state != "open":
            continue
        banner = _truncate(r.banner or "", config.max_banner_len)
        line = (
            f"{r.port:<{w['port']}} {r.state:<{w['state']}} "
            f"{(r.service or ''):<{w['service']}} {banner:<{w['banner']}}"
        )
        lines.append(line)
    return "\n".join(lines)


def format_compact(results: List[ScanResult], config: FormatterConfig) -> str:
    lines = []
    for r in results:
        if not config.show_closed and r.state != "open":
            continue
        service_part = f" ({r.service})" if r.service else ""
        banner_part = f" — {_truncate(r.banner, config.max_banner_len)}" if r.banner else ""
        lines.append(f"{r.port}/{r.state}{service_part}{banner_part}")
    return "\n".join(lines)


def format_minimal(results: List[ScanResult], config: FormatterConfig) -> str:
    return "\n".join(
        str(r.port) for r in results if config.show_closed or r.state == "open"
    )


_FORMATTERS = {
    FormatMode.TABLE: format_table,
    FormatMode.COMPACT: format_compact,
    FormatMode.MINIMAL: format_minimal,
}


def format_results(results: List[ScanResult], config: FormatterConfig | None = None) -> str:
    """Format a list of ScanResults according to the given FormatterConfig."""
    if config is None:
        config = FormatterConfig()
    formatter_fn = _FORMATTERS[config.mode]
    return formatter_fn(results, config)
