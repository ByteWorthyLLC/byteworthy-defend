# Security Architecture

## Threat Model Focus

- malicious artifacts on Linux hosts
- unsafe or over-broad remediation actions
- integrity tampering of rule bundles
- loss of forensic auditability

## Control Model

- deny-by-default policy for unapproved destructive actions
- confidence thresholds for auto-remediation
- explicit approval path for dangerous operations
- append-only audit records for proposed/executed actions

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
