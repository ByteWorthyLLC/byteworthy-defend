#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
SKYLOS_BIN="${SKYLOS_BIN:-skylos}"

export BW_DEFEND_CONFIG_DIR="${PWD}/.ci/config"
export BW_DEFEND_STATE_DIR="${PWD}/.ci/state"
export BW_DEFEND_RULES_SIGNATURE_REQUIRED="true"
export BW_DEFEND_RULES_SIGNING_KEY="ci-signing-key"

"${PYTHON_BIN}" - <<'PY'
import hashlib
import hmac
import os

from bw_defend.core.rules import ensure_rules

path = ensure_rules()
signature = hmac.new(os.environ["BW_DEFEND_RULES_SIGNING_KEY"].encode("utf-8"), path.read_bytes(), hashlib.sha256).hexdigest()
path.with_suffix(path.suffix + ".sig").write_text(f"{signature}  {path.name}\n", encoding="utf-8")
PY

"${PYTHON_BIN}" -m pytest
"${SKYLOS_BIN}" src --all --gate --no-upload
bw-defend doctor --strict --json
bw-defend rules verify --json
bw-defend audit verify --json
"${PYTHON_BIN}" scripts/validate-docs.py
