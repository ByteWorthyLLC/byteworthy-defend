# Quickstart

## Prerequisites

- Linux host (production target)
- Python 3.11+

## Install

```bash
git clone https://github.com/ByteWorthyLLC/byteworthy-defend.git
cd byteworthy-defend
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## First Health Check

```bash
bw-defend doctor --strict --json
```

## Linux Parity via Docker (macOS/Windows Dev Hosts)

Run the same Linux gate used by CI:

```bash
docker compose run --rm linux-gate
```

Open an interactive Linux shell with the project pre-installed:

```bash
docker compose run --rm linux-shell
```

## First Scan

```bash
mkdir -p /tmp/bw-defend-lab
echo 'EICAR-STANDARD-ANTIVIRUS-TEST-FILE' > /tmp/bw-defend-lab/eicar.txt
bw-defend scan /tmp/bw-defend-lab --json
bw-defend quarantine list --json
```
