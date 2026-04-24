# Security Policy

## Supported Branches

- `main` is the supported security branch.
- Security fixes are published on `main` and included in tagged releases.

## Reporting a Vulnerability

Do not open public issues for vulnerabilities.

Use one of the following channels:

1. GitHub Security Advisory (private disclosure)
2. Email: `security@byteworthy.io`

Include:

- affected component and commit/version
- clear reproduction steps or PoC
- impact statement
- suggested mitigation (if available)

## Response Targets

- Acknowledge report within 3 business days
- Triage and severity determination within 7 business days
- Critical severity mitigation path published as quickly as possible

## Security Scope

In scope:

- rule integrity validation and update path
- quarantine lifecycle and rollback safety
- policy engine approval enforcement
- audit trail integrity and forensic usability
- process/firewall control safety and reversibility

Out of scope:

- unsupported branches
- vulnerabilities requiring privileged host compromise before exploitation

## Operator Hardening Checklist

- [ ] Restrict CLI execution to trusted operators
- [ ] Store config at `~/.config/bw-defend/config.toml` with least-privilege permissions
- [ ] Keep rules bundles signed/checksummed by trusted source
- [ ] Validate rollback and incident runbooks quarterly
- [ ] Keep Windows and Linux hosts patched and endpoint telemetry enabled
