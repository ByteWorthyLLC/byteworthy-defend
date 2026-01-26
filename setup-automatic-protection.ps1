#Requires -Version 5.1
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Set up automatic HifzDefend protection using Windows Task Scheduler

.DESCRIPTION
    Creates scheduled tasks to automatically:
    - Monitor Downloads folder for new files
    - Scan system hourly
    - Generate daily security reports

.NOTES
    Requires Administrator privileges
#>

[CmdletBinding()]
param(
    [switch]$Remove
)

$ErrorActionPreference = "Stop"

# Configuration
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$hifzDefendPath = Join-Path $scriptDir "hifzdefend.ps1"
$taskPrefix = "HifzDefend"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "HifzDefend Automatic Protection" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[ERROR] This script requires Administrator privileges" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator', then run:" -ForegroundColor Yellow
    Write-Host "  cd '$scriptDir'" -ForegroundColor White
    Write-Host "  .\setup-automatic-protection.ps1" -ForegroundColor White
    exit 1
}

# Remove existing tasks if requested
if ($Remove) {
    Write-Host "[INFO] Removing HifzDefend scheduled tasks..." -ForegroundColor Yellow

    $tasks = @(
        "$taskPrefix - Monitor Downloads",
        "$taskPrefix - Hourly Scan",
        "$taskPrefix - Daily Report"
    )

    foreach ($taskName in $tasks) {
        try {
            $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($task) {
                Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
                Write-Host "  [OK] Removed: $taskName" -ForegroundColor Green
            }
        }
        catch {
            Write-Host "  [SKIP] Task not found: $taskName" -ForegroundColor Gray
        }
    }

    Write-Host ""
    Write-Host "[SUCCESS] Automatic protection disabled" -ForegroundColor Green
    exit 0
}

# Create monitoring scripts
Write-Host "[1/4] Creating monitoring scripts..." -ForegroundColor Cyan

# Script 1: Monitor Downloads Folder
$monitorDownloadsScript = @'
# Monitor Downloads Folder for New Files
$downloadsPath = [Environment]::GetFolderPath("Downloads")
$hifzDefendScript = "SCRIPT_DIR\hifzdefend.ps1"
$logFile = "$env:LOCALAPPDATA\HifzDefend\logs\downloads-monitor.log"

# Ensure log directory exists
$logDir = Split-Path -Parent $logFile
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Log function
function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -Append -FilePath $logFile
}

Write-Log "Starting downloads folder monitoring..."

# Get files modified in last hour
$cutoffTime = (Get-Date).AddHours(-1)
$newFiles = Get-ChildItem -Path $downloadsPath -File -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -gt $cutoffTime }

if ($newFiles) {
    Write-Log "Found $($newFiles.Count) new files in Downloads folder"

    foreach ($file in $newFiles) {
        Write-Log "Analyzing: $($file.Name)"

        # Analyze executable files, scripts, and archives
        if ($file.Extension -match '\.(exe|msi|ps1|bat|cmd|vbs|js|py|zip|rar|7z)$') {
            try {
                # Run analysis (suppress output, log to file)
                $result = & powershell.exe -ExecutionPolicy Bypass -File $hifzDefendScript analyze-script $file.FullName 2>&1

                # Check for threats in output
                if ($result -match 'MALICIOUS|SUSPICIOUS') {
                    Write-Log "WARNING: Potential threat detected in $($file.Name)!"

                    # Send Windows notification
                    $notificationParams = @{
                        ToastTitle = "HifzDefend Alert"
                        ToastText = "Suspicious file detected: $($file.Name)"
                    }
                    # Note: Would use BurntToast module in production

                    # Quarantine file
                    & powershell.exe -ExecutionPolicy Bypass -File $hifzDefendScript quarantine $file.FullName --threat-name "Auto-detected-threat"
                    Write-Log "File quarantined: $($file.Name)"
                }
                else {
                    Write-Log "File appears safe: $($file.Name)"
                }
            }
            catch {
                Write-Log "ERROR analyzing $($file.Name): $_"
            }
        }
    }
}
else {
    Write-Log "No new files in Downloads folder"
}

