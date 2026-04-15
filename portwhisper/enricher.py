"""Result enrichment: attach extra metadata to ScanResults."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from portwhisper.scanner import ScanResult

# Well-known port descriptions beyond basic service names
_PORT_DESCRIPTIONS: Dict[int, str] = {
    21: "File Transfer Protocol – control channel",
    22: "Secure Shell remote login",
    23: "Telnet unencrypted remote login",
    25: "SMTP mail transfer",
    53: "Domain Name System",
    80: "HTTP web traffic",
    110: "POP3 mail retrieval",
    143: "IMAP mail access",
    443: "HTTPS encrypted web traffic",
    445: "SMB file sharing",
    3306: "MySQL database",
    3389: "Remote Desktop Protocol",
    5432: "PostgreSQL database",
    6379: "Redis in-memory store",
    8080: "HTTP alternate / proxy",
    8443: "HTTPS alternate",
    27017: "MongoDB database",
}


@dataclass
class EnricherConfig:
    """Configuration for the enrichment step."""

    add_description: bool = True
    add_risk_flag: bool = True
    # Ports considered elevated-risk when open
    risky_ports: List[int] = field(
        default_factory=lambda: [21, 23, 445, 3389, 5900]
    )

    def __post_init__(self) -> None:
        if not isinstance(self.risky_ports, list):
            raise TypeError("risky_ports must be a list")


@dataclass
class EnrichedResult:
    """A ScanResult with optional extra metadata."""

    result: ScanResult
    description: Optional[str] = None
    is_risky: bool = False

    def to_dict(self) -> dict:
        base = self.result.to_dict()
        base["description"] = self.description
        base["is_risky"] = self.is_risky
        return base


def enrich_results(
    results: List[ScanResult],
    config: Optional[EnricherConfig] = None,
) -> List[EnrichedResult]:
    """Attach description and risk metadata to each ScanResult."""
    if config is None:
        config = EnricherConfig()

    enriched: List[EnrichedResult] = []
    risky_set = set(config.risky_ports)

    for r in results:
        description: Optional[str] = None
        if config.add_description:
            description = _PORT_DESCRIPTIONS.get(r.port)

        is_risky = False
        if config.add_risk_flag and r.state == "open":
            is_risky = r.port in risky_set

        enriched.append(
            EnrichedResult(result=r, description=description, is_risky=is_risky)
        )

    return enriched
