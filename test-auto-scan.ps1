# Quick Test - Automatic Downloads Scanning
# This shows how automatic protection works

$downloadsPath = [Environment]::GetFolderPath("Downloads")
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "HifzDefend Automatic Protection - TEST" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Scanning Downloads folder: $downloadsPath" -ForegroundColor White
Write-Host ""

# Get recent files (last 24 hours)
$cutoff = (Get-Date).AddHours(-24)
$recentFiles = Get-ChildItem -Path $downloadsPath -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -gt $cutoff -and $_.Extension -match '\.(exe|ps1|bat|cmd|py|zip)$' } |
    Select-Object -First 5

if ($recentFiles) {
    Write-Host "Found $($recentFiles.Count) recent files to scan:" -ForegroundColor Yellow
    Write-Host ""

    foreach ($file in $recentFiles) {
        Write-Host "  [SCAN] $($file.Name)" -ForegroundColor Cyan
        Write-Host "         Size: $([math]::Round($file.Length/1KB, 2)) KB" -ForegroundColor Gray
        Write-Host "         Modified: $($file.LastWriteTime)" -ForegroundColor Gray

        # In automatic mode, this would run:
        # .\hifzdefend.ps1 analyze-script $file.FullName

        Write-Host "         Status: Would be analyzed automatically" -ForegroundColor Green
        Write-Host ""
    }

    Write-Host "===================================" -ForegroundColor Cyan
    Write-Host "This is how automatic protection works!" -ForegroundColor Cyan
    Write-Host "===================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "With automatic protection enabled:" -ForegroundColor White
    Write-Host "  1. Every 10 minutes, HifzDefend checks Downloads" -ForegroundColor Gray
    Write-Host "  2. New files are automatically analyzed" -ForegroundColor Gray
    Write-Host "  3. Threats are quarantined automatically" -ForegroundColor Gray
    Write-Host "  4. You get notified of any issues" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To enable automatic protection, run:" -ForegroundColor Yellow
    Write-Host "  .\setup-automatic-protection.ps1" -ForegroundColor White
    Write-Host "  (Requires Administrator)" -ForegroundColor Gray
}
else {
    Write-Host "No recent files found in Downloads folder" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Automatic protection would monitor this folder" -ForegroundColor Yellow
    Write-Host "and analyze any new files automatically." -ForegroundColor Yellow
}

Write-Host ""
