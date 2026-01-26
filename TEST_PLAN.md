# HifzDefend v0.2.0 Testing Plan

**Created**: 2026-01-26
**Status**: Ready for Execution

---

## Known Issues Before Testing

### ClamAV Timeout Issue
**Symptom**: Commands that check ClamAV connection may hang for 30-60 seconds
**Affected Commands**: `status`, `scan`, `quarantine`
**Cause**: Default ClamAV timeout is 60 seconds
**Impact**: Annoying but not critical for AI features
**Workaround**: Wait for timeout, or kill process (Ctrl+C)

**AI commands are NOT affected** - they work independently of ClamAV.

---

## Test Categories

### Category 1: Basic CLI (No API Key Needed)
These should work immediately:

```powershell
# Test 1: Version check
hifzdefend --version
# Expected: "HifzDefend, version 0.2.0" or similar

# Test 2: Help system
hifzdefend --help
# Expected: Command list with descriptions

# Test 3: AI help
hifzdefend ai --help
# Expected: AI subcommands list (stats, cost, reset-cache, test)

# Test 4: Status (will timeout on ClamAV)
hifzdefend status
# Expected: Hangs 30-60s, then shows ClamAV: Not running (this is NORMAL)
```

### Category 2: AI Commands (Requires API Key)
Set your API key first:
```powershell
$env:CLAUDE_API_KEY = "sk-ant-api03-your-key-here"
```

#### Test AI Infrastructure

```powershell
# Test 5: Connection test
hifzdefend ai test
# Expected: Shows configuration, test request, "Connection successful!"
# Expected cost: ~$0.0001

# Test 6: Initial stats (before any usage)
hifzdefend ai stats
# Expected: Shows 0 requests, 0 tokens, $0.00 cost

# Test 7: Initial cost breakdown
hifzdefend ai cost
# Expected: Empty table, $0.00 costs
```

#### Test AI Features

```powershell
# Test 8: Natural language query
hifzdefend query "what is hifzdefend?"
# Expected: AI explanation of HifzDefend
# Expected cost: ~$0.001-0.005

# Test 9: Threat explanation
hifzdefend explain "trojan"
# Expected: Detailed explanation of trojan malware
# Expected cost: ~$0.001-0.003

# Test 10: Script analysis (create test file first)
echo "Write-Host 'Hello, World!'" > test_safe.ps1
hifzdefend analyze-script test_safe.ps1
# Expected: Analysis showing script is benign
# Expected cost: ~$0.003-0.010
```

#### Test Cost Monitoring

```powershell
# Test 11: Stats after usage
hifzdefend ai stats
# Expected: Shows 3+ requests, tokens, costs from previous tests
# Should show cache entries if repeated queries

# Test 12: Detailed cost breakdown
hifzdefend ai cost
# Expected: Table with token breakdown, pricing info, cache savings
# Should show non-zero costs

# Test 13: Cache clearing
hifzdefend ai reset-cache
# Expected: Shows cache size, asks for confirmation
# Type 'y' to confirm
# Expected: "Cleared X cache entries"

# Test 14: Stats after cache clear
hifzdefend ai stats
# Expected: Still shows costs (stats persist), but cache entries = 0
```

### Category 3: Configuration Commands

```powershell
# Test 15: Show configuration
hifzdefend config-show
# Expected: Full configuration output in TOML format

# Test 16: Filter config
hifzdefend config-show | Select-String "ai"
# Expected: Only AI-related config lines
```

### Category 4: Other Commands (May require ClamAV)

```powershell
# Test 17: Rules list
hifzdefend rules list
# Expected: Shows available rules (or error if not configured)

# Test 18: Monitor status
hifzdefend monitor status
# Expected: Shows monitoring status (or error if not running)
```

---

## Expected Results Summary

| Test # | Command | Should Work? | Expected Outcome |
|--------|---------|--------------|------------------|
| 1 | `--version` | ✅ Yes | Version 0.2.0 |
| 2 | `--help` | ✅ Yes | Command list |
| 3 | `ai --help` | ✅ Yes | AI commands |
| 4 | `status` | ⚠️ Slow | Timeout, then ClamAV not running |
| 5 | `ai test` | ✅ Yes | Connection successful |
| 6 | `ai stats` | ✅ Yes | Empty stats |
| 7 | `ai cost` | ✅ Yes | Zero costs |
| 8 | `query` | ✅ Yes | AI response |
| 9 | `explain` | ✅ Yes | Threat explanation |
| 10 | `analyze-script` | ✅ Yes | Script analysis |
| 11 | `ai stats` | ✅ Yes | Non-zero stats |
| 12 | `ai cost` | ✅ Yes | Cost breakdown table |
| 13 | `ai reset-cache` | ✅ Yes | Cache cleared |
| 14 | `ai stats` | ✅ Yes | Stats persist, cache=0 |
| 15 | `config-show` | ✅ Yes | Full config |
| 16 | `config-show` filter | ✅ Yes | AI config only |
| 17 | `rules list` | ❓ Maybe | Depends on setup |
| 18 | `monitor status` | ❓ Maybe | Depends on setup |

