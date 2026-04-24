# Command Reference

## Global Output Contract

All operational commands support `--json`.

## Exit Codes

- `0`: success
- `1`: operational/runtime failure
- `2`: policy/validation gate failed (for example `rules verify` mismatch or `doctor --strict` check failure)

## Commands

- `bw-defend scan <path|system>`
- `bw-defend monitor start|stop|status`
- `bw-defend quarantine list|restore|purge`
- `bw-defend firewall status|apply|revert`
- `bw-defend process list|kill --pid <id> --approve`
- `bw-defend ai remediate <incident-id> [--approve]`
- `bw-defend rules update|list|verify`
- `bw-defend doctor`

## Notes

- `ai remediate` requires `edition = "ai"` in config.
- destructive actions (`delete`, `kill`, `network_block`) require `--approve` when policy enforces approval.
- `bw-defend rules verify` exits `2` if verification fails.
- `bw-defend doctor --strict` exits `2` if any health check fails, including unsupported runtime platform (supported: Windows and Linux).
