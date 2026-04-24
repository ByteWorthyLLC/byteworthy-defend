#!/usr/bin/env bash
set -euo pipefail

export BW_DEFEND_CONFIG_DIR="${PWD}/.ci/config"
export BW_DEFEND_STATE_DIR="${PWD}/.ci/state"
export BW_DEFEND_RULES_SIGNATURE_REQUIRED="true"
export BW_DEFEND_RULES_SIGNING_KEY="ci-signing-key"

python - <<'PY'
import hashlib
import hmac
import os

from bw_defend.core.rules import ensure_rules

path = ensure_rules()
signature = hmac.new(os.environ["BW_DEFEND_RULES_SIGNING_KEY"].encode("utf-8"), path.read_bytes(), hashlib.sha256).hexdigest()
path.with_suffix(path.suffix + ".sig").write_text(f"{signature}  {path.name}\n", encoding="utf-8")
PY

python -m pytest
bw-defend doctor --strict --json
bw-defend rules verify --json
bw-defend audit verify --json
python3 scripts/validate-docs.py
