# GA Readiness Criteria

A release is production-ready only when all criteria are true.

## Mandatory Gates

- [ ] CI workflow green on `main` for Linux and Windows jobs
- [ ] Security workflow green on `main`
- [ ] Release-readiness workflow green on `main`
- [ ] `pytest` passes on release commit for Linux and Windows runners
- [ ] all release checklist items in `docs/release-readiness-checklist.md` checked

## Safety and Controls

- [ ] policy gate tested for destructive actions without `--approve`
- [ ] approved destructive action path tested and audited
- [ ] quarantine restore and purge behavior validated
- [ ] firewall apply/revert reversible in test environment

## Evidence

- [ ] release notes include risk summary and rollback owner
- [ ] command/test logs archived for release tag
- [ ] security evidence pack reviewed and linked
