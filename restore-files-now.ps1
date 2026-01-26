# Restore Quarantined Files - Manual Method

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONIOENCODING = "utf-8"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Restoring Quarantined Files" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Load .env file
$envFile = Join-Path $scriptDir ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#')) {
            if ($line -match '^([^=]+)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                [Environment]::SetEnvironmentVariable($key, $value, 'Process')
            }
        }
    }
    Write-Host "[OK] Loaded API key from .env" -ForegroundColor Green
}

# Activate virtual environment
$activateScript = Join-Path $scriptDir ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "[OK] Activated virtual environment" -ForegroundColor Green
}

Write-Host ""
Write-Host "Listing quarantined files..." -ForegroundColor Yellow
Write-Host ""

# List quarantine
$listOutput = & python -m hifzdefend list-quarantine 2>&1 | Out-String
Write-Host $listOutput

Write-Host ""
Write-Host "Restoring files by ID..." -ForegroundColor Yellow
Write-Host ""

# Restore each file
$quarantineIds = @(
    "a06a47e6-09af-4a91-af3d-5971fc10777e",
    "86bfab42-a957-4c05-8ce3-fadb9be45877",
    "b3b7625b-f643-4f50-832a-b18e16b24bee"
)

foreach ($qid in $quarantineIds) {
    Write-Host "Restoring: $qid" -ForegroundColor Cyan
    $output = & python -m hifzdefend restore-quarantine $qid --force 2>&1 | Out-String
    Write-Host $output
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "Checking if files are restored..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$files = @(
    "hifzdefend.ps1",
    "fix-scheduled-tasks.ps1",
    "disable-automatic-protection.ps1"
)

foreach ($file in $files) {
    $exists = Test-Path (Join-Path $scriptDir $file)
    if ($exists) {
        Write-Host "  [OK] $file - RESTORED" -ForegroundColor Green
    }
    else {
        Write-Host "  [MISSING] $file - NOT FOUND" -ForegroundColor Red
    }
}

Write-Host ""
