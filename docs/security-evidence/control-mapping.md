# Security Evidence: Control Mapping

| Risk | Control | Location |
|---|---|---|
| unapproved destructive remediation | approval gate + policy engine | `src/bw_defend/core/policy.py` |
| rule tampering | checksum verification before update | `src/bw_defend/core/rules.py` |
| forensic gaps | append-only audit logging | `src/bw_defend/core/audit.py` |
| irreversible host controls | explicit revert command paths | `src/bw_defend/security/firewall.py` |
