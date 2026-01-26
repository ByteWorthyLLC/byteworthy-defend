# Monitor Downloads Folder for New Files (FIXED - No False Positives)
$downloadsPath = Join-Path $env:USERPROFILE "Downloads"
$hifzDefendScript = "C:\Users\richa\Documents\HifzDefend\hifzdefend.ps1"
$logFile = "$env:LOCALAPPDATA\HifzDefend\logs\downloads-monitor.log"
$projectDir = "C:\Users\richa\Documents\HifzDefend"

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
Write-Log "Monitoring: $downloadsPath"

# Check if Downloads folder exists
if (-not (Test-Path $downloadsPath)) {
    Write-Log "ERROR: Downloads folder not found at $downloadsPath"
    exit 1
}

# Get files modified in last hour
$cutoffTime = (Get-Date).AddHours(-1)
$newFiles = Get-ChildItem -Path $downloadsPath -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.LastWriteTime -gt $cutoffTime -and
        $_.FullName -notlike "$projectDir*"  # Exclude HifzDefend project files
    }

if ($newFiles) {
    Write-Log "Found $($newFiles.Count) new files in Downloads folder"

    foreach ($file in $newFiles) {
        Write-Log "Checking: $($file.Name) (Size: $([math]::Round($file.Length/1KB, 2)) KB)"

        # Only analyze executable files, scripts, and archives
        if ($file.Extension -match '\.(exe|msi|ps1|bat|cmd|vbs|js|py|zip|rar|7z)$') {
            Write-Log "  File type requires analysis: $($file.Extension)"

            try {
                # Run analysis and capture output
                Write-Log "  Running AI analysis..."
                $analysisOutput = & powershell.exe -ExecutionPolicy Bypass -File $hifzDefendScript analyze-script $file.FullName 2>&1 | Out-String

                # Parse the output more carefully
                # Look for explicit threat level indicators in the structured output
                $isMalicious = $analysisOutput -match '\[MALICIOUS\]|\bThreat Level:.*MALICIOUS\b|Classification:.*MALICIOUS'
                $isSuspicious = $analysisOutput -match '\[SUSPICIOUS\]|\bThreat Level:.*SUSPICIOUS\b|Classification:.*SUSPICIOUS'

                if ($isMalicious) {
                    Write-Log "  *** MALICIOUS threat detected in $($file.Name)! ***"

                    # Quarantine file
                    Write-Log "  Quarantining file..."
                    $quarantineOutput = & powershell.exe -ExecutionPolicy Bypass -File $hifzDefendScript quarantine $file.FullName --threat-name "Auto-detected-malicious" 2>&1 | Out-String
                    Write-Log "  Quarantine result: $quarantineOutput"

                    # TODO: Send Windows notification (requires BurntToast module)
                }
                elseif ($isSuspicious) {
                    Write-Log "  ** SUSPICIOUS file detected: $($file.Name)"
                    Write-Log "  Review recommended - not auto-quarantined"
                    # Don't auto-quarantine suspicious files to avoid false positives
                }
                else {
                    Write-Log "  File appears benign: $($file.Name)"
                }
            }
            catch {
                Write-Log "  ERROR analyzing $($file.Name): $_"
            }
        }
        else {
            Write-Log "  Skipping: $($file.Name) (safe file type: $($file.Extension))"
        }
    }
}
else {
    Write-Log "No new files in Downloads folder (checked since $cutoffTime)"
}

Write-Log "Monitoring complete"
Write-Log "---"
