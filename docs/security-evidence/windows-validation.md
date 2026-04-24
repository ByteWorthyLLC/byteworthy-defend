# Security Evidence: Windows Validation

## Validation Scope

- `bw-defend doctor --strict --json`
- Rules verification gate
- Audit-chain verification gate
- Monitor/firewall/process operational checks

## Workflow

- `.github/workflows/ci.yml` (`windows` matrix)
- `.github/workflows/release-readiness.yml` (`gate-windows`)

## Evidence

- Windows workflow logs
- Reliability drill artifact from `release-readiness` workflow
