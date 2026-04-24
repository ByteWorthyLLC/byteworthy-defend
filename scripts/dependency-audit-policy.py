#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: dependency-audit-policy.py <pip-audit-json>", file=sys.stderr)
        return 2

    report_path = Path(sys.argv[1])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    dependencies = report.get("dependencies", [])

    vulnerable = []
    skipped = []
    for dep in dependencies:
        name = dep.get("name", "unknown")
        if dep.get("skip_reason"):
            skipped.append({"name": name, "reason": dep["skip_reason"]})
            continue
        vulns = dep.get("vulns", [])
        if vulns:
            vulnerable.append({"name": name, "vulns": vulns})

    payload = {
        "ok": len(vulnerable) == 0,
        "dependency_count": len(dependencies),
        "skipped_count": len(skipped),
        "vulnerable_count": len(vulnerable),
        "vulnerable": vulnerable,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
