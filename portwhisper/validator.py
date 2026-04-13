"""Input validation utilities for portwhisper."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from typing import List, Tuple


_HOSTNAME_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+"
    r"[a-zA-Z]{2,}$"
)


@dataclass
class ValidationResult:
    """Outcome of a validation check."""

    valid: bool
    errors: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:  # noqa: D105
        return self.valid


def validate_host(host: str) -> ValidationResult:
    """Return a ValidationResult indicating whether *host* is acceptable."""
    if not host or not host.strip():
        return ValidationResult(valid=False, errors=["Host must not be empty."])

    host = host.strip()

    # Try as an IP address first.
    try:
        ipaddress.ip_address(host)
        return ValidationResult(valid=True)
    except ValueError:
        pass

    # Try as a hostname.
    if _HOSTNAME_RE.match(host) or host == "localhost":
        return ValidationResult(valid=True)

    return ValidationResult(
        valid=False,
        errors=[f"'{host}' is not a valid IP address or hostname."],
    )


def validate_port(port: int) -> ValidationResult:
    """Return a ValidationResult indicating whether *port* is in range."""
    if not isinstance(port, int) or isinstance(port, bool):
        return ValidationResult(valid=False, errors=["Port must be an integer."])
    if port < 1 or port > 65535:
        return ValidationResult(
            valid=False,
            errors=[f"Port {port} is out of range (1-65535)."],
        )
    return ValidationResult(valid=True)


def validate_port_list(ports: List[int]) -> ValidationResult:
    """Validate every port in *ports* and aggregate errors."""
    if not ports:
        return ValidationResult(valid=False, errors=["Port list must not be empty."])

    errors: List[str] = []
    for p in ports:
        result = validate_port(p)
        if not result:
            errors.extend(result.errors)

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_scan_input(host: str, ports: List[int]) -> ValidationResult:
    """Validate both the host and port list together."""
    errors: List[str] = []

    host_result = validate_host(host)
    if not host_result:
        errors.extend(host_result.errors)

    ports_result = validate_port_list(ports)
    if not ports_result:
        errors.extend(ports_result.errors)

    return ValidationResult(valid=len(errors) == 0, errors=errors)
