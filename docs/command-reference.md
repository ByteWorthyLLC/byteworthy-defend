# Command Reference

## Global Output Contract

All operational commands support `--json`.

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
