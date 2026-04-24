$ErrorActionPreference = "Stop"

if (-not $IsWindows) {
  throw "windows gate must run on a Windows host"
}

$env:BW_DEFEND_CONFIG_DIR = "$pwd\.ci\config"
$env:BW_DEFEND_STATE_DIR = "$pwd\.ci\state"
$env:BW_DEFEND_RULES_SIGNATURE_REQUIRED = "true"
$env:BW_DEFEND_RULES_SIGNING_KEY = "ci-signing-key"

python -c "import hashlib,hmac,os; from bw_defend.core.rules import ensure_rules; p=ensure_rules(); s=hmac.new(os.environ['BW_DEFEND_RULES_SIGNING_KEY'].encode('utf-8'), p.read_bytes(), hashlib.sha256).hexdigest(); p.with_suffix(p.suffix + '.sig').write_text(f'{s}  {p.name}\n', encoding='utf-8')"

python -m pytest
skylos src --all --gate --no-upload

$doctorJson = bw-defend doctor --strict --json
$doctor = $doctorJson | ConvertFrom-Json

if (-not $doctor.checks.config_loaded) {
  throw "doctor check failed: config_loaded=false"
}

if (-not $doctor.checks.state_writable) {
  throw "doctor check failed: state_writable=false"
}

if (-not $doctor.checks.supported_platform) {
  throw "doctor check failed: supported_platform=false on Windows gate"
}

if ($doctor.platform -ne "windows") {
  throw "doctor platform mismatch on Windows gate"
}

bw-defend rules verify --json | Out-Null
bw-defend audit verify --json | Out-Null
python scripts/validate-docs.py

Write-Host "Windows gate passed"
