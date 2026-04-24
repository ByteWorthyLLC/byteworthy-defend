# Production Readiness

## Reliability

- monitor lifecycle tested under repeated starts/stops
- state-file recovery tested after restart
- offline behavior of rules operations documented
- SLO targets documented and approved (`docs/slo-and-reliability.md`)
- reliability drill artifacts retained for Linux and Windows release runs

## Security

- approval gates enforced for destructive operations
- rule integrity verification enabled and tested
- audit trail generation validated for all remediation actions
- dependency audit policy enforced in CI
- supply-chain artifacts generated with checksum + SBOM + provenance attestation

## Operations

- release and rollback runbooks reviewed
- incident response owner assigned
- support escalation path tested
- independent security assessment evidence tracked when performed

## Documentation

- README command contract matches implementation
- runbooks and release checklist up to date
- security evidence reviewed
