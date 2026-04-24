$ErrorActionPreference = "Stop"

if (-not $IsWindows) {
  throw "windows gate must run on a Windows host"
}

python -m pytest

$doctorJson = bw-defend doctor --json
$doctor = $doctorJson | ConvertFrom-Json

if (-not $doctor.checks.config_loaded) {
  throw "doctor check failed: config_loaded=false"
}

if (-not $doctor.checks.state_writable) {
  throw "doctor check failed: state_writable=false"
}

if ($doctor.checks.linux_target) {
  throw "doctor check failed: linux_target=true on Windows gate"
}

bw-defend rules verify --json | Out-Null
python scripts/validate-docs.py

Write-Host "Windows gate passed"
