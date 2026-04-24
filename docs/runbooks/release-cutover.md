# Runbook: Release Cutover

## Pre-Cutover

1. confirm `docs/release-blockers.md` has no open blockers
2. validate all CI checks are green
3. confirm rollback owner and comms channel

## Cutover

1. tag release commit
2. publish release notes and checksums
3. deploy package in staging then production
4. run `bw-defend doctor --json` and baseline scan

## Post-Cutover

1. monitor incidents and audit stream
2. validate firewall and monitor status baseline
3. log release evidence links
