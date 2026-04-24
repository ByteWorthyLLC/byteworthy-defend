# Contributing to ByteWorthy Defend

ByteWorthy Defend is an open-source Linux security project. Every change must preserve operational safety, reproducibility, and clear rollback behavior.

## Branching and Commits

- Branch from `main`.
- Use scoped branch names:
  - `feat/<area>-<topic>`
  - `fix/<area>-<topic>`
  - `docs/<area>-<topic>`
- Use conventional commits:
  - `feat(core): ...`
  - `fix(cli): ...`
  - `docs(release): ...`

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Required Quality Gates

Run these before opening or updating a PR:

```bash
pytest
python -m bw_defend.cli.main doctor --json
```

For release-bound changes, also ensure:

```bash
python -m bw_defend.cli.main rules verify --json
```

## Pull Request Requirements

- Fill out `.github/PULL_REQUEST_TEMPLATE.md`.
- Include validation evidence (commands and outcomes).
- Update docs when behavior, interfaces, or policy logic change.
- Explicitly describe blast radius and rollback path.

## Security Requirements

- Never commit malware samples, secrets, tokens, or private keys.
- Keep destructive actions approval-gated.
- Preserve audit trail behavior for remediation actions.
- Report vulnerabilities privately per `SECURITY.md`.

## Ownership

Sensitive files are governed by `.github/CODEOWNERS` and require security-owner review.
