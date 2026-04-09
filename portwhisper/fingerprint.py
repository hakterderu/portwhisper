"""Service fingerprinting based on port number and banner content."""

from typing import Optional
from portwhisper.scanner import ScanResult

# Well-known port → service name mapping
_PORT_MAP: dict[int, str] = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    80: "http",
    110: "pop3",
    143: "imap",
    443: "https",
    445: "smb",
    3306: "mysql",
    3389: "rdp",
    5432: "postgresql",
    6379: "redis",
    8080: "http-alt",
    8443: "https-alt",
    27017: "mongodb",
}

# Banner substring → service name (checked in order)
_BANNER_SIGNATURES: list[tuple[str, str]] = [
    ("SSH-", "ssh"),
    ("220 ", "ftp/smtp"),
    ("HTTP/", "http"),
    ("+OK", "pop3"),
    ("* OK", "imap"),
    ("redis_version", "redis"),
    ("mysql_native_password", "mysql"),
    ("PostgreSQL", "postgresql"),
]


def fingerprint_service(result: ScanResult) -> Optional[str]:
    """Return a service name string for an open port result, or None."""
    if result.state != "open":
        return None

    # Banner-based detection takes priority
    if result.banner:
        for signature, service in _BANNER_SIGNATURES:
            if signature in result.banner:
                return service

    # Fall back to well-known port lookup
    return _PORT_MAP.get(result.port)


def annotate_results(results: list[ScanResult]) -> list[ScanResult]:
    """Mutate each ScanResult in-place to add service fingerprint."""
    for result in results:
        result.service = fingerprint_service(result)
    return results
