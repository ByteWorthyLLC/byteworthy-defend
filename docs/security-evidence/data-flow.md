# Security Evidence: Data Flow

## Core flows

1. scan input -> detection -> incident record
2. incident -> remediation proposal -> policy decision
3. approved action -> execution -> audit log entry

## Stored artifacts

- incidents log (JSONL)
- audit log (JSONL-like line records)
- quarantine manifest
