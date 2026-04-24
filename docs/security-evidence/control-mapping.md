# Security Evidence: Control Mapping

| Control ID | Risk | Control | Location |
|---|---|---|---|
| `BW-C-001` | unapproved destructive remediation | approval gate + policy engine | `src/bw_defend/core/policy.py` |
| `BW-C-002` | rule tampering | checksum + detached signature verification before update | `src/bw_defend/core/rules.py` |
| `BW-C-003` | forensic gaps | append-only audit logging with chain verification | `src/bw_defend/core/audit.py` |
| `BW-C-004` | irreversible host controls | explicit revert command paths | `src/bw_defend/security/firewall.py` |
| `BW-C-005` | dependency vulnerability exposure | CI dependency audit policy and artifact retention | `.github/workflows/security.yml` |
| `BW-C-006` | supply-chain artifact substitution | checksums + SBOM + provenance attestation | `.github/workflows/supply-chain.yml` |
| `BW-C-007` | reliability regression | cross-platform reliability drill in release-readiness pipeline | `scripts/reliability-drill.py` |
