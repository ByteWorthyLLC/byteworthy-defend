# Architecture

## Product Boundaries

ByteWorthy Defend is Windows and Linux endpoint protection operated from a terminal interface.

Repository modules:

- `core/`: scanning, rule lifecycle, quarantine, incidents, policy
- `security/`: process and firewall controls (reversible)
- `ai/`: optional remediation orchestration
- `cli/`: stable operator interface (`bw-defend`)

## Runtime Data Paths

- config:
  - Linux: `~/.config/bw-defend/config.toml`
  - Windows: `%APPDATA%\\bw-defend\\config.toml`
- state root:
  - Linux: `~/.local/state/bw-defend/`
  - Windows: `%LOCALAPPDATA%\\bw-defend\\state\\`
- incidents log: `incidents.jsonl`
- audit trail: `audit.log`
- monitor state: `monitor.json`
- firewall state: `firewall.json`
- quarantine manifest: `quarantine/manifest.json`
- rules store: `rules/active-rules.json`

## Edition Model

- `core`: no AI dependencies; deterministic and policy-managed controls
- `ai`: adds remediation planner/executor; still constrained by policy engine

## Safety Invariants

1. AI cannot bypass policy evaluation.
2. Destructive actions require explicit approval.
3. Every proposed and executed remediation step is audit-logged.
4. Quarantine and firewall controls are reversible through first-class CLI commands.
