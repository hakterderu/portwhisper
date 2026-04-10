"""Command-line interface for portwhisper."""

import argparse
import asyncio
import sys
from pathlib import Path

from portwhisper.scanner import ScanConfig, scan
from portwhisper.fingerprint import annotate_results
from portwhisper.exporter import export_json, export_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portwhisper",
        description="Lightweight async port scanner with service fingerprinting.",
    )
    parser.add_argument("host", help="Target hostname or IP address")
    parser.add_argument(
        "-p", "--ports",
        default="1-1024",
        help="Port range, e.g. '22', '80,443', or '1-1024' (default: 1-1024)",
    )
    parser.add_argument(
        "-t", "--timeout",
        type=float,
        default=1.0,
        help="Connection timeout in seconds (default: 1.0)",
    )
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=200,
        help="Max concurrent connections (default: 200)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (.json or .csv)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Export format when -o is specified (default: json)",
    )
    parser.add_argument(
        "--no-fingerprint",
        action="store_true",
        help="Skip service fingerprinting",
    )
    return parser


def parse_ports(port_str: str) -> list:
    ports = []
    for part in port_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            ports.extend(range(int(start), int(end) + 1))
        else:
            ports.append(int(part))
    return ports


async def run(args: argparse.Namespace) -> int:
    ports = parse_ports(args.ports)
    config = ScanConfig(
        host=args.host,
        ports=ports,
        timeout=args.timeout,
        concurrency=args.concurrency,
    )

    results = await scan(config)

    if not args.no_fingerprint:
        results = await annotate_results(results)

    open_results = [r for r in results if r.open]
    print(f"[portwhisper] {args.host} — {len(open_results)} open port(s) found.")
    for r in open_results:
        svc = f"  [{r.service}]" if r.service else ""
        print(f"  {r.port}/tcp  OPEN{svc}")

    if args.output:
        fmt = args.format
        if args.output.endswith(".csv"):
            fmt = "csv"
        if fmt == "csv":
            export_csv(results, destination=args.output)
        else:
            export_json(results, destination=args.output)
        print(f"[portwhisper] Results written to {args.output}")

    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
