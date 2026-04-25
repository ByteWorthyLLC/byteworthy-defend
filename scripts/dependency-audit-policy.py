#!/usr/bin/env python3
"""Dependency audit policy: fail CI on any vulnerability that is not in the allowlist.

Allowlisted CVEs require:
- A justification (typically: no upstream fix available, or transitive in build-only dep)
- A review-by date (we re-evaluate at every cadence)
- Documentation of why the risk is acceptable for ByteWorthy Defend's threat model
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# CVEs allowlisted with explicit justification.
# Format: { "CVE-id": { "package": "...", "justification": "...", "review_by": "YYYY-MM-DD" } }
ALLOWLIST = {
    "CVE-2026-3219": {
        "package": "pip",
        "justification": (
            "pip handles concatenated tar+ZIP files as ZIP. No upstream fix yet "
            "(fix_versions: []). pip is a build-time dep for installing Defend, "
            "not a runtime surface. Concatenated archive scenario does not apply "
            "to ByteWorthy distribution channels (PyPI + signed releases). "
            "Risk: low. Re-evaluate when pip ships fix."
        ),
        "review_by": "2026-07-25",
    },
}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: dependency-audit-policy.py <pip-audit-json>", file=sys.stderr)
        return 2

    report_path = Path(sys.argv[1])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    dependencies = report.get("dependencies", [])

    vulnerable = []
    allowlisted = []
    skipped = []
    for dep in dependencies:
        name = dep.get("name", "unknown")
        if dep.get("skip_reason"):
            skipped.append({"name": name, "reason": dep["skip_reason"]})
            continue
        vulns = dep.get("vulns", [])
        if not vulns:
            continue
        # Partition vulns into blocking vs allowlisted
        blocking = []
        allowed = []
        for v in vulns:
            cve_id = v.get("id", "")
            if cve_id in ALLOWLIST:
                allowed.append({**v, "_allowlist": ALLOWLIST[cve_id]})
            else:
                blocking.append(v)
        if blocking:
            vulnerable.append({"name": name, "vulns": blocking})
        if allowed:
            allowlisted.append({"name": name, "vulns": allowed})

    payload = {
        "ok": len(vulnerable) == 0,
        "dependency_count": len(dependencies),
        "skipped_count": len(skipped),
        "vulnerable_count": len(vulnerable),
        "allowlisted_count": len(allowlisted),
        "vulnerable": vulnerable,
        "allowlisted": allowlisted,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
