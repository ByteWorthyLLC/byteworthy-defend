#!/usr/bin/env bash
set -euo pipefail

pytest
bw-defend doctor --strict --json
bw-defend rules verify --json
./scripts/validate-docs.sh
