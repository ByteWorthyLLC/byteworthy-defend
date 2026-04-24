#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify release artifact integrity and required files")
    parser.add_argument("--dist", type=str, default="dist", help="Distribution directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dist_dir = Path(args.dist)
    if not dist_dir.is_dir():
        print(f"distribution directory missing: {dist_dir}", file=sys.stderr)
        return 1

    checksums = dist_dir / "SHA256SUMS"
    sbom = dist_dir / "sbom.cdx.json"
    if not checksums.is_file():
        print("missing SHA256SUMS", file=sys.stderr)
        return 1
    if not sbom.is_file():
        print("missing sbom.cdx.json", file=sys.stderr)
        return 1

    sbom_payload = json.loads(sbom.read_text(encoding="utf-8"))
    if "components" not in sbom_payload:
        print("sbom.cdx.json missing 'components'", file=sys.stderr)
        return 1

    failures = []
    for line in checksums.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            failures.append(f"invalid checksum line: {line}")
            continue
        expected, filename = parts[0], parts[-1]
        path = dist_dir / filename
        if not path.is_file():
            failures.append(f"missing artifact listed in SHA256SUMS: {filename}")
            continue
        actual = _sha256(path)
        if actual != expected:
            failures.append(f"checksum mismatch for {filename}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    print("release artifacts verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
