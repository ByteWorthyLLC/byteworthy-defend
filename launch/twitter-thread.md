# ByteWorthy Defend — Twitter / X Launch Thread

> 8 tweets, each ≤280 chars. Post Tuesday or Wednesday, 9-11am PT. Attach hero to tweet 1, demo GIF to tweet 4 (terminal scan → quarantine → JSON pipe), comparison shot to tweet 5.

## Tweet 1 — Hook (attach hero image)

```
Crowdstrike costs more than my mortgage.
ClamAV's CLI is from 2008.
Consumer AV assumes a desktop user.

I run 50 Linux servers and a few Windows boxes via Ansible.

So I built the CLI antivirus operators actually wanted. MIT licensed.
```

(252 chars)

## Tweet 2 — Problem

```
Every operator hits the same wall:

You want threat response wired into the same pipeline as everything else.
JSON in, JSON out, exit codes that mean something.

Enterprise EDR is GUI-first, per-seat priced, and impossible to put in a Salt grain.
```

(263 chars)

## Tweet 3 — Insight

```
The non-obvious bit:

Quarantine policy belongs in your infra repo, not in a vendor's console.

`policy.json` in version control means your security posture is auditable, reviewable, and rolls back like any other config change.
```

(231 chars)

## Tweet 4 — Solution (attach demo GIF)

```
Defend is what threat response looks like when it speaks pipeline:

defend scan ./ --output json | jq
defend quarantine list
defend quarantine remediate <id>

Watch mode via systemd. YARA rules in ~/.defend/rules/. Audit chain everywhere.
```

(247 chars)

## Tweet 5 — Proof (attach comparison shot)

```
Vendor EDR:
$, GUI-first, partial JSON, per-seat, closed-source

Consumer AV:
$$, desktop UX, no pipeline integration

Defend:
$0, CLI-first, JSON-out, MIT, audit chain by default

Pick the one that fits a sysadmin running 50 servers.
```

(245 chars)

## Tweet 6 — Transparency

```
MIT license. Free for personal, commercial, enterprise. Forever.

GitHub Sponsors keeps the lights on:
$5/mo - newsletter
$25/mo - Discord stargazer access
$99/mo - priority issue triage
Enterprise - custom rule packs + SLA

No vendor lock-in. No per-seat tax.
```

(257 chars)

## Tweet 7 — Use cases

```
Where Defend is running so far:

- DevSecOps wiring scans into CI before deploys
- Sysadmins running scheduled scans across Ansible-managed Linux fleets
- Self-hosted infra teams treating bastion hosts + build agents as targets
- DFIR folks using JSON output for automated triage
```

(269 chars)

## Tweet 8 — CTA

```
Install: pipx install byteworthy-defend
Repo: github.com/byteworthyllc/byteworthy-defend
Sponsor: github.com/sponsors/byteworthyllc

I'm one developer. Two years. Five products. Zero investors.

If Defend replaces a hand-rolled bash script, sponsor a tier.
```

(258 chars)

## Engagement plan

- Quote-tweet from `@byteworthyllc` org account 1hr after personal post
- Engage thoughtfully with security Twitter — `@SwiftOnSecurity`, `@mubix`, `@taviso`, `@malwaretech` if their recent thread is on-topic; never spam
- Reply to recent `tl;dr sec` newsletter tweets with link if topical
- Cross-post tweet 1 + 4 + 8 to LinkedIn 4 hours later
- Hashtags only on tweet 8 if needed: `#devsecops #cybersecurity #opensource`
- Avoid clickbait or fearmongering — security audience punishes both
