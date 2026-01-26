# ============================================================================
# HifzDefend - Batch Script Analysis Workflow
# ============================================================================
# Analyzes multiple scripts in a directory or from a file list
#
# Usage: .\batch_analysis.ps1 -Path <directory or file list>
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Path,

    [string]$OutputFile = "batch_analysis_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv",
    [string[]]$Extensions = @('.ps1', '.bat', '.cmd', '.vbs', '.js', '.py'),
    [switch]$Recursive,
    [int]$MaxFiles = 100,
    [switch]$StopOnMalicious
)

# Banner
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " HifzDefend Batch Script Analyzer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verify path exists
if (-not (Test-Path $Path)) {
    Write-Host "[ERROR] Path not found: $Path" -ForegroundColor Red
    exit 1
}

# Determine if path is file or directory
$isFile = (Get-Item $Path) -is [System.IO.FileInfo]

if ($isFile) {
    # Path is a file list
    Write-Host "Reading file list from: $Path" -ForegroundColor Yellow
    try {
        $files = Get-Content $Path | Where-Object { $_ -and (Test-Path $_) } | ForEach-Object { Get-Item $_ }
    } catch {
        Write-Host "[ERROR] Failed to read file list: $_" -ForegroundColor Red
        exit 1
    }
} else {
    # Path is a directory
    Write-Host "Scanning directory: $Path" -ForegroundColor Yellow
    Write-Host "  Recursive: $Recursive" -ForegroundColor Gray
    Write-Host "  Extensions: $($Extensions -join ', ')" -ForegroundColor Gray

    try {
        if ($Recursive) {
            $files = Get-ChildItem -Path $Path -File -Recurse -ErrorAction SilentlyContinue |
                     Where-Object { $_.Extension -in $Extensions }
        } else {
            $files = Get-ChildItem -Path $Path -File -ErrorAction SilentlyContinue |
                     Where-Object { $_.Extension -in $Extensions }
        }
    } catch {
        Write-Host "[ERROR] Failed to scan directory: $_" -ForegroundColor Red
        exit 1
    }
}

if ($files.Count -eq 0) {
    Write-Host "[WARNING] No matching files found" -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($files.Count) file(s) to analyze" -ForegroundColor Green
Write-Host ""

# Limit files if needed
if ($files.Count -gt $MaxFiles) {
    Write-Host "[WARNING] Found more than $MaxFiles files. Analyzing first $MaxFiles only." -ForegroundColor Yellow
    Write-Host "Increase -MaxFiles parameter to analyze more." -ForegroundColor Yellow
    $files = $files | Select-Object -First $MaxFiles
    Write-Host ""
}

# Confirmation
$estimatedCost = $files.Count * 0.01  # Rough estimate
Write-Host "Estimated cost: ~`$$([math]::Round($estimatedCost, 2))" -ForegroundColor Yellow
$response = Read-Host "Continue with analysis? (y/n)"
if ($response -ne 'y' -and $response -ne 'Y') {
    Write-Host "Analysis cancelled by user" -ForegroundColor Yellow
    exit 0
}

Write-Host "`nStarting batch analysis..." -ForegroundColor Cyan
Write-Host "Output file: $OutputFile" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================`n" -ForegroundColor Gray

# Initialize results
$results = @()
$stats = @{
    Total = $files.Count
    Analyzed = 0
    Clean = 0
    Suspicious = 0
    Malicious = 0
    Errors = 0
}

# Progress tracking
$current = 0

# Analyze each file
foreach ($file in $files) {
    $current++
    $percentComplete = [math]::Round(($current / $files.Count) * 100, 1)

    Write-Host "[$current/$($files.Count) - $percentComplete%] $($file.Name)" -ForegroundColor Cyan
    Write-Host "  Path: $($file.FullName)" -ForegroundColor Gray

    $result = [PSCustomObject]@{
        FileName = $file.Name
        FilePath = $file.FullName
        FileSize = $file.Length
        Extension = $file.Extension
        Modified = $file.LastWriteTime
        Classification = "Unknown"
        ThreatLevel = "None"
        ThreatName = ""
        Details = ""
        AnalysisTime = Get-Date
        Error = ""
    }

    try {
        $startTime = Get-Date
        $output = hifzdefend analyze-script $file.FullName 2>&1 | Out-String
        $analysisTime = ((Get-Date) - $startTime).TotalSeconds

        $stats.Analyzed++

        # Parse classification
        if ($output -match "clean|safe|benign" -and $output -notmatch "malicious|suspicious") {
            $result.Classification = "Clean"
            $result.ThreatLevel = "None"
            $stats.Clean++
            Write-Host "  Result: CLEAN" -ForegroundColor Green
        }
        elseif ($output -match "suspicious") {
            $result.Classification = "Suspicious"
            $result.ThreatLevel = "Medium"
            $stats.Suspicious++
            Write-Host "  Result: SUSPICIOUS" -ForegroundColor Yellow

            # Extract threat details if available
            if ($output -match "threat|indicator|pattern") {
                $result.Details = ($output -split "`n" | Select-String -Pattern "threat|indicator|pattern" | Select-Object -First 3) -join "; "
            }
        }
        elseif ($output -match "malicious|malware") {
            $result.Classification = "Malicious"
            $result.ThreatLevel = "High"
            $stats.Malicious++
            Write-Host "  Result: MALICIOUS" -ForegroundColor Red

            # Extract threat name
            if ($output -match "trojan|ransomware|cryptominer|backdoor|worm|virus") {
                $result.ThreatName = ($Matches[0])
            }

            $result.Details = ($output -split "`n" | Select-String -Pattern "malicious|threat" | Select-Object -First 3) -join "; "

            if ($StopOnMalicious) {
                Write-Host "`n[ALERT] Malicious file detected. Stopping analysis (--StopOnMalicious)" -ForegroundColor Red
                $results += $result
                break
            }
        }

        Write-Host "  Analysis time: $([math]::Round($analysisTime, 2))s" -ForegroundColor Gray

    } catch {
        Write-Host "  [ERROR] Analysis failed: $_" -ForegroundColor Red
        $result.Classification = "Error"
        $result.Error = $_.Exception.Message
        $stats.Errors++
    }

    $results += $result
    Write-Host ""
}

