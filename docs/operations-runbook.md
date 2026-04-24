# Operations Runbook

## Daily

1. Check monitor status: `bw-defend monitor status --json`
2. Verify firewall is in expected state: `bw-defend firewall status --json`
3. Run health check: `bw-defend doctor --strict --json`
4. Review new incidents and remediation outcomes
5. Review audit log growth and archive policy

## Weekly

1. Verify rules integrity:
   - `bw-defend rules verify --json`
2. Perform quarantine restore drill in staging
3. Verify process control approval gates with non-production PID
4. Validate docs remain aligned with live behavior

## Monthly

1. Run production readiness checklist
2. Run recovery drill for monitor and firewall state resets
3. Rotate operator access credentials and shell permissions

## Incident Response

- For active malware findings:
  1. run `scan`
  2. quarantine artifact
  3. evaluate blast radius
  4. if AI edition is enabled, use remediation with explicit approvals
- Preserve `audit.log` and `incidents.jsonl` as forensic evidence.
