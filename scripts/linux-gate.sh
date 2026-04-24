#!/usr/bin/env bash
set -euo pipefail

python -m pytest
bw-defend doctor --strict --json
bw-defend rules verify --json
python3 scripts/validate-docs.py
