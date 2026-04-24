# CLI Contract v1

Stable top-level command surface for `bw-defend`:

- `scan`
- `monitor`
- `quarantine`
- `firewall`
- `process`
- `ai`
- `rules`
- `audit`
- `doctor`

## Compatibility Policy

- Removing or renaming top-level commands requires a major version bump.
- JSON output field removals for operational commands require a major version bump.
- New optional JSON fields are allowed in minor versions.
