$ErrorActionPreference = "Stop"

if (-not $IsWindows) {
  throw "windows gate must run on a Windows host"
}

python -m pytest

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
python scripts/validate-docs.py

Write-Host "Windows gate passed"
