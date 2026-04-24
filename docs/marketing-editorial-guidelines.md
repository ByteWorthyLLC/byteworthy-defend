# Marketing Editorial Guidelines

Use this guide for all user-facing content in README, docs, and site pages.

## Voice Rules

1. Lead with operator outcomes.
2. Keep language direct and concrete.
3. State limits and prerequisites clearly.
4. Tie claims to verifiable repository assets.

## Style Rules

1. Use short paragraphs and explicit sections.
2. Prefer checklists, commands, and tables over vague prose.
3. Keep naming consistent: `ByteWorthy Defend` and `bw-defend`.
4. Keep Linux-first scope explicit for production declarations.

## Phrase Policy

Do not use these phrases in user-facing copy:

- revolutionary
- cutting-edge
- seamless
- game-changing
- leverage
- unlock

## Product Context Rules

Keep ByteWorthy references explicit and accurate:

1. Sovra: open-source AI SaaS baseline
2. Klienta: paid white-label baseline
3. Clynova: paid healthcare baseline
4. ByteWorthy Defend: open-source Linux endpoint defense CLI

## Offer Clarity Checklist

Every public page should answer:

1. Who is this for?
2. What is included?
3. What is not included?
4. How quickly can teams start?
5. How is production readiness validated?
6. Where are security and support policies documented?

## Proof-First Checklist

Back claims with links to:

- commands in `README.md` and `docs/command-reference.md`
- release gates in `.github/workflows/` and `docs/release-readiness-checklist.md`
- security posture in `SECURITY.md` and `docs/security.md`
- incident and policy behavior in `src/bw_defend/core/*`

## Pre-Publish Steps

1. Run `pytest`.
2. Run `./scripts/validate-docs.sh`.
3. Validate command snippets.
4. Check links and canonical URLs.
