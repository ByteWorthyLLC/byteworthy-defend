# ============================================================================
# SAFE DEMO SCRIPT - benign_system_check.ps1
# ============================================================================
# Purpose: Safe system information check for testing HifzDefend
# Status: BENIGN - Safe to run and analyze
# Expected Analysis: Should be classified as SAFE/CLEAN
# ============================================================================

<#
.SYNOPSIS
    System Information Checker

.DESCRIPTION
    This is a SAFE demonstration script that gathers basic system information.
    It's designed for testing HifzDefend's AI analysis capabilities.

.EXAMPLE
    hifzdefend analyze-script benign_system_check.ps1

.NOTES
    This script performs only read-only operations.
    No modifications are made to the system.
#>

# Display script banner
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " System Information Check" -ForegroundColor Cyan
Write-Host " (Safe Demo Script for HifzDefend)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get basic system information
Write-Host "Collecting system information..." -ForegroundColor Yellow

# Computer information
$computerInfo = Get-ComputerInfo | Select-Object `
    CsName,
    OsName,
    OsVersion,
    OsBuildNumber,
    OsArchitecture,
    CsProcessors,
    CsTotalPhysicalMemory

# Display computer info
Write-Host "`nComputer Information:" -ForegroundColor Green
Write-Host "  Computer Name: $($computerInfo.CsName)"
Write-Host "  OS Name: $($computerInfo.OsName)"
Write-Host "  OS Version: $($computerInfo.OsVersion)"
Write-Host "  Architecture: $($computerInfo.OsArchitecture)"
Write-Host "  Processors: $($computerInfo.CsProcessors.Count)"
Write-Host "  Memory: $([math]::Round($computerInfo.CsTotalPhysicalMemory / 1GB, 2)) GB"

# Get PowerShell version
Write-Host "`nPowerShell Information:" -ForegroundColor Green
Write-Host "  Version: $($PSVersionTable.PSVersion)"
Write-Host "  Edition: $($PSVersionTable.PSEdition)"

# Get current date and time
Write-Host "`nSystem Time:" -ForegroundColor Green
Write-Host "  Current Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "  Time Zone: $([System.TimeZoneInfo]::Local.DisplayName)"

# Get disk space information
Write-Host "`nDisk Space:" -ForegroundColor Green
$drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null }
foreach ($drive in $drives) {
    $freeSpace = [math]::Round($drive.Free / 1GB, 2)
    $totalSpace = [math]::Round(($drive.Used + $drive.Free) / 1GB, 2)
    $usedPercent = [math]::Round(($drive.Used / ($drive.Used + $drive.Free)) * 100, 1)

    Write-Host "  Drive $($drive.Name):"
    Write-Host "    Total: $totalSpace GB"
    Write-Host "    Free: $freeSpace GB"
    Write-Host "    Used: $usedPercent%"
}

# Get network adapter information
Write-Host "`nNetwork Adapters:" -ForegroundColor Green
$adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' }
foreach ($adapter in $adapters) {
    Write-Host "  $($adapter.Name): $($adapter.Status) ($($adapter.LinkSpeed))"
}

# Check for Windows updates (read-only)
Write-Host "`nWindows Update Status:" -ForegroundColor Green
try {
    $updateSession = New-Object -ComObject Microsoft.Update.Session
    $updateSearcher = $updateSession.CreateUpdateSearcher()
    $searchResult = $updateSearcher.Search("IsInstalled=0")

    if ($searchResult.Updates.Count -eq 0) {
        Write-Host "  No pending updates" -ForegroundColor Green
    } else {
        Write-Host "  $($searchResult.Updates.Count) updates available" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Unable to check (requires elevation)" -ForegroundColor Gray
}

# Display security features status
Write-Host "`nSecurity Features:" -ForegroundColor Green

# Check Windows Defender status
$defenderStatus = Get-MpComputerStatus -ErrorAction SilentlyContinue
if ($defenderStatus) {
    Write-Host "  Defender Enabled: $($defenderStatus.AntivirusEnabled)"
    Write-Host "  Real-time Protection: $($defenderStatus.RealTimeProtectionEnabled)"
    Write-Host "  Last Quick Scan: $($defenderStatus.QuickScanEndTime)"
} else {
    Write-Host "  Windows Defender: Unable to check (requires elevation)" -ForegroundColor Gray
}

# Check firewall status
$firewallProfiles = Get-NetFirewallProfile
Write-Host "`nFirewall Status:" -ForegroundColor Green
foreach ($profile in $firewallProfiles) {
    Write-Host "  $($profile.Name): $($profile.Enabled)"
}

# Display running processes (top 10 by CPU)
Write-Host "`nTop 10 Processes by CPU:" -ForegroundColor Green
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 | ForEach-Object {
    Write-Host "  $($_.ProcessName): CPU=$([math]::Round($_.CPU, 2))s, Memory=$([math]::Round($_.WorkingSet64 / 1MB, 2))MB"
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " System Check Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script performed read-only operations only." -ForegroundColor Green
Write-Host "No changes were made to your system." -ForegroundColor Green
Write-Host ""

# HifzDefend Analysis Notes
# -------------------------
# This script should be classified as SAFE because:
# 1. Only performs read operations (Get-* cmdlets)
# 2. No network connections to external servers
# 3. No file modifications or downloads
# 4. No process execution or injections
# 5. No registry modifications
# 6. No PowerShell remoting or WMI abuse
# 7. Clear documentation and purpose
# 8. Standard system administration tasks
