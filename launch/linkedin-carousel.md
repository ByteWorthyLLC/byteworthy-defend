# ByteWorthy Defend — LinkedIn Carousel (8 slides)

> Export as PDF, 1080×1080 per slide. Defend accent color (`#4A4E54` slate-graphite) with red `#C9433D` for danger states. Mid-tone palette throughout. Post Tuesday 8am PT (DevSecOps LinkedIn is active early). Cross-post to security influencer DMs once core engagement settles.

---

## Slide 1 — Hook

**Copy**:
```
Crowdstrike costs more
than my mortgage.

ClamAV's CLI is from 2008.

Consumer AV assumes
I'm a desktop user.

I run 50 Linux servers
via Ansible.
```

**Design**:
- Bold serif headline (Fraunces 56pt) on cream
- Each comparison line set tighter, like a bash output block
- Slim "1/8" indicator bottom-right in mono
- Defend mark watermark bottom-left at 30% opacity
- No image — let the cadence land

---

## Slide 2 — The cost

**Copy**:
```
What every operator wants
from threat response:

- JSON in, JSON out
- Exit codes that mean something
- Policy as code, in version control
- Audit chains for every action
- Wire into Ansible, Salt, GHA

Enterprise EDR ships
none of this.
```

**Design**:
- Left-aligned bullet list, mono font (JetBrains Mono 28pt)
- Headline in Fraunces serif
- Bottom callout "Enterprise EDR ships none of this." in italic, slate
- Small icon row across the bottom: brackets, terminal, doc, lock, plug

---

## Slide 3 — The "what if"

**Copy**:
```
What if AV behaved
like every other tool
in your pipeline?

JSON in.
JSON out.
Policy as code.
```

**Design**:
- Three-line headline in Fraunces 56pt
- "in your pipeline" highlighted with a thin underline brushstroke in slate
- Triple-line copy below set in mono caps
- Empty space below

---

## Slide 4 — Introducing Defend

**Copy**:
```
ByteWorthy Defend

Open-source CLI antivirus
for Windows + Linux.

JSON output by default.
Policy gates as code.
YARA rule support.
Quarantine audit chain.

MIT licensed. Free forever.
```

**Design**:
- Defend mark anchor on the left, copy on the right
- Headline "ByteWorthy Defend" 80pt Fraunces in deep blue (#0F172A)
- Capability lines stacked, mono font with mid-dot separators
- "MIT licensed" pill bottom-right in slate

---

## Slide 5 — How it works (architecture)

**Copy**:
```
File system event
↓
Scan engine (signatures + YARA)
↓
Verdict (clean / suspect / malicious)
↓
Policy gate (JSON-defined)
↓
Quarantine vault (encrypted)
↓
Operator review (JSON or TUI)
↓
Audit chain (signed, append-only)
```

**Design**:
- Vertical flow diagram, each step in a card with thin connector arrow
- Use existing Defend `diagram-architecture.webp` simplified
- Mono font for technical labels
- Slate accents on policy gate + audit nodes (the load-bearing operator hooks)
- Small terminal-style frame around the whole diagram

---

## Slide 6 — Defend vs the alternatives

**Copy**:
```
Vendor EDR:
$$$ · GUI-first · partial JSON · per-seat · closed-source

Consumer AV:
$$ · desktop UX · no pipeline · mostly closed

Defend:
$0 · CLI-first · JSON-out · MIT · audit chain by default

Pick the one that fits
a fleet of 50 servers.
```

**Design**:
- Three rows, each with name + traits inline
- Each row has a horizontal cost bar (long → none)
- "Defend" row sized larger, in slate
- Bottom quote "Pick the one that fits a fleet of 50 servers." in italic

---

## Slide 7 — Pricing transparency

**Copy**:
```
MIT licensed.
Free forever for any use.

GitHub Sponsors funds the work:

$5/mo .... newsletter + name in CONTRIBUTORS
$25/mo ... Discord stargazer access
$99/mo ... priority issue triage
Enterprise ... custom rule packs + SLA

No vendor lock-in.
No per-seat tax.
```

**Design**:
- Header pill "MIT" in slate, prominent
- Sponsor tiers as dotted-leader rows (price right-aligned, mono)
- "Enterprise" row sized slightly larger
- Bottom italic quote in mono caps
- Defend mark watermark bottom-right at 20% opacity

---

## Slide 8 — CTA

**Copy**:
```
Install:
pipx install byteworthy-defend

Repo:
github.com/byteworthyllc/byteworthy-defend

Sponsor:
github.com/sponsors/byteworthyllc

Built by Kevin Richards
at ByteWorthy.

One developer.
Two years.
Five products.
Zero investors.
```

**Design**:
- Three stacked CTAs with chevron arrows in slate
- Founder credit block in middle-italic with portrait avatar (or initial mark)
- Stack signature at the bottom: "1 dev · 2 years · 5 products · 0 investors" in mono caps
- ByteWorthy mark + "byteworthy.io" wordmark bottom-right

---

## Caption (paste in LinkedIn post body, not the carousel)

```
Threat response that behaves like every other tool in your pipeline.

Crowdstrike costs more than my mortgage. ClamAV's CLI is from 2008. Consumer
AV assumes I'm a desktop user. None of those fit a sysadmin running 50 Linux
servers and a few Windows boxes via Ansible.

So I open-sourced the alternative.

ByteWorthy Defend is CLI-first antivirus with JSON output by default,
quarantine policy gates as code, YARA rule support, and audit chains on every
action. Watch mode runs as a systemd unit. Multi-platform (Linux, Windows,
macOS) from one Python codebase.

Honest framing: Defend is userland tooling, not kernel-mode EDR. It
complements enterprise EDR if you have it; it replaces the hand-rolled bash
if you don't.

MIT licensed, free forever. GitHub Sponsors funds development.

Repo: github.com/byteworthyllc/byteworthy-defend
Sponsor: github.com/sponsors/byteworthyllc

What's the threat-response automation you've been hand-rolling that this
could replace? Comments open.
```

## Engagement plan

- Reply to every comment in the first 6 hours
- DM the carousel as PDF to 5 specific DevSecOps leaders the day before for early shares
- Tag at most 1-2 people who'd genuinely benefit (no mass-tag)
- Repost from personal account 4 hours later with reflection comment
- LinkedIn newsletter follow-up the next week with deep-dive on policy.json DSL pattern
