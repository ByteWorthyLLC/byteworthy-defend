# Release Blockers

Use this file as a strict gate. A release cannot proceed if any blocker remains unchecked.

- [ ] unresolved critical or high security finding
- [ ] failing CI/security/release-readiness checks
- [ ] failing supply-chain workflow checks
- [ ] unresolved dependency vulnerabilities in audit report
- [ ] failed rollback drill in current release cycle
- [ ] incomplete threat model or security evidence updates
- [ ] missing SBOM/checksums/provenance evidence for release candidate
- [ ] missing independent third-party security review report
- [ ] command contract drift between README and CLI implementation