---

## Automated Testing Script

Save this as `test_commands.ps1` and run it:

```powershell
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
            Invoke-Expression $cmd
        } -ArgumentList $Command

        $result = Wait-Job $job -Timeout $Timeout

        if ($result) {
            $output = Receive-Job $job
            Write-Host "[PASS]" -ForegroundColor Green
            $output | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" }
            if ($output.Count -gt 5) {
                Write-Host "  ... (truncated)" -ForegroundColor Gray
            }
        } else {
            Write-Host "[TIMEOUT] Command took > ${Timeout}s" -ForegroundColor Yellow
            Stop-Job $job
        }

        Remove-Job $job -Force
        return $true
    }
    catch {
        Write-Host "[FAIL] $_" -ForegroundColor Red
        return $false
    }
}

# Basic Tests
Test-Command "1" "Version check" "hifzdefend --version" -Timeout 5
Test-Command "2" "Help system" "hifzdefend --help" -Timeout 5
Test-Command "3" "AI help" "hifzdefend ai --help" -Timeout 5

# AI Tests (if API key available)
if (-not $skipAI) {
    Write-Host "`n--- AI Features Tests ---`n" -ForegroundColor Cyan

    Test-Command "5" "Connection test" "hifzdefend ai test" -Timeout 30
    Test-Command "6" "Initial stats" "hifzdefend ai stats" -Timeout 10
    Test-Command "7" "Cost breakdown" "hifzdefend ai cost" -Timeout 10

    # Create test file
    "Write-Host 'Hello, World!'" | Out-File -FilePath "test_safe.ps1" -Encoding UTF8

    Test-Command "10" "Script analysis" "hifzdefend analyze-script test_safe.ps1" -Timeout 30
    Test-Command "11" "Stats after usage" "hifzdefend ai stats" -Timeout 10
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Testing Complete" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review test results above" -ForegroundColor Yellow
Write-Host "  2. Run manual tests for interactive commands" -ForegroundColor Yellow
Write-Host "  3. Document any failures in TEST_RESULTS.md" -ForegroundColor Yellow
Write-Host ""
```

---

## Manual Testing Checklist

After running automated tests, test these manually:

- [ ] Test 1: Version check works
- [ ] Test 2: Help text displays correctly
- [ ] Test 3: AI help shows all subcommands
- [ ] Test 4: Status command (accept 30-60s timeout)
- [ ] Test 5: AI test succeeds with valid API key
- [ ] Test 6: Empty stats shown correctly
- [ ] Test 7: Empty cost breakdown shown correctly
- [ ] Test 8: Query command works and gives relevant answer
- [ ] Test 9: Explain command gives useful threat info
- [ ] Test 10: Script analysis detects benign script
- [ ] Test 11: Stats show non-zero values after usage
- [ ] Test 12: Cost table displays correctly with data
- [ ] Test 13: Cache reset asks for confirmation
- [ ] Test 14: Stats persist but cache entries reset
- [ ] Test 15: Config display works
- [ ] Test 16: Config filtering works

---

## Known Issues to Document

If you encounter these, they are expected:

1. **ClamAV timeout on `status`**: Normal, ClamAV not installed/running
2. **"AI features not available"**: Install dependencies or check CLAUDE_API_KEY
3. **"ChromaDB not available"**: Optional, only needed for `query` command
4. **Slow first query**: ChromaDB initialization takes 5-10s

---

## What to Report

Create `TEST_RESULTS.md` with:

### Successes
- Which commands worked
- Example outputs
- Performance notes

### Failures
- Which commands failed
- Error messages (copy full error)
- Steps to reproduce

### Observations
- Cost per operation
- Response times
- Cache effectiveness
- Any unexpected behavior

---

## Next Steps After Testing

Based on test results:

1. **All tests pass**: Ready for Task #6 (error message improvements)
2. **AI tests pass, others fail**: Document failures, proceed with AI focus
3. **Critical failures**: Fix bugs before continuing

---

**Good luck with testing!** 🧪

If you need help interpreting results, share the output and I'll help debug.
