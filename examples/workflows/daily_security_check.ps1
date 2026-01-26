# ============================================================================
# HifzDefend - Daily Security Check Workflow
# ============================================================================
# Automated daily security routine using AI-powered analysis
#
# Usage: .\daily_security_check.ps1
# ============================================================================

param(
    [switch]$Verbose,
    [switch]$SkipCostCheck
)

# Configuration
$scriptName = "Daily Security Check"
$logFile = "daily_check_$(Get-Date -Format 'yyyyMMdd').log"

# Helper function for logging
function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    $logMessage | Out-File -Append -FilePath $logFile
}

# Banner
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " HifzDefend Daily Security Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Log "Starting daily security check..." "Cyan"

# ==========================
# Step 1: Check AI Status
# ==========================

Write-Log "Step 1: Checking AI status..." "Yellow"

try {
    $testOutput = hifzdefend ai test 2>&1 | Out-String
    if ($testOutput -match "Connection successful") {
        Write-Log "[OK] AI features are operational" "Green"
    } else {
        Write-Log "[WARNING] AI test had issues" "Yellow"
        if ($Verbose) {
            Write-Host $testOutput -ForegroundColor Gray
        }
    }
} catch {
    Write-Log "[ERROR] Failed to test AI: $_" "Red"
}

Write-Host ""

# ==========================
# Step 2: Query Recent Threats
# ==========================

Write-Log "Step 2: Checking for recent threats..." "Yellow"

try {
    Write-Log "Querying: 'what threats were detected today?'" "Gray"
    hifzdefend query "what threats were detected today?"
    Write-Host ""
} catch {
    Write-Log "[ERROR] Threat query failed: $_" "Red"
}

# ==========================
# Step 3: Check Quarantine Status
# ==========================

Write-Log "Step 3: Checking quarantine status..." "Yellow"

try {
    Write-Log "Querying: 'did any files get quarantined today?'" "Gray"
    hifzdefend query "did any files get quarantined today?"
    Write-Host ""
} catch {
    Write-Log "[ERROR] Quarantine query failed: $_" "Red"
}

# ==========================
# Step 4: Network Activity Check
# ==========================

Write-Log "Step 4: Checking network activity..." "Yellow"

try {
    Write-Log "Querying: 'what domains were blocked today?'" "Gray"
    hifzdefend query "what domains were blocked today?"
    Write-Host ""
} catch {
    Write-Log "[ERROR] Network query failed: $_" "Red"
}

# ==========================
# Step 5: Check Downloads Folder
# ==========================

Write-Log "Step 5: Scanning downloads folder..." "Yellow"

$downloadsFolder = [Environment]::GetFolderPath("UserProfile") + "\Downloads"
if (Test-Path $downloadsFolder) {
    $recentFiles = Get-ChildItem -Path $downloadsFolder -File |
                   Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-1) } |
                   Where-Object { $_.Extension -in @('.exe', '.ps1', '.bat', '.cmd', '.vbs', '.js') }

    if ($recentFiles.Count -gt 0) {
        Write-Log "Found $($recentFiles.Count) potentially suspicious file(s) in Downloads" "Yellow"

        foreach ($file in $recentFiles | Select-Object -First 3) {
            Write-Log "  Analyzing: $($file.Name)" "Gray"
            try {
                hifzdefend analyze-script $file.FullName
                Write-Host ""
            } catch {
                Write-Log "[ERROR] Failed to analyze $($file.Name): $_" "Red"
            }
        }

        if ($recentFiles.Count -gt 3) {
            Write-Log "  ... and $($recentFiles.Count - 3) more files" "Gray"
            Write-Log "  Run manually: Get-ChildItem Downloads\*.exe | ForEach-Object { hifzdefend analyze-script `$_.FullName }" "Gray"
        }
    } else {
        Write-Log "[OK] No suspicious files in Downloads folder" "Green"
    }
} else {
    Write-Log "[WARNING] Downloads folder not found" "Yellow"
}

Write-Host ""

# ==========================
# Step 6: System Events Summary
# ==========================

Write-Log "Step 6: Generating security summary..." "Yellow"

try {
    Write-Log "Querying: 'summarize today's security events'" "Gray"
    hifzdefend query "summarize today's security events"
    Write-Host ""
} catch {
    Write-Log "[ERROR] Summary query failed: $_" "Red"
}

# ==========================
# Step 7: Cost Summary
# ==========================

if (-not $SkipCostCheck) {
    Write-Log "Step 7: Checking AI costs..." "Yellow"

    try {
        hifzdefend ai cost
        Write-Host ""
    } catch {
        Write-Log "[ERROR] Cost check failed: $_" "Red"
    }
}

# ==========================
# Step 8: AI Statistics
# ==========================

Write-Log "Step 8: AI usage statistics..." "Yellow"

try {
    hifzdefend ai stats
    Write-Host ""
} catch {
    Write-Log "[ERROR] Stats check failed: $_" "Red"
}

# ==========================
# Summary
# ==========================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Daily Check Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Log "Daily security check completed" "Green"
Write-Log "Log saved to: $logFile" "Cyan"

# Generate summary counts
$warningCount = (Get-Content $logFile | Select-String "\[WARNING\]").Count
$errorCount = (Get-Content $logFile | Select-String "\[ERROR\]").Count
$okCount = (Get-Content $logFile | Select-String "\[OK\]").Count

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  [OK]      : $okCount" -ForegroundColor Green
Write-Host "  [WARNING] : $warningCount" -ForegroundColor Yellow
Write-Host "  [ERROR]   : $errorCount" -ForegroundColor Red
Write-Host ""

if ($errorCount -gt 0) {
    Write-Host "ATTENTION: $errorCount error(s) detected. Review the log for details." -ForegroundColor Red
} elseif ($warningCount -gt 0) {
    Write-Host "Note: $warningCount warning(s) detected. Review if needed." -ForegroundColor Yellow
} else {
    Write-Host "All checks passed successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  - Review any warnings or errors" -ForegroundColor White
Write-Host "  - Investigate flagged files if any" -ForegroundColor White
Write-Host "  - Monitor AI costs: hifzdefend ai cost" -ForegroundColor White
Write-Host "  - Schedule this script to run daily" -ForegroundColor White
Write-Host ""

# Recommendation for scheduling
if (-not (Test-Path "C:\Windows\System32\schtasks.exe")) {
    Write-Host "To schedule this check daily:" -ForegroundColor Yellow
    Write-Host '  schtasks /create /tn "HifzDefend Daily Check" /tr "powershell -File \"' + $PSCommandPath + '\"" /sc daily /st 08:00' -ForegroundColor Gray
    Write-Host ""
}
