# Security Architecture

## Threat Model Focus

- malicious artifacts on Windows and Linux hosts
- unsafe or over-broad remediation actions
- integrity tampering of rule bundles
- loss of forensic auditability

## Control Model

- deny-by-default policy for unapproved destructive actions
- deny-by-default for unknown remediation action types
- confidence thresholds for auto-remediation
- explicit approval path for dangerous operations
- append-only audit records for proposed/executed actions with unique audit event IDs and hash chaining
- rules bundle checksum validation plus schema validation before activation
- optional detached bundle signature enforcement via `BW_DEFEND_RULES_SIGNATURE_REQUIRED=true`
- optional outbound telemetry for audit events via `BW_DEFEND_TELEMETRY_ENDPOINT`
- dependency vulnerability audit gate in CI (`pip-audit`)
- supply-chain integrity controls for release artifacts (checksums + SBOM + provenance attestation)

## Destructive Actions

The following always require explicit operator approval when policy requires it:

- `delete`
- `kill`
- `network_block`

## Audit Record Expectations

Every remediation attempt should capture:

- action proposed
- policy decision and reason
- action execution status
- incident linkage (`incident_id`)
- timestamp

## Independent Review Requirement

Before GA release tagging, a third-party independent security review report is required and tracked in:

- `docs/security-evidence/independent-security-review.md`
