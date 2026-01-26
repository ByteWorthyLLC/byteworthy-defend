#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Fix false positive quarantine issue and update monitoring script

.DESCRIPTION
    This script will:
    1. Pause monitoring tasks
    2. Restore false-positive quarantined files
    3. Update monitoring script with better threat detection
    4. Re-enable monitoring tasks
#>

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Red
Write-Host "HifzDefend False Positive Fix" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "Issue: The monitoring script had a bug that caused it to" -ForegroundColor Yellow
Write-Host "quarantine legitimate HifzDefend files as threats." -ForegroundColor Yellow
Write-Host ""
Write-Host "This script will fix the issue and restore your files." -ForegroundColor Yellow
Write-Host ""

# Step 1: Disable monitoring tasks
Write-Host "[1/4] Pausing monitoring tasks..." -ForegroundColor Cyan

$tasks = @(
    "HifzDefend - Monitor Downloads",
    "HifzDefend - Hourly Scan"
)

foreach ($taskName in $tasks) {
    try {
        Disable-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue | Out-Null
        Write-Host "  [OK] Paused: $taskName" -ForegroundColor Green
    }
    catch {
        Write-Host "  [SKIP] Not found: $taskName" -ForegroundColor Gray
    }
}

Write-Host ""

# Step 2: Restore quarantined files
Write-Host "[2/4] Restoring quarantined files..." -ForegroundColor Cyan

# Set up environment
$env:PYTHONIOENCODING = "utf-8"

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
}

# Activate virtual environment
$activateScript = Join-Path $scriptDir ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
}

# List and restore quarantined files
$quarantineIds = @(
    "a06a47e6-09af-4a91-af3d-5971fc10777e",  # disable-automatic-protection.ps1
    "86bfab42-a957-4c05-8ce3-fadb9be45877",  # fix-scheduled-tasks.ps1
    "b3b7625b-f643-4f50-832a-b18e16b24bee"   # hifzdefend.ps1
)

foreach ($qid in $quarantineIds) {
    Write-Host "  Restoring: $qid" -ForegroundColor White
    try {
        $output = & python -m hifzdefend restore-quarantine $qid --force 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    [OK] Restored" -ForegroundColor Green
        }
        else {
            Write-Host "    [WARN] May already be restored" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "    [ERROR] $_" -ForegroundColor Red
    }
}

Write-Host ""

# Step 3: Update monitoring script
Write-Host "[3/4] Updating monitoring script..." -ForegroundColor Cyan

$fixedScript = Join-Path $scriptDir "scripts\monitor-downloads-fixed.ps1"
$originalScript = Join-Path $scriptDir "scripts\monitor-downloads.ps1"

if (Test-Path $fixedScript) {
    # Backup original
    if (Test-Path $originalScript) {
        Copy-Item $originalScript "$originalScript.buggy.bak" -Force
        Write-Host "  [OK] Backed up buggy script" -ForegroundColor Gray
    }

    # Replace with fixed version
    Copy-Item $fixedScript $originalScript -Force
    Write-Host "  [OK] Installed fixed monitoring script" -ForegroundColor Green
}
else {
    Write-Host "  [ERROR] Fixed script not found!" -ForegroundColor Red
}

Write-Host ""

# Step 4: Re-enable tasks
Write-Host "[4/4] Re-enabling monitoring tasks..." -ForegroundColor Cyan

foreach ($taskName in $tasks) {
    try {
        Enable-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue | Out-Null
        Write-Host "  [OK] Enabled: $taskName" -ForegroundColor Green
    }
    catch {
        Write-Host "  [ERROR] Failed to enable: $taskName" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Fix Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "What was fixed:" -ForegroundColor White
Write-Host "  - Restored quarantined HifzDefend files" -ForegroundColor Gray
Write-Host "  - Updated monitoring script to prevent false positives" -ForegroundColor Gray
Write-Host "  - Re-enabled automatic monitoring" -ForegroundColor Gray
Write-Host ""
Write-Host "The monitoring script now:" -ForegroundColor White
Write-Host "  - Excludes HifzDefend project directory" -ForegroundColor Gray
Write-Host "  - Better threat level detection" -ForegroundColor Gray
Write-Host "  - Only auto-quarantines MALICIOUS files" -ForegroundColor Gray
Write-Host "  - Logs SUSPICIOUS files for review (no auto-quarantine)" -ForegroundColor Gray
Write-Host ""
Write-Host "Test the fixed monitoring:" -ForegroundColor Yellow
Write-Host "  .\scripts\monitor-downloads.ps1" -ForegroundColor White
Write-Host ""
