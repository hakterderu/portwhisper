"""Timeout configuration and async connect helper for portwhisper."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class TimeoutConfig:
    """Configuration for connection and banner-read timeouts."""

    connect_timeout: float = 1.5
    banner_timeout: float = 2.0
    max_retries: int = 1

    def __post_init__(self) -> None:
        if self.connect_timeout <= 0:
            raise ValueError("connect_timeout must be positive")
        if self.banner_timeout <= 0:
            raise ValueError("banner_timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")


async def try_connect(
    host: str,
    port: int,
    config: Optional[TimeoutConfig] = None,
) -> Tuple[bool, Optional[str]]:
    """Attempt a TCP connection and optional banner grab.

    Returns a tuple of (is_open, banner_or_none).
    """
    if config is None:
        config = TimeoutConfig()

    attempts = config.max_retries + 1
    for attempt in range(attempts):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=config.connect_timeout,
            )
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            if attempt < attempts - 1:
                continue
            return False, None

        banner: Optional[str] = None
        try:
            raw = await asyncio.wait_for(
                reader.read(1024),
                timeout=config.banner_timeout,
            )
            if raw:
                banner = raw.decode(errors="replace").strip()
        except (asyncio.TimeoutError, OSError):
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except OSError:
                pass

        return True, banner

    return False, None