# Export results to CSV
Write-Host "`nExporting results to CSV..." -ForegroundColor Yellow
try {
    $results | Export-Csv -Path $OutputFile -NoTypeInformation
    Write-Host "[OK] Results exported to: $OutputFile" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to export results: $_" -ForegroundColor Red
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Batch Analysis Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Statistics:" -ForegroundColor Yellow
Write-Host "  Total files: $($stats.Total)" -ForegroundColor White
Write-Host "  Analyzed: $($stats.Analyzed)" -ForegroundColor White
Write-Host "  Clean: $($stats.Clean)" -ForegroundColor Green
Write-Host "  Suspicious: $($stats.Suspicious)" -ForegroundColor Yellow
Write-Host "  Malicious: $($stats.Malicious)" -ForegroundColor Red
if ($stats.Errors -gt 0) {
    Write-Host "  Errors: $($stats.Errors)" -ForegroundColor Red
}
Write-Host ""

# Threat breakdown
if ($stats.Malicious -gt 0 -or $stats.Suspicious -gt 0) {
    Write-Host "Threat Details:" -ForegroundColor Yellow

    if ($stats.Malicious -gt 0) {
        Write-Host "`n  Malicious Files:" -ForegroundColor Red
        $results | Where-Object { $_.Classification -eq "Malicious" } | ForEach-Object {
            Write-Host "    - $($_.FileName)" -ForegroundColor Red
            if ($_.ThreatName) {
                Write-Host "      Type: $($_.ThreatName)" -ForegroundColor DarkRed
            }
        }
    }

    if ($stats.Suspicious -gt 0) {
        Write-Host "`n  Suspicious Files:" -ForegroundColor Yellow
        $results | Where-Object { $_.Classification -eq "Suspicious" } | ForEach-Object {
            Write-Host "    - $($_.FileName)" -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Cost summary
Write-Host "Cost Summary:" -ForegroundColor Cyan
try {
    hifzdefend ai cost
} catch {
    Write-Host "Failed to retrieve cost information" -ForegroundColor Red
}

Write-Host ""

# Recommendations
if ($stats.Malicious -gt 0) {
    Write-Host "CRITICAL: Malicious files detected!" -ForegroundColor Red
    Write-Host "Recommended actions:" -ForegroundColor Yellow
    Write-Host "  1. Review detailed analysis in: $OutputFile" -ForegroundColor White
    Write-Host "  2. Quarantine all malicious files" -ForegroundColor White
    Write-Host "  3. Investigate how these files arrived" -ForegroundColor White
    Write-Host "  4. Scan other systems for similar threats" -ForegroundColor White
} elseif ($stats.Suspicious -gt 0) {
    Write-Host "WARNING: Suspicious files detected" -ForegroundColor Yellow
    Write-Host "Recommended actions:" -ForegroundColor Yellow
    Write-Host "  1. Review detailed analysis in: $OutputFile" -ForegroundColor White
    Write-Host "  2. Manually inspect suspicious files" -ForegroundColor White
    Write-Host "  3. Consider additional analysis or sandboxing" -ForegroundColor White
} else {
    Write-Host "All analyzed files appear clean!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Analysis complete!" -ForegroundColor Green
Write-Host "Results saved to: $OutputFile" -ForegroundColor Cyan
Write-Host ""

# Exit codes
if ($stats.Malicious -gt 0) {
    exit 2  # Malicious files found
} elseif ($stats.Suspicious -gt 0) {
    exit 1  # Suspicious files found
} else {
    exit 0  # Clean
}
