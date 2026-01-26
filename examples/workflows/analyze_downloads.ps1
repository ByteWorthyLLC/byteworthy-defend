# ============================================================================
# HifzDefend - Analyze Downloads Folder Workflow
# ============================================================================
# Scans and analyzes all executable files in Downloads folder
#
# Usage: .\analyze_downloads.ps1 [-DaysBack 7] [-AutoQuarantine]
# ============================================================================

param(
    [int]$DaysBack = 7,
    [switch]$AutoQuarantine,
    [switch]$ShowCleanFiles
)

# Configuration
$downloadsFolder = [Environment]::GetFolderPath("UserProfile") + "\Downloads"
$suspiciousExtensions = @('.exe', '.ps1', '.bat', '.cmd', '.vbs', '.js', '.jar', '.msi', '.scr', '.dll')
$cutoffDate = (Get-Date).AddDays(-$DaysBack)

# Banner
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " HifzDefend Downloads Folder Scanner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verify downloads folder exists
if (-not (Test-Path $downloadsFolder)) {
    Write-Host "[ERROR] Downloads folder not found: $downloadsFolder" -ForegroundColor Red
    exit 1
}

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Folder: $downloadsFolder" -ForegroundColor Gray
Write-Host "  Days back: $DaysBack" -ForegroundColor Gray
Write-Host "  Cutoff date: $($cutoffDate.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor Gray
Write-Host "  Auto-quarantine: $AutoQuarantine" -ForegroundColor Gray
Write-Host ""

# Find suspicious files
Write-Host "Scanning for potentially suspicious files..." -ForegroundColor Yellow

$suspiciousFiles = Get-ChildItem -Path $downloadsFolder -File -Recurse -ErrorAction SilentlyContinue |
                   Where-Object {
                       $_.LastWriteTime -gt $cutoffDate -and
                       $_.Extension -in $suspiciousExtensions
                   } |
                   Sort-Object LastWriteTime -Descending

if ($suspiciousFiles.Count -eq 0) {
    Write-Host "[OK] No suspicious files found in the last $DaysBack days" -ForegroundColor Green
    exit 0
}

Write-Host "Found $($suspiciousFiles.Count) potentially suspicious file(s):`n" -ForegroundColor Yellow

# Display files
$suspiciousFiles | ForEach-Object {
    $ageInDays = [math]::Round((New-TimeSpan -Start $_.LastWriteTime -End (Get-Date)).TotalDays, 1)
    Write-Host "  $($_.Name)" -ForegroundColor Cyan
    Write-Host "    Size: $([math]::Round($_.Length / 1KB, 2)) KB" -ForegroundColor Gray
    Write-Host "    Modified: $($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm')) ($ageInDays days ago)" -ForegroundColor Gray
    Write-Host "    Path: $($_.FullName)" -ForegroundColor DarkGray
    Write-Host ""
}

# Confirm analysis
if (-not $AutoQuarantine) {
    $response = Read-Host "Analyze these files? (y/n)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host "Analysis cancelled by user" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "`nStarting analysis...`n" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Gray

# Analysis results tracking
$results = @{
    Total = $suspiciousFiles.Count
    Analyzed = 0
    Clean = 0
    Suspicious = 0
    Malicious = 0
    Errors = 0
}

$maliciousFiles = @()
$suspiciousFilesList = @()

# Analyze each file
foreach ($file in $suspiciousFiles) {
    Write-Host "Analyzing: $($file.Name)" -ForegroundColor Cyan
    Write-Host "  Path: $($file.FullName)" -ForegroundColor Gray

    try {
        # Analyze with HifzDefend
        $output = hifzdefend analyze-script $file.FullName 2>&1 | Out-String

        $results.Analyzed++

        # Parse output (basic classification)
        if ($output -match "clean|safe|benign" -and $output -notmatch "malicious|suspicious") {
            Write-Host "  Result: CLEAN" -ForegroundColor Green
            $results.Clean++
            if ($ShowCleanFiles) {
                Write-Host $output -ForegroundColor Gray
            }
        }
        elseif ($output -match "suspicious") {
            Write-Host "  Result: SUSPICIOUS" -ForegroundColor Yellow
            $results.Suspicious++
            $suspiciousFilesList += $file
            Write-Host $output -ForegroundColor Yellow
        }
        elseif ($output -match "malicious|malware|trojan|ransomware|cryptominer") {
            Write-Host "  Result: MALICIOUS" -ForegroundColor Red
            $results.Malicious++
            $maliciousFiles += $file
            Write-Host $output -ForegroundColor Red
        }
        else {
            Write-Host "  Result: UNKNOWN (review manually)" -ForegroundColor Magenta
            Write-Host $output -ForegroundColor Gray
        }

    } catch {
        Write-Host "  [ERROR] Analysis failed: $_" -ForegroundColor Red
        $results.Errors++
    }

    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Analysis Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Results Summary:" -ForegroundColor Yellow
Write-Host "  Total files: $($results.Total)" -ForegroundColor White
Write-Host "  Analyzed: $($results.Analyzed)" -ForegroundColor White
Write-Host "  Clean: $($results.Clean)" -ForegroundColor Green
Write-Host "  Suspicious: $($results.Suspicious)" -ForegroundColor Yellow
Write-Host "  Malicious: $($results.Malicious)" -ForegroundColor Red
if ($results.Errors -gt 0) {
    Write-Host "  Errors: $($results.Errors)" -ForegroundColor Red
}
Write-Host ""

# Handle malicious files
if ($maliciousFiles.Count -gt 0) {
    Write-Host "ALERT: $($maliciousFiles.Count) malicious file(s) detected!" -ForegroundColor Red
    Write-Host ""

    foreach ($file in $maliciousFiles) {
        Write-Host "  - $($file.FullName)" -ForegroundColor Red
    }
    Write-Host ""

    if ($AutoQuarantine) {
        Write-Host "Auto-quarantine is enabled. Quarantining malicious files..." -ForegroundColor Yellow

        foreach ($file in $maliciousFiles) {
            try {
                hifzdefend quarantine $file.FullName --threat-name "Detected by downloads scan"
                Write-Host "  [OK] Quarantined: $($file.Name)" -ForegroundColor Green
            } catch {
                Write-Host "  [ERROR] Failed to quarantine $($file.Name): $_" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "Recommended actions:" -ForegroundColor Yellow
        Write-Host "  1. Review the analysis output above" -ForegroundColor White
        Write-Host "  2. Quarantine malicious files:" -ForegroundColor White
        Write-Host '     hifzdefend quarantine "<file>" --threat-name "Malware"' -ForegroundColor Gray
        Write-Host "  3. Or re-run with -AutoQuarantine flag" -ForegroundColor White
    }
    Write-Host ""
}

# Handle suspicious files
if ($suspiciousFilesList.Count -gt 0) {
    Write-Host "WARNING: $($suspiciousFilesList.Count) suspicious file(s) detected" -ForegroundColor Yellow
    Write-Host ""

    foreach ($file in $suspiciousFilesList) {
        Write-Host "  - $($file.FullName)" -ForegroundColor Yellow
    }
    Write-Host ""

    Write-Host "Recommended actions:" -ForegroundColor Yellow
    Write-Host "  1. Review the analysis output above" -ForegroundColor White
    Write-Host "  2. Investigate suspicious files manually" -ForegroundColor White
    Write-Host "  3. Consider quarantining if confirmed malicious" -ForegroundColor White
    Write-Host ""
}

# Clean result
if ($results.Malicious -eq 0 -and $results.Suspicious -eq 0) {
    Write-Host "All analyzed files appear clean!" -ForegroundColor Green
    Write-Host ""
}

# Cost summary
Write-Host "Cost summary:" -ForegroundColor Cyan
try {
    hifzdefend ai cost
} catch {
    Write-Host "Failed to retrieve cost information" -ForegroundColor Red
}

Write-Host ""
Write-Host "Scan complete!" -ForegroundColor Green
Write-Host ""

# Exit with appropriate code
if ($results.Malicious -gt 0) {
    exit 2  # Malicious files found
} elseif ($results.Suspicious -gt 0) {
    exit 1  # Suspicious files found
} else {
    exit 0  # Clean
}