Write-Log "Monitoring complete"
'@.Replace('SCRIPT_DIR', $scriptDir)

$monitorScriptPath = Join-Path $scriptDir "scripts\monitor-downloads.ps1"
$monitorDownloadsScript | Out-File -FilePath $monitorScriptPath -Encoding UTF8 -Force

# Script 2: Hourly System Scan
$hourlyScanScript = @'
# Hourly System Security Scan
$hifzDefendScript = "SCRIPT_DIR\hifzdefend.ps1"
$logFile = "$env:LOCALAPPDATA\HifzDefend\logs\hourly-scan.log"

# Ensure log directory exists
$logDir = Split-Path -Parent $logFile
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Log function
function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -Append -FilePath $logFile
}

Write-Log "Starting hourly security scan..."

# Run system status check
try {
    $statusResult = & powershell.exe -ExecutionPolicy Bypass -File $hifzDefendScript status 2>&1
    Write-Log "System status checked"
}
catch {
    Write-Log "ERROR checking status: $_"
}

# Check AI cost
try {
    $costResult = & powershell.exe -ExecutionPolicy Bypass -File $hifzDefendScript ai cost 2>&1
    if ($costResult -match 'Total cost.*\$(\d+\.\d+)') {
        $totalCost = [decimal]$matches[1]
        Write-Log "Current AI cost: `$$totalCost"

        if ($totalCost -gt 10) {
            Write-Log "WARNING: AI costs exceed $10"
        }
    }
}
catch {
    Write-Log "ERROR checking costs: $_"
}

Write-Log "Hourly scan complete"
'@.Replace('SCRIPT_DIR', $scriptDir)

$hourlyScanPath = Join-Path $scriptDir "scripts\hourly-scan.ps1"
$hourlyScanScript | Out-File -FilePath $hourlyScanPath -Encoding UTF8 -Force

# Script 3: Daily Security Report
$dailyReportScript = @'
# Daily Security Report Generation
$hifzDefendScript = "SCRIPT_DIR\hifzdefend.ps1"
$logFile = "$env:LOCALAPPDATA\HifzDefend\logs\daily-report.log"
$reportFile = "$env:LOCALAPPDATA\HifzDefend\reports\daily-$(Get-Date -Format 'yyyy-MM-dd').txt"

# Ensure directories exist
foreach ($dir in @((Split-Path $logFile), (Split-Path $reportFile))) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Log function
function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -Append -FilePath $logFile
}

Write-Log "Generating daily security report..."

# Generate report
$report = @"
================================
HifzDefend Daily Security Report
================================
Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

System Status:
"@

# Add system status
try {
    $status = & powershell.exe -ExecutionPolicy Bypass -File $hifzDefendScript status 2>&1
    $report += "`n$status`n"
}
catch {
    $report += "`nERROR: Could not retrieve status`n"
}

# Add AI usage
$report += "`nAI Usage Summary:`n"
try {
    $aiStats = & powershell.exe -ExecutionPolicy Bypass -File $hifzDefendScript ai stats 2>&1
    $report += "`n$aiStats`n"
}
catch {
    $report += "`nERROR: Could not retrieve AI stats`n"
}

# Add quarantine list
$report += "`nQuarantined Files:`n"
try {
    $quarantine = & powershell.exe -ExecutionPolicy Bypass -File $hifzDefendScript list-quarantine 2>&1
    $report += "`n$quarantine`n"
}
catch {
    $report += "`nERROR: Could not retrieve quarantine list`n"
}

# Save report
$report | Out-File -FilePath $reportFile -Encoding UTF8
Write-Log "Report saved to: $reportFile"

# Send notification (would use email or notification service in production)
Write-Log "Daily report generation complete"
'@.Replace('SCRIPT_DIR', $scriptDir)

$dailyReportPath = Join-Path $scriptDir "scripts\daily-report.ps1"
$dailyReportScript | Out-File -FilePath $dailyReportPath -Encoding UTF8 -Force

Write-Host "  [OK] Monitoring scripts created" -ForegroundColor Green
Write-Host ""

# Create scheduled tasks
Write-Host "[2/4] Creating scheduled tasks..." -ForegroundColor Cyan

