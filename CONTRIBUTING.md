# Contributing to ByteWorthy

Thanks for considering a contribution! ByteWorthy is a one-developer studio, so contributions matter.

## Quick start

1. **Search [existing issues](../issues)** — your idea may already be discussed
2. **Open an issue first** for non-trivial changes — saves time vs surprise PRs
3. **Fork, branch, commit, PR** — standard workflow

## Branch + commit conventions

- Branch naming: `feature/short-desc`, `fix/short-desc`, `chore/short-desc`
- Commit format: [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, `refactor:`, etc.)
- Keep PRs focused on one logical change

## Code style

| Stack | Tools |
|---|---|
| TypeScript / JavaScript | `pnpm lint`, `pnpm typecheck`, Prettier |
| Python | `ruff format`, `ruff check`, `mypy` |
| Go | `gofmt`, `golangci-lint` |
| Markdown | `pnpm lint:md` (markdownlint) |

PRs must pass CI (lint + typecheck + tests) before review.

## Testing

- New features need tests
- Bug fixes need a regression test
- Integration tests over unit tests for critical paths
- See `__tests__/` or `tests/` for examples

## What we accept

✅ Bug fixes (always welcome)
✅ Documentation improvements
✅ Test coverage additions
✅ Performance improvements with benchmarks
✅ Accessibility improvements
✅ Translations (when product supports i18n)

## What we don't accept (without prior discussion)

❌ Major architecture changes — discuss in an Issue first
❌ New dependencies without justification
❌ Style-only changes (rename variables, reformat) without functional purpose
❌ Removal of telemetry/analytics (we use it minimally for product improvement)
❌ Vendor swaps (e.g., replacing Supabase with X) — these need product-level alignment

## DCO sign-off

All commits require a [Developer Certificate of Origin](https://developercertificate.org/) sign-off:

```bash
git commit -s -m "feat: add the thing"
```

Or configure once:
```bash
git config --global commit.gpgsign true
git config --global format.signoff true
```

## Code review

- All PRs reviewed by Kevin (founder)
- Expect 1-2 round of feedback
- We aim for ≤7-day review turnaround on community PRs
- Paid-tier customers get faster review windows

## Recognition

Contributors land in:
- `CONTRIBUTORS.md` (public list)
- Release notes (per release that includes their work)
- ByteWorthy newsletter shoutouts (optional, opt-in)

## Questions?

- 💬 [Discord](https://discord.gg/byteworthy) `#contributors` channel
- 📧 kevin@byteworthy.io for anything sensitive

Built by [Kevin Richards](https://byteworthy.io) at [ByteWorthy](https://byteworthy.io).
