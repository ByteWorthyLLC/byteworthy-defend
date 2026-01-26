#Requires -Version 5.1
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Disable HifzDefend automatic protection

.DESCRIPTION
    Removes all HifzDefend scheduled tasks to stop automatic monitoring
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "Disable HifzDefend Automatic Protection" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host ""

# Check if running as admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[ERROR] This script requires Administrator privileges" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator', then run:" -ForegroundColor Yellow
    Write-Host "  cd '$PSScriptRoot'" -ForegroundColor White
    Write-Host "  .\disable-automatic-protection.ps1" -ForegroundColor White
    exit 1
}

Write-Host "Removing HifzDefend scheduled tasks..." -ForegroundColor Yellow
Write-Host ""

$tasks = @(
    "HifzDefend - Monitor Downloads",
    "HifzDefend - Hourly Scan",
    "HifzDefend - Daily Report"
)

$removedCount = 0

foreach ($taskName in $tasks) {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task) {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
            Write-Host "  [OK] Removed: $taskName" -ForegroundColor Green
            $removedCount++
        }
        else {
            Write-Host "  [SKIP] Not found: $taskName" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  [ERROR] Failed to remove: $taskName" -ForegroundColor Red
    }
}

Write-Host ""

if ($removedCount -gt 0) {
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "SUCCESS! Automatic Protection Disabled" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Removed $removedCount scheduled task(s)" -ForegroundColor White
    Write-Host ""
    Write-Host "HifzDefend is now in manual mode." -ForegroundColor Yellow
    Write-Host "You can still use it via: .\hifzdefend.ps1 <command>" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To re-enable automatic protection:" -ForegroundColor Yellow
    Write-Host "  .\setup-automatic-protection.ps1" -ForegroundColor White
}
else {
    Write-Host "[INFO] No HifzDefend tasks were found" -ForegroundColor Cyan
    Write-Host "Automatic protection may already be disabled" -ForegroundColor Gray
}

Write-Host ""
