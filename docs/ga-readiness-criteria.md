# GA Readiness Criteria

A release is production-ready only when all criteria are true.

## Mandatory Gates

- [ ] CI workflow green on `main` for Linux and Windows jobs
- [ ] Security workflow green on `main`
- [ ] Release-readiness workflow green on `main`
- [ ] Supply-chain workflow green on `main` or release tag
- [ ] `pytest` passes on release commit for Linux and Windows runners
- [ ] all release checklist items in `docs/release-readiness-checklist.md` checked

## Safety and Controls

- [ ] policy gate tested for destructive actions without `--approve`
- [ ] approved destructive action path tested and audited
- [ ] audit-chain verification gate passes (`bw-defend audit verify --json`)
- [ ] detached signature rules gate tested in required mode
- [ ] quarantine restore and purge behavior validated
- [ ] firewall apply/revert reversible in test environment

## Evidence

- [ ] release notes include risk summary and rollback owner
- [ ] command/test logs archived for release tag
- [ ] security evidence pack reviewed and linked
- [ ] dependency audit report attached to release evidence
- [ ] SBOM + SHA256SUMS + provenance attestation attached to release evidence
- [ ] third-party independent review report linked
