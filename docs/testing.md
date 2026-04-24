# Testing Strategy

## Unit Coverage

- rule parsing and integrity checks
- quarantine state transitions
- policy decision logic and approval gates
- CLI contract argument behavior (implicitly via integration flows)

## Integration Coverage

- scan -> incident -> quarantine lifecycle
- monitor start/stop/status flow
- firewall apply/revert lifecycle
- process kill approval enforcement
- AI remediation gating (blocked vs approved)

## End-to-End Linux Verification

Before production release, run:

```bash
pytest
bw-defend doctor --strict --json
bw-defend scan /tmp --json
bw-defend monitor start --json
bw-defend firewall apply --json
bw-defend firewall revert --json
bw-defend monitor stop --json
bw-defend rules verify --json
```

## Reliability and Regression Scenarios

- repeated monitor cycles
- restart recovery on state files
- corrupted config handling
- offline mode behavior for rules updates
- invalid rules schema rejection
- unknown remediation action policy denial
