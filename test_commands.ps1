# Test Commands Script for HifzDefend v0.2.0
# Usage: .\test_commands.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " HifzDefend v0.2.0 Testing" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if API key is set
if (-not $env:CLAUDE_API_KEY) {
    Write-Host "[WARNING] CLAUDE_API_KEY not set" -ForegroundColor Yellow
    Write-Host "Set it with: `$env:CLAUDE_API_KEY = 'sk-ant-...'" -ForegroundColor Yellow
    Write-Host "`nTesting non-AI commands only...`n" -ForegroundColor Yellow
    $skipAI = $true
} else {
    Write-Host "[OK] API key found: $($env:CLAUDE_API_KEY.Substring(0, 12))..." -ForegroundColor Green
    $skipAI = $false
}

# Test results tracking
$script:passCount = 0
$script:failCount = 0
$script:timeoutCount = 0

# Test function
function Test-Command {
    param(
        [string]$Number,
        [string]$Description,
        [string]$Command,
        [int]$Timeout = 10
    )

    Write-Host "`n[Test $Number] $Description" -ForegroundColor Cyan
    Write-Host "Command: $Command" -ForegroundColor Gray

    try {
        $job = Start-Job -ScriptBlock {
            param($cmd)
            try {
                Invoke-Expression $cmd 2>&1
            } catch {
                Write-Error $_
            }
        } -ArgumentList $Command

        $result = Wait-Job $job -Timeout $Timeout

        if ($result) {
            $output = Receive-Job $job
            $hasError = $output | Where-Object { $_ -is [System.Management.Automation.ErrorRecord] }

            if ($hasError) {
                Write-Host "[FAIL]" -ForegroundColor Red
                $output | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
                $script:failCount++
            } else {
                Write-Host "[PASS]" -ForegroundColor Green
                $output | Select-Object -First 10 | ForEach-Object {
                    Write-Host "  $_" -ForegroundColor Gray
                }
                if ($output.Count -gt 10) {
                    Write-Host "  ... ($($output.Count - 10) more lines)" -ForegroundColor DarkGray
                }
                $script:passCount++
            }
        } else {
            Write-Host "[TIMEOUT] Command took > ${Timeout}s" -ForegroundColor Yellow
            Stop-Job $job
            $script:timeoutCount++
        }

        Remove-Job $job -Force
    }
    catch {
        Write-Host "[FAIL] $_" -ForegroundColor Red
        $script:failCount++
    }
}

# === BASIC TESTS ===
Write-Host "`n=== BASIC TESTS (No API Key) ===" -ForegroundColor Magenta

Test-Command "1" "Version check" "hifzdefend --version" -Timeout 5
Test-Command "2" "Help system" "hifzdefend --help" -Timeout 5
Test-Command "3" "AI help" "hifzdefend ai --help" -Timeout 5
Test-Command "15" "Config display" "hifzdefend config-show" -Timeout 10

# === AI TESTS ===
if (-not $skipAI) {
    Write-Host "`n=== AI FEATURES TESTS ===" -ForegroundColor Magenta

    Test-Command "5" "AI connection test" "hifzdefend ai test" -Timeout 30
    Test-Command "6" "Initial statistics" "hifzdefend ai stats" -Timeout 10
    Test-Command "7" "Initial cost breakdown" "hifzdefend ai cost" -Timeout 10

    # Create test file for script analysis
    Write-Host "`nCreating test script file..." -ForegroundColor Gray
    "Write-Host 'Hello, World!'" | Out-File -FilePath "test_safe.ps1" -Encoding UTF8

    Test-Command "8" "Natural language query" "hifzdefend query 'what is hifzdefend?'" -Timeout 30
    Test-Command "9" "Threat explanation" "hifzdefend explain 'trojan'" -Timeout 30
    Test-Command "10" "Script analysis" "hifzdefend analyze-script test_safe.ps1" -Timeout 40

    Test-Command "11" "Stats after usage" "hifzdefend ai stats" -Timeout 10
    Test-Command "12" "Cost breakdown with data" "hifzdefend ai cost" -Timeout 10

    Write-Host "`nNote: Cache reset test requires manual confirmation (not automated)" -ForegroundColor Yellow
} else {
    Write-Host "`n=== AI TESTS SKIPPED (No API Key) ===" -ForegroundColor Yellow
}

# === STATUS TEST (WILL TIMEOUT) ===
Write-Host "`n=== OPTIONAL: ClamAV Status Test ===" -ForegroundColor Magenta
Write-Host "WARNING: This will hang for 30-60 seconds (ClamAV timeout)" -ForegroundColor Yellow
$response = Read-Host "Run status test? (y/n)"
if ($response -eq 'y' -or $response -eq 'Y') {
    Test-Command "4" "Status command (ClamAV check)" "hifzdefend status" -Timeout 70
}

# === SUMMARY ===
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Passed:  $script:passCount" -ForegroundColor Green
Write-Host "  Failed:  $script:failCount" -ForegroundColor Red
Write-Host "  Timeout: $script:timeoutCount" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# === RESULTS FILE ===
$resultsFile = "TEST_RESULTS_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
Write-Host "Test results saved to: $resultsFile" -ForegroundColor Cyan

@"
HifzDefend v0.2.0 Test Results
Generated: $(Get-Date)

Summary:
- Passed:  $script:passCount
- Failed:  $script:failCount
- Timeout: $script:timeoutCount

Test Environment:
- PowerShell Version: $($PSVersionTable.PSVersion)
- API Key Set: $(-not $skipAI)
- Working Directory: $(Get-Location)

Next Steps:
1. Review failures above (if any)
2. Run manual tests for interactive commands
3. Document detailed results in TEST_RESULTS.md
4. Proceed to next development phase

For detailed test log, see console output above.
"@ | Out-File -FilePath $resultsFile -Encoding UTF8

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Review test results above" -ForegroundColor Yellow
Write-Host "  2. Create detailed TEST_RESULTS.md if needed" -ForegroundColor Yellow
Write-Host "  3. Share results for debugging if failures occurred" -ForegroundColor Yellow
Write-Host ""
