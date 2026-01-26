# Simple PowerShell test script for HifzDefend analysis
# This is a benign script that demonstrates what Claude can analyze

# Get system information
Write-Host "Getting system information..."
Get-ComputerInfo | Select-Object CsName, OsName, OsVersion

# List running processes
Write-Host "`nTop 5 processes by CPU:"
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 | Format-Table Name, CPU, WorkingSet

# Check Windows Defender status
Write-Host "`nWindows Defender Status:"
Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled

Write-Host "`nScript completed successfully!"
