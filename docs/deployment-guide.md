# Deployment Guide (Linux)

## Target

- Production support declaration: Linux only.

## Install Path

1. Build and install package:

```bash
python3 -m venv /opt/bw-defend/.venv
source /opt/bw-defend/.venv/bin/activate
pip install byteworthy-defend
```

2. Seed config:

```bash
mkdir -p ~/.config/bw-defend
cp config.example.toml ~/.config/bw-defend/config.toml
```

3. Validate runtime:

```bash
bw-defend doctor --json
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

## Rollback

1. stop monitor mode
2. revert firewall changes
3. restore prior package version
4. run doctor and baseline scan
