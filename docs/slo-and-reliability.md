# SLO and Reliability Targets

This document defines production service objectives for `bw-defend` operations.

## Scope

- CLI operational commands
- Monitor lifecycle state transitions
- Rules verification/update safety controls
- Audit-chain verification command

## Service Level Objectives

- Availability SLO (operational commands): `99.9%` successful command completion per rolling 30 days.
- Monitor transition SLO: `99.95%` successful `start|stop|status` transitions.
- Safety gate SLO: `100%` enforcement for destructive action approval requirements.
- Rules integrity SLO: `100%` rejection rate for invalid checksum/signature bundles.

## Error Budget

- Availability SLO error budget: `43m 49s` per 30-day window.
- Any safety gate violation consumes full release budget and blocks release.

## Reliability Drill Policy

- Linux and Windows release candidates must run `scripts/reliability-drill.py`.
- Minimum drill target:
  - `--monitor-cycles 40`
  - `--firewall-cycles 8`
- Drill output must be archived as workflow artifacts.

## On-Call and Escalation

- Primary on-call owner: ByteWorthy Security Maintainers.
- Escalation path:
  1. Triage owner acknowledges within `15 minutes`.
  2. Critical regressions trigger immediate release freeze.
  3. Rollback owner executes runbook if SLO breach is confirmed.
