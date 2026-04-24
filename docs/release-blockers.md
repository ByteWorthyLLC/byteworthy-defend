# Release Blockers

Use this file as a strict gate. A release cannot proceed if any blocker remains unchecked.

- [ ] unresolved critical or high security finding
- [ ] failing CI/security/release-readiness checks
- [ ] failed rollback drill in current release cycle
- [ ] incomplete threat model or security evidence updates
- [ ] command contract drift between README and CLI implementation
