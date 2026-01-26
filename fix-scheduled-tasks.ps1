#Requires -Version 5.1
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Fix HifzDefend scheduled tasks with correct duration format

.DESCRIPTION
    Recreates the two failed scheduled tasks with proper RepetitionDuration
    that doesn't exceed Windows Task Scheduler's XML format limits.
#>

$ErrorActionPreference = "Stop"

# Configuration
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$taskPrefix = "HifzDefend"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Fixing HifzDefend Scheduled Tasks" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[ERROR] This script requires Administrator privileges" -ForegroundColor Red
    exit 1
}

# Remove failed tasks
Write-Host "[1/2] Removing failed tasks..." -ForegroundColor Cyan
Write-Host ""

$failedTasks = @(
    "$taskPrefix - Monitor Downloads",
    "$taskPrefix - Hourly Scan"
)

foreach ($taskName in $failedTasks) {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task) {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
        }
    }
    catch {
        # Silently continue if task doesn't exist
    }
}

Write-Host ""

# Recreate tasks with fixed duration
Write-Host "[2/2] Creating fixed tasks..." -ForegroundColor Cyan
Write-Host ""

$monitorScriptPath = Join-Path $scriptDir "scripts\monitor-downloads.ps1"
$hourlyScanPath = Join-Path $scriptDir "scripts\hourly-scan.ps1"

# Task 1: Monitor Downloads (every 10 minutes) - FIXED DURATION
$action1 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$monitorScriptPath`""
$trigger1 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 9999)
$settings1 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal1 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName "$taskPrefix - Monitor Downloads" -Action $action1 -Trigger $trigger1 -Settings $settings1 -Principal $principal1 -Description "Monitors Downloads folder for new files and analyzes them with HifzDefend" -Force | Out-Null
Write-Host "  [OK] Downloads monitoring (every 10 minutes)" -ForegroundColor Green

# Task 2: Hourly Scan - FIXED DURATION
$action2 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$hourlyScanPath`""
$trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 9999)
$settings2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal2 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName "$taskPrefix - Hourly Scan" -Action $action2 -Trigger $trigger2 -Settings $settings2 -Principal $principal2 -Description "Performs hourly system security checks" -Force | Out-Null
Write-Host "  [OK] Hourly security scan" -ForegroundColor Green

Write-Host ""
Write-Host "==================================" -ForegroundColor Green
Write-Host "Verification" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""

# Verify all tasks
$tasks = Get-ScheduledTask | Where-Object { $_.TaskName -like "$taskPrefix*" }

if ($tasks.Count -eq 3) {
    Write-Host "[SUCCESS] All 3 tasks created successfully!" -ForegroundColor Green
    Write-Host ""
    foreach ($task in $tasks | Sort-Object TaskName) {
        Write-Host "  [$($task.State)] $($task.TaskName)" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "HifzDefend automatic protection is now fully operational!" -ForegroundColor Green
}
else {
    Write-Host "[WARNING] Expected 3 tasks, found $($tasks.Count)" -ForegroundColor Yellow
}

Write-Host ""
