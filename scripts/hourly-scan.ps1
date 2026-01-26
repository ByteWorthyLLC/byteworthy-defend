# Hourly System Security Scan
$hifzDefendScript = "C:\Users\richa\Documents\HifzDefend\hifzdefend.ps1"
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
