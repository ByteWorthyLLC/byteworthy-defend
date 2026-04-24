# Quickstart

## Prerequisites

- Linux host (production target)
- Windows host (production target)
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
bw-defend audit verify --json
```

## Linux Runtime Parity via Docker (Optional)

Run the same Linux gate used by CI/release workflows:

```bash
docker compose run --rm linux-gate
```

Open an interactive Linux shell with the project pre-installed:

```bash
docker compose run --rm linux-shell
```

## Native Windows Development Gate

Run the Windows CI-equivalent gate locally:

```powershell
pwsh -File scripts/windows-gate.ps1
```

## First Scan

Linux:

```bash
mkdir -p /tmp/bw-defend-lab
echo 'EICAR-STANDARD-ANTIVIRUS-TEST-FILE' > /tmp/bw-defend-lab/eicar.txt
bw-defend scan /tmp/bw-defend-lab --json
bw-defend quarantine list --json
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path \"$env:TEMP\\bw-defend-lab\" | Out-Null
Set-Content -Path \"$env:TEMP\\bw-defend-lab\\eicar.txt\" -Value 'EICAR-STANDARD-ANTIVIRUS-TEST-FILE'
bw-defend scan \"$env:TEMP\\bw-defend-lab\" --json
bw-defend quarantine list --json
```
