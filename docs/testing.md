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

## End-to-End Cross-Platform Verification

Before production release on Linux, run:

```bash
./scripts/linux-gate.sh
```

For macOS/Windows developers who need Linux parity:

```bash
docker compose run --rm linux-gate
```

Before production release on Windows, run:

```powershell
pwsh -File scripts/windows-gate.ps1
```

## Reliability and Regression Scenarios

- repeated monitor cycles
- restart recovery on state files
- corrupted config handling
- offline mode behavior for rules updates
- invalid rules schema rejection
- unknown remediation action policy denial
