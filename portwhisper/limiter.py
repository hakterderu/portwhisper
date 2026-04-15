"""Port range limiter: clamp and validate port lists before scanning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

MIN_PORT = 1
MAX_PORT = 65535


@dataclass
class LimiterConfig:
    """Configuration for the port range limiter."""

    min_port: int = MIN_PORT
    max_port: int = MAX_PORT
    allow_privileged: bool = True  # ports < 1024

    def __post_init__(self) -> None:
        if not (MIN_PORT <= self.min_port <= MAX_PORT):
            raise ValueError(
                f"min_port must be between {MIN_PORT} and {MAX_PORT}, got {self.min_port}"
            )
        if not (MIN_PORT <= self.max_port <= MAX_PORT):
            raise ValueError(
                f"max_port must be between {MIN_PORT} and {MAX_PORT}, got {self.max_port}"
            )
        if self.min_port > self.max_port:
            raise ValueError(
                f"min_port ({self.min_port}) must not exceed max_port ({self.max_port})"
            )


def limit_ports(
    ports: List[int],
    config: LimiterConfig | None = None,
) -> List[int]:
    """Return ports filtered to the configured range and privilege rules.

    Args:
        ports: Raw list of port numbers.
        config: LimiterConfig instance; defaults to LimiterConfig().

    Returns:
        Sorted, deduplicated list of ports that pass all constraints.
    """
    if config is None:
        config = LimiterConfig()

    result: List[int] = []
    for port in ports:
        if port < config.min_port or port > config.max_port:
            continue
        if not config.allow_privileged and port < 1024:
            continue
        result.append(port)

    return sorted(set(result))
