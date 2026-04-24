#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REQUIRED_FILES = [
    "README.md",
    "MARKETING.md",
    "llms.txt",
    "Dockerfile",
    "docker-compose.yml",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
    "docs/index.md",
    "docs/llms.txt",
    "docs/architecture.md",
    "docs/command-reference.md",
    "docs/deployment-guide.md",
    "docs/operations-runbook.md",
    "docs/release-process.md",
    "docs/release-readiness-checklist.md",
    "docs/production-readiness.md",
    "docs/ga-readiness-criteria.md",
    "docs/release-blockers.md",
    "docs/security.md",
    "docs/threat-model.md",
    "docs/support-and-release-cadence.md",
    "docs/github-cutover-runbook.md",
    "docs/github-hardening.md",
    "docs/marketing-editorial-guidelines.md",
    "docs/seo-aeo-geo-playbook.md",
    "site/index.html",
    "site/trust.html",
    "site/robots.txt",
    "site/sitemap.xml",
    "site/llms.txt",
    "scripts/validate-docs.py",
    "scripts/linux-gate.sh",
    "scripts/windows-gate.ps1",
]


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    missing = [path for path in REQUIRED_FILES if not (repo_root / path).is_file()]
    if missing:
        for path in missing:
            print(f"Missing required documentation file: {path}", file=sys.stderr)
        return 1
    print("Docs validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
