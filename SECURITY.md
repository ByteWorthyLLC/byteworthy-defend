# Security Policy

## Supported versions

We support the latest minor version on the `main` branch. Security fixes are backported to the most recent tagged release.

## Reporting a vulnerability

**Please do NOT open a public GitHub Issue for security vulnerabilities.**

Email **security@byteworthy.io** with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Your contact information for follow-up

You'll receive an acknowledgment within 48 hours and a status update within 7 days.

## Disclosure policy

We follow **coordinated disclosure**:

1. We acknowledge receipt within 48 hours
2. We confirm the issue and determine severity within 7 days
3. We develop a fix and release it (typically within 30-90 days)
4. We disclose the issue publicly once a fix is available
5. We credit the reporter (unless they prefer anonymity)

Critical vulnerabilities (RCE, auth bypass, PHI exposure for healthcare products) are prioritized.

## Bug bounty

ByteWorthy does not currently run a formal bug bounty program. We do offer:
- Public credit (in our security advisories and release notes)
- ByteWorthy product credits / Pioneer tier access
- Paid bounties for impactful findings on healthcare products (Clynova) — case-by-case

## Scope

In scope:
- Authentication and authorization issues
- Data exposure (PHI, billing info, customer data)
- Injection vulnerabilities (SQL, XSS, SSRF, etc.)
- Cryptographic issues
- Dependency vulnerabilities with active exploitation paths

Out of scope:
- Self-XSS requiring user complicity
- Social engineering of ByteWorthy employees
- Issues requiring physical access to a victim's device
- Vulnerabilities in third-party services we depend on (report to those vendors)

## Built by ByteWorthy

> Maintained by [Kevin Richards](https://byteworthy.io). Security issues are P0 — they get faster responses than feature requests, even on the free tier.
