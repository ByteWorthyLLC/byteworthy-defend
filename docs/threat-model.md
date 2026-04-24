# Threat Model

## Assets

- host filesystem integrity
- runtime process integrity
- network egress integrity
- incident and audit records

## Adversary Goals

- execute or persist malicious artifacts
- evade detection or incident logging
- trigger destructive actions without authorization
- tamper with rule updates

## Mitigations

- signature-based scanning baseline
- controlled quarantine lifecycle
- policy engine approval gates
- rule checksum verification
- append-only remediation audit records

## Residual Risks

- signature-only detection blind spots
- local operator misuse with privileged shell access
- environmental gaps when host telemetry is unavailable
