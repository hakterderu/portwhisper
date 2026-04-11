"""Core data structures and scan configuration for portwhisper."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScanResult:
    """Result of scanning a single port on a host."""

    host: str
    port: int
    open: bool
    banner: Optional[str] = None
    service: Optional[str] = None
    error: Optional[str] = None

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def state(self) -> str:
        return "open" if self.open else "closed"

    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "open": self.open,
            "state": self.state,
            "banner": self.banner,
            "service": self.service,
            "error": self.error,
        }


@dataclass
class ScanConfig:
    """Runtime configuration passed to scanning primitives."""

    timeout: float = 2.0
    banner_timeout: float = 1.0
    retries: int = 1
    concurrency: int = 200
    grab_banner: bool = True

    def __post_init__(self) -> None:
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")
        if self.banner_timeout <= 0:
            raise ValueError("banner_timeout must be > 0")
        if self.retries < 0:
            raise ValueError("retries must be >= 0")
        if self.concurrency < 1:
            raise ValueError("concurrency must be >= 1")


async def scan_port(host: str, port: int, config: ScanConfig) -> ScanResult:
    """Attempt a TCP connection to *host*:*port* and return a :class:`ScanResult`."""
    last_error: Optional[str] = None

    for attempt in range(config.retries + 1):
        try:
            conn = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(conn, timeout=config.timeout)

            banner: Optional[str] = None
            if config.grab_banner:
                try:
                    data = await asyncio.wait_for(
                        reader.read(1024), timeout=config.banner_timeout
                    )
                    banner = data.decode(errors="replace").strip() or None
                except asyncio.TimeoutError:
                    pass

            writer.close()
            await writer.wait_closed()
            return ScanResult(host=host, port=port, open=True, banner=banner)
        except (OSError, asyncio.TimeoutError) as exc:
            last_error = str(exc)

    return ScanResult(host=host, port=port, open=False, error=last_error)
