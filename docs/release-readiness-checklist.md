# Release Readiness Checklist (Single Production Cut)

## Windows and Linux Packaging and Installability

- [ ] Linux package/install instructions verified on clean host
- [ ] Windows package/install instructions verified on clean host
- [ ] rollback instructions validated in dry-run and live-safe test
- [ ] command completion and help text verified for all required commands
- [ ] `bw-defend doctor --strict --json` passes on Linux release candidate host
- [ ] `bw-defend doctor --strict --json` passes on Windows release candidate host

## Security and Safety Gates

- [ ] rules update integrity verification passes with valid bundle and fails invalid bundle
- [ ] detached rule signature enforcement tested (`BW_DEFEND_RULES_SIGNATURE_REQUIRED=true`)
- [ ] quarantine lifecycle validated: list, restore, purge
- [ ] firewall apply/revert verified reversible
- [ ] process kill path requires approval and logs attempt
- [ ] `bw-defend audit verify --json` returns `status=ok` or `status=empty` on release candidate
- [ ] AI destructive actions blocked without `--approve`
- [ ] AI destructive actions execute with `--approve` and are audited

## Performance and Reliability

- [ ] monitor mode survives repeated start/stop cycles
- [ ] restart recovery of state files verified
- [ ] corrupted config behavior handled with actionable error
- [ ] offline mode tested for rule operations

## Documentation and Governance

- [ ] README command contract matches implementation
- [ ] architecture, runbook, testing, security docs reviewed
- [ ] CONTRIBUTING, SECURITY, CODEOWNERS, issue/PR templates present and current
- [ ] threat model and security review completed
- [ ] `./scripts/validate-docs.sh` passes on release candidate commit

## Final Sign-Off Evidence

- [ ] CI/test run URL or terminal logs captured
- [ ] release notes include known limitations
- [ ] rollback owner and on-call owner assigned
