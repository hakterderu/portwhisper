# portwhisper

A lightweight async port scanner with service fingerprinting and JSON/CSV export support.

---

## Installation

```bash
pip install portwhisper
```

Or install from source:

```bash
git clone https://github.com/youruser/portwhisper.git && cd portwhisper && pip install .
```

---

## Usage

Scan a host across a range of ports and export the results:

```bash
# Basic scan
portwhisper scan 192.168.1.1 --ports 1-1024

# Scan with service fingerprinting and JSON export
portwhisper scan example.com --ports 22,80,443,8080 --fingerprint --output results.json

# Export as CSV
portwhisper scan 10.0.0.1 --ports 1-65535 --output results.csv
```

You can also use it programmatically:

```python
import asyncio
from portwhisper import Scanner

async def main():
    scanner = Scanner(host="192.168.1.1", ports=range(1, 1025))
    results = await scanner.run(fingerprint=True)
    scanner.export(results, path="output.json")

asyncio.run(main())
```

---

## Features

- ⚡ Async-first design for fast, non-blocking scans
- 🔍 Service fingerprinting on open ports
- 📄 Export results to JSON or CSV
- 🎯 Flexible port targeting (ranges, lists, or single ports)

---

## License

This project is licensed under the [MIT License](LICENSE).