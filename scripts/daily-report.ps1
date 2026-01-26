# Daily Security Report Generation
$hifzDefendScript = "C:\Users\richa\Documents\HifzDefend\hifzdefend.ps1"
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
