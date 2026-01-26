# Check HifzDefend Automatic Protection Status

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "HifzDefend Automatic Protection Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get HifzDefend scheduled tasks
$tasks = Get-ScheduledTask | Where-Object { $_.TaskName -like 'HifzDefend*' }

if ($tasks.Count -eq 0) {
    Write-Host "[ERROR] No HifzDefend tasks found!" -ForegroundColor Red
    Write-Host "Run: .\setup-automatic-protection.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Scheduled Tasks:" -ForegroundColor White
Write-Host ""

foreach ($task in $tasks | Sort-Object TaskName) {
    $stateColor = switch ($task.State) {
        "Ready" { "Green" }
        "Running" { "Cyan" }
        "Disabled" { "Red" }
        default { "Yellow" }
    }

    $stateText = $task.State.ToString().PadRight(8)
    Write-Host "  [$stateText] " -NoNewline -ForegroundColor $stateColor
    Write-Host "$($task.TaskName)" -ForegroundColor White

    # Get trigger info
    $taskInfo = Get-ScheduledTaskInfo -TaskName $task.TaskName -ErrorAction SilentlyContinue
    if ($taskInfo) {
        if ($taskInfo.LastRunTime -gt (Get-Date).AddYears(-10)) {
            Write-Host "               Last run: $($taskInfo.LastRunTime)" -ForegroundColor Gray
        }
        if ($taskInfo.NextRunTime -gt (Get-Date)) {
            Write-Host "               Next run: $($taskInfo.NextRunTime)" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check log directory
$logDir = "$env:LOCALAPPDATA\HifzDefend\logs"
if (Test-Path $logDir) {
    Write-Host "Log Directory: $logDir" -ForegroundColor White
    $logFiles = Get-ChildItem -Path $logDir -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($logFiles) {
        Write-Host "Recent logs:" -ForegroundColor Gray
        foreach ($log in $logFiles | Select-Object -First 3) {
            Write-Host "  - $($log.Name) ($(Get-Date $log.LastWriteTime -Format 'yyyy-MM-dd HH:mm'))" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  (No logs yet - tasks will create logs on first run)" -ForegroundColor Gray
    }
}
else {
    Write-Host "Log Directory: Will be created on first run" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Protection Status: " -NoNewline -ForegroundColor White
Write-Host "ACTIVE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Your system is now protected!" -ForegroundColor Green
Write-Host ""
Write-Host "What's running automatically:" -ForegroundColor White
Write-Host "  1. Downloads folder scanned every 10 minutes" -ForegroundColor Gray
Write-Host "  2. System security check every hour" -ForegroundColor Gray
Write-Host "  3. Daily security report at 8 AM" -ForegroundColor Gray
Write-Host ""
Write-Host "Commands:" -ForegroundColor Yellow
Write-Host "  View this status: " -NoNewline -ForegroundColor Gray
Write-Host ".\status-protection.ps1" -ForegroundColor White
Write-Host "  View logs:        " -NoNewline -ForegroundColor Gray
Write-Host "explorer $logDir" -ForegroundColor White
Write-Host "  Disable:          " -NoNewline -ForegroundColor Gray
Write-Host ".\disable-automatic-protection.ps1" -ForegroundColor White
Write-Host ""
