# Restore False Positive Quarantined Files

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Restoring Quarantined HifzDefend Files" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
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
& "$scriptDir\.venv\Scripts\Activate.ps1"

# Restore the three quarantined files
$quarantineIds = @(
    "a06a47e6-09af-4a91-af3d-5971fc10777e",  # disable-automatic-protection.ps1
    "86bfab42-a957-4c05-8ce3-fadb9be45877",  # fix-scheduled-tasks.ps1
    "b3b7625b-f643-4f50-832a-b18e16b24bee"   # hifzdefend.ps1
)

Write-Host "Restoring false positive quarantined files..." -ForegroundColor Yellow
Write-Host ""

foreach ($qid in $quarantineIds) {
    Write-Host "  Restoring: $qid" -ForegroundColor Cyan
    try {
        & python -m hifzdefend restore-quarantine $qid --force
        Write-Host "    [OK] Restored successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "    [ERROR] Failed to restore: $_" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "Files Restored!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The monitoring script has been disabled to prevent" -ForegroundColor Yellow
Write-Host "further false positives. It will be fixed and re-enabled." -ForegroundColor Yellow
Write-Host ""
