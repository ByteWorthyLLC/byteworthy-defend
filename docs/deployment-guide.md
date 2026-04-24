# Deployment Guide (Windows and Linux)

## Target

- Production support declaration: Windows and Linux.

## Install Path

Linux:

```bash
python3 -m venv /opt/bw-defend/.venv
source /opt/bw-defend/.venv/bin/activate
pip install byteworthy-defend
```

Windows PowerShell:

```powershell
python -m venv $env:USERPROFILE\\.bw-defend\\.venv
& $env:USERPROFILE\\.bw-defend\\.venv\\Scripts\\Activate.ps1
pip install byteworthy-defend
```

Seed config:

```bash
mkdir -p ~/.config/bw-defend
cp config.example.toml ~/.config/bw-defend/config.toml
```

Windows PowerShell config seed:

```powershell
New-Item -ItemType Directory -Force -Path \"$env:APPDATA\\bw-defend\" | Out-Null
Copy-Item config.example.toml \"$env:APPDATA\\bw-defend\\config.toml\" -Force
```

Validate runtime:

```bash
bw-defend doctor --strict --json
bw-defend audit verify --json
```

## Enterprise Control Flags

Enforce detached rule signatures:

```bash
export BW_DEFEND_RULES_SIGNATURE_REQUIRED=true
export BW_DEFEND_RULES_SIGNING_KEY='<signing-secret>'
```

Enable outbound audit telemetry:

```bash
export BW_DEFEND_TELEMETRY_ENDPOINT='https://security.example.com/ingest'
export BW_DEFEND_TELEMETRY_ENABLED=true
export BW_DEFEND_TELEMETRY_TOKEN='<bearer-token>'
```

Tune per-file scan limit (bytes):

```bash
export BW_DEFEND_MAX_SCAN_BYTES=8388608
```

## Linux Runtime Mimic (Containerized)

For non-Linux developer machines, use Docker to mimic production checks:

```bash
docker build -t byteworthy-defend:linux-gate .
docker run --rm byteworthy-defend:linux-gate
```

Or use compose:

```bash
docker compose run --rm linux-gate
```

## Native Windows Validation Gate

Run the Windows CI-equivalent gate:

```powershell
pwsh -File scripts/windows-gate.ps1
```

## Rollback

1. stop monitor mode
2. revert firewall changes
3. restore prior package version
4. run doctor and baseline scan