# Task 1: Monitor Downloads (every 10 minutes)
$action1 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$monitorScriptPath`""
$trigger1 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration ([TimeSpan]::MaxValue)
$settings1 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal1 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName "$taskPrefix - Monitor Downloads" -Action $action1 -Trigger $trigger1 -Settings $settings1 -Principal $principal1 -Description "Monitors Downloads folder for new files and analyzes them with HifzDefend" -Force | Out-Null
Write-Host "  [OK] Downloads monitoring (every 10 minutes)" -ForegroundColor Green

# Task 2: Hourly Scan
$action2 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$hourlyScanPath`""
$trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)
$settings2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal2 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName "$taskPrefix - Hourly Scan" -Action $action2 -Trigger $trigger2 -Settings $settings2 -Principal $principal2 -Description "Performs hourly system security checks" -Force | Out-Null
Write-Host "  [OK] Hourly security scan" -ForegroundColor Green

# Task 3: Daily Report (8 AM)
$action3 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$dailyReportPath`""
$trigger3 = New-ScheduledTaskTrigger -Daily -At 8am
$settings3 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal3 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName "$taskPrefix - Daily Report" -Action $action3 -Trigger $trigger3 -Settings $settings3 -Principal $principal3 -Description "Generates daily security report" -Force | Out-Null
Write-Host "  [OK] Daily security report (8 AM)" -ForegroundColor Green

Write-Host ""

# Summary
Write-Host "[3/4] Verifying scheduled tasks..." -ForegroundColor Cyan

$tasks = Get-ScheduledTask | Where-Object { $_.TaskName -like "$taskPrefix*" }
foreach ($task in $tasks) {
    $state = $task.State
    $stateColor = if ($state -eq "Ready") { "Green" } else { "Yellow" }
    Write-Host "  [$state] $($task.TaskName)" -ForegroundColor $stateColor
}

Write-Host ""

# Create uninstall script
Write-Host "[4/4] Creating management scripts..." -ForegroundColor Cyan

$uninstallScript = @'
# Remove HifzDefend Automatic Protection
Write-Host "Removing HifzDefend automatic protection..." -ForegroundColor Yellow
& "SCRIPT_DIR\setup-automatic-protection.ps1" -Remove
'@.Replace('SCRIPT_DIR', $scriptDir)

$uninstallPath = Join-Path $scriptDir "disable-automatic-protection.ps1"
$uninstallScript | Out-File -FilePath $uninstallPath -Encoding UTF8 -Force

Write-Host "  [OK] Management scripts created" -ForegroundColor Green
Write-Host ""

# Final summary
Write-Host "==================================" -ForegroundColor Green
Write-Host "SUCCESS! Automatic Protection Enabled" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "HifzDefend is now running automatically:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Downloads Monitoring:" -ForegroundColor Cyan
Write-Host "     - Checks Downloads folder every 10 minutes" -ForegroundColor Gray
Write-Host "     - Automatically analyzes new files" -ForegroundColor Gray
Write-Host "     - Quarantines threats" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Hourly Security Scan:" -ForegroundColor Cyan
Write-Host "     - System status check every hour" -ForegroundColor Gray
Write-Host "     - Cost monitoring" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Daily Security Report:" -ForegroundColor Cyan
Write-Host "     - Generated every morning at 8 AM" -ForegroundColor Gray
Write-Host "     - Saved to: %LOCALAPPDATA%\HifzDefend\reports\" -ForegroundColor Gray
Write-Host ""
Write-Host "View Logs:" -ForegroundColor Yellow
Write-Host "  %LOCALAPPDATA%\HifzDefend\logs\" -ForegroundColor White
Write-Host ""
Write-Host "Manage Protection:" -ForegroundColor Yellow
Write-Host "  - View tasks: taskschd.msc" -ForegroundColor White
Write-Host "  - Disable: .\disable-automatic-protection.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Note: This provides basic automation. Full real-time protection" -ForegroundColor Gray
Write-Host "      (like Windows Defender) is coming in v0.3.0" -ForegroundColor Gray
Write-Host ""
