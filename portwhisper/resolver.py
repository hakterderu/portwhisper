"""Hostname resolution utilities for portwhisper."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResolveResult:
    """Result of a hostname resolution attempt."""

    host: str
    ip_address: Optional[str]
    resolved: bool
    error: Optional[str] = field(default=None)

    def __str__(self) -> str:
        if self.resolved:
            return f"{self.host} -> {self.ip_address}"
        return f"{self.host} -> [unresolved: {self.error}]"


async def resolve_host(host: str, timeout: float = 5.0) -> ResolveResult:
    """Resolve a hostname to an IP address asynchronously.

    Args:
        host: Hostname or IP address string to resolve.
        timeout: Maximum seconds to wait for resolution.

    Returns:
        A ResolveResult with the resolved IP or error details.
    """
    loop = asyncio.get_event_loop()
    try:
        ip = await asyncio.wait_for(
            loop.run_in_executor(None, socket.gethostbyname, host),
            timeout=timeout,
        )
        return ResolveResult(host=host, ip_address=ip, resolved=True)
    except asyncio.TimeoutError:
        return ResolveResult(
            host=host,
            ip_address=None,
            resolved=False,
            error="resolution timed out",
        )
    except socket.gaierror as exc:
        return ResolveResult(
            host=host,
            ip_address=None,
            resolved=False,
            error=str(exc),
        )


def resolve_host_sync(host: str, timeout: float = 5.0) -> ResolveResult:
    """Synchronous wrapper around resolve_host for CLI use."""
    return asyncio.run(resolve_host(host, timeout=timeout))
