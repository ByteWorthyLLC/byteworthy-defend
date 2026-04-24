<p align="center">
  <img src="site/assets/brand-mark.svg" width="150" alt="ByteWorthy Defend" />
</p>

<h1 align="center">ByteWorthy Defend</h1>

<p align="center">
  <strong>Open-source Linux-first terminal antivirus for production operations.</strong>
</p>

<p align="center">
  One repo, two editions: <code>core</code> (no AI) and <code>ai</code> (policy-gated remediation).
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a>&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="#command-surface">Commands</a>&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="#editions">Editions</a>&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="#security-model">Security Model</a>&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="#docs">Docs</a>&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="#production-gate">Production Gate</a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/platform-Linux-informational?style=flat-square" alt="Linux target" />
  <img src="https://img.shields.io/badge/interface-bw--defend-black?style=flat-square" alt="bw-defend CLI" />
</p>

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
bw-defend doctor --json
```

Enable AI edition:

```bash
pip install -e '.[ai]'
mkdir -p ~/.config/bw-defend
cat > ~/.config/bw-defend/config.toml <<'CFG'
edition = "ai"

[remediation_policy]
allow_auto_quarantine = true
allow_auto_temp_isolation = true
destructive_requires_approval = true
auto_execute_min_confidence = 0.85
CFG
```

## Command Surface

- `bw-defend scan <path|system>`
- `bw-defend monitor start|stop|status`
- `bw-defend quarantine list|restore|purge`
- `bw-defend firewall status|apply|revert`
- `bw-defend process list|kill --pid <id> --approve`
- `bw-defend ai remediate <incident-id> [--approve]`
- `bw-defend rules update|list|verify`
- `bw-defend doctor`

All operational commands support `--json` for machine-readable output.

## Editions

- **Core edition**: scanning, monitoring, quarantine, rules, firewall/process controls.
- **AI edition**: adds AI remediation planner/executor with policy enforcement.

Edition is controlled in `~/.config/bw-defend/config.toml` via:

```toml
edition = "core" # or "ai"
```

## Security Model

- AI never bypasses policy evaluation.
- Destructive actions (`delete`, `kill`, `network_block`) require `--approve`.
- Non-destructive actions can auto-execute only when policy allows and confidence threshold is met.
- All proposed and executed remediation actions are appended to an immutable audit trail file.

## Incident Schema v1

Stable required fields:

- `id`
- `timestamp`
- `source`
- `artifact`
- `detection_type`
- `severity`
- `confidence`
- `action_state`
- `approval_required`
- `remediation_plan`
- `final_outcome`

## Project Site

- Product page: `site/index.html`
- Trust center: `site/trust.html`

## Docs

- [Quickstart Guide](docs/quickstart.md)
- [Command Reference](docs/command-reference.md)
- [Architecture](docs/architecture.md)
- [Deployment Guide](docs/deployment-guide.md)
- [Operations Runbook](docs/operations-runbook.md)
- [Release Process](docs/release-process.md)
- [Production Readiness](docs/production-readiness.md)
- [GA Readiness Criteria](docs/ga-readiness-criteria.md)
- [Release Blockers](docs/release-blockers.md)
- [Support and Release Cadence](docs/support-and-release-cadence.md)
- [Testing Strategy](docs/testing.md)
- [GitHub Hardening](docs/github-hardening.md)
- [Security Policy](SECURITY.md)
- [Contributing Guide](CONTRIBUTING.md)
- [GitHub Cutover Runbook](docs/github-cutover-runbook.md)
- [Docs Index](docs/index.md)

## Production Gate

A production tag must not be created until all gates in [`docs/release-readiness-checklist.md`](docs/release-readiness-checklist.md) and [`docs/ga-readiness-criteria.md`](docs/ga-readiness-criteria.md) are checked and evidence is attached.
