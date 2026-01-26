#Requires -RunAsAdministrator

Write-Host "Temporarily disabling monitoring tasks..." -ForegroundColor Yellow

$tasks = @(
    "HifzDefend - Monitor Downloads",
    "HifzDefend - Hourly Scan"
)

foreach ($taskName in $tasks) {
    try {
        Disable-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue | Out-Null
        Write-Host "  [OK] Disabled: $taskName" -ForegroundColor Green
    }
    catch {
        Write-Host "  [SKIP] Task not found: $taskName" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Monitoring paused. Run restore-quarantined-files.ps1 next." -ForegroundColor Cyan
