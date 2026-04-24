#!/usr/bin/env bash
set -euo pipefail

required=(
  README.md
  MARKETING.md
  llms.txt
  Dockerfile
  docker-compose.yml
  CONTRIBUTING.md
  SECURITY.md
  SUPPORT.md
  docs/index.md
  docs/llms.txt
  docs/architecture.md
  docs/command-reference.md
  docs/deployment-guide.md
  docs/operations-runbook.md
  docs/release-process.md
  docs/release-readiness-checklist.md
  docs/production-readiness.md
  docs/ga-readiness-criteria.md
  docs/release-blockers.md
  docs/security.md
  docs/threat-model.md
  docs/support-and-release-cadence.md
  docs/github-cutover-runbook.md
  docs/github-hardening.md
  docs/marketing-editorial-guidelines.md
  docs/seo-aeo-geo-playbook.md
  site/index.html
  site/trust.html
  site/robots.txt
  site/sitemap.xml
  site/llms.txt
  scripts/linux-gate.sh
)

for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing required documentation file: $f" >&2
    exit 1
  fi
done

echo "Docs validation passed"
