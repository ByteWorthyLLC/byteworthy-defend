# ByteWorthy Defend — Show HN Launch Pack

> **Recommended launch window**: Tuesday or Wednesday, 8-10am PT. Security-Twitter overlap with HN is high — expect tougher scrutiny on detection claims.

## Title (60-character cap, action-led)

```
Show HN: Defend – Open-source CLI antivirus with JSON output
```

**Alternative titles** (rotate if first attempt doesn't catch):
- `Show HN: ByteWorthy Defend – Operator-first AV for Linux + Windows`
- `Show HN: Defend – CLI antivirus that wires into Ansible / GitHub Actions`
- `Show HN: Defend – YARA + quarantine + JSON-out, MIT licensed`

## First comment (post immediately after submission)

```
Hey HN — Kevin from ByteWorthy.

Defend is an open-source CLI antivirus for Windows and Linux (macOS too).
Operator-first: JSON output by default, quarantine lifecycle with policy gates,
YARA rule support, watch mode via systemd. Every command emits structured JSON
so you can wire threat response into Ansible, Salt, GitHub Actions, or whatever
orchestrator you actually use.

Why I built it: I run a fleet of Linux build agents and a few Windows VMs.
Crowdstrike is great if you're an enterprise with a six-figure budget. ClamAV
exists but its CLI is from a different decade. I wanted threat response that
behaves like every other tool in my pipeline — JSON in, JSON out, exit codes
that mean something.

How it's different:
  - JSON output by default — pipe to jq, Slack, PagerDuty without scraping
  - Quarantine policy as a JSON file checked into your infra repo
  - YARA rule support; drop your custom rules in `~/.defend/rules/`
  - Watch mode runs as a systemd unit (or Windows service)
  - Audit chain on every quarantine action (who, when, why, signed)

What's open / what's paid:
  - MIT license; free forever for any use
  - GitHub Sponsors funds development ($5/$25/$99/mo tiers)
  - Enterprise tier exists for custom rule packs + SLA + paid support

Demo: <link to GIF showing scan → quarantine → review → JSON pipeline>
Repo: github.com/byteworthyllc/byteworthy-defend
Sponsor: github.com/sponsors/byteworthyllc

Honest scope statement: Defend is not a replacement for kernel-mode AV at the
desktop user level. It's complementary tooling for engineers running self-hosted
infrastructure. If you have 50 Linux servers, a few Windows boxes, and you
already use Ansible — Defend is the threat-response tool you've probably been
hand-rolling.

Solo dev, two years in. Happy to answer anything about YARA tuning, quarantine
policy patterns, false-positive triage, or why I chose Python + Typer over Go.
```

## Pre-submission checklist

- [ ] Demo GIF (5-10s) shows: `defend scan ./ --output json | jq` → flag detection → `defend quarantine list` → policy gate review
- [ ] README hero loads at desktop + mobile widths
- [ ] github.com/byteworthyllc/byteworthy-defend description, topics (`antivirus`, `cybersecurity`, `devsecops`, `cli`, `yara`, `opensource`), social preview set
- [ ] byteworthy.io/defend page is up
- [ ] Discord invite link tested (not expired)
- [ ] First comment text in clipboard, ready to paste in <60s after submission
- [ ] PostHog UTM dashboard live (verify utm_source=hn captures)
- [ ] Twitter thread scheduled 30 min after HN submission
- [ ] LICENSE = MIT, plain and visible
- [ ] CHANGELOG.md current — last release within 7 days
- [ ] SECURITY.md describes coordinated disclosure (90 days, CVE for impactful)
- [ ] Bundled YARA rule set tested against EICAR test file (proof it actually scans)
- [ ] At least 3 sysadmin/DevSecOps friends know to read first, then upvote

## Avoid

- "Next-gen AI-powered EDR..." marketing-speak — security HN flags it instantly
- Claiming detection rates without methodology — security audience knows benchmarks lie
- Comparing to Crowdstrike on detection — Defend is complementary, not a replacement; say so
- Linking only to byteworthy.io — repo first, sponsor second, commercial last
- Replying defensively to skepticism on YARA-only detection — agree where they're right
- Disabling Issues or hiding the bug tracker — security audience expects transparency
- Inflating "production users" — name actual deployment patterns, not customer counts
- Hiding that Python isn't a kernel-level AV stack — Defend operates in userland; say so plainly
