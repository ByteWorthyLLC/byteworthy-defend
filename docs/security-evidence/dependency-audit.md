# Security Evidence: Dependency Audit

## Controls

- Python dependency audit executed in CI for `dev` and `ai` dependency sets.
- Any known vulnerability findings fail the Security workflow.

## Workflow and Policy

- `.github/workflows/security.yml`
- `scripts/dependency-audit-policy.py`

## Artifact

- `pip-audit.json` uploaded by Security workflow.
