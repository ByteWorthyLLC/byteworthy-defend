# Runbook: Release Rollback

## Trigger Conditions

- critical regression in scanning/remediation behavior
- failed policy enforcement
- operational instability in monitor mode

## Steps

1. stop monitor mode
2. revert firewall changes
3. restore prior package version
4. run `bw-defend doctor --json`
5. validate baseline scan behavior
6. notify stakeholders and document timeline
