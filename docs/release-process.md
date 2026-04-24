# Release Process

## Branch Model

- `main` is release branch.
- Merge only via PR with passing quality gates.

## Pre-Release Validation

Linux:

```bash
./scripts/linux-gate.sh
```

Windows:

```powershell
pwsh -File scripts/windows-gate.ps1
```

Static analysis policy (run in CI gates):

```bash
skylos src --all --gate --no-upload
```

Notes:

- Scope is `src/` (production code) to avoid dead-code noise from test harnesses.
- Rule suppressions and thresholds are centrally documented in `[tool.skylos]` in `pyproject.toml`.

## Versioning

- Follow semantic versioning (`MAJOR.MINOR.PATCH`).
- Keep in-progress notes in `CHANGELOG.md` under `Unreleased`.
- Cut annotated tags for releases.

## Release Artifacts

Each release should include:

- source archive
- checksums file
- release notes with risk summary
- rollback instructions

## Rollback Policy

If regression is detected:

1. stop monitor mode
2. revert firewall changes if applied
3. restore quarantined files where required by incident commander
4. roll back package to prior known-good version
5. record incident and remediation timeline
