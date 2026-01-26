# Phase 1.5 Testing Plan

**Version**: 0.1.5
**Date**: 2026-01-25
**Purpose**: Verify all Phase 1.5 features are functional before beta release

---

## Prerequisites

Before testing, ensure:
- [x] ClamAV daemon is running
- [x] Virtual environment is activated
- [x] HifzDefend is installed: `pip install -e .`

```bash
# Verify prerequisites
hifzdefend --version
# Expected: HifzDefend version 0.1.5 (or similar)

hifzdefend status
# Expected: ClamAV daemon: Running
```

---

## Test Suite 1: Core Functionality (Phase 1)

### Test 1.1: Basic Scanning

```bash
# Scan a clean file
hifzdefend scan README.md

# Expected output:
# ✓ Scanned 1 file
# ✓ Threats detected: 0
# ✓ Duration: <1 second
```

### Test 1.2: Configuration System

```bash
# View configuration
hifzdefend config-show

# Expected: Display configuration with default values

# Check specific section
hifzdefend config-show monitoring

# Expected: Show monitoring configuration
```

### Test 1.3: Quarantine Management

```bash
# List quarantine (should be empty initially)
hifzdefend list-quarantine

# Expected: "No quarantined files found" or empty table
```

---

## Test Suite 2: Phase 1.5 - Monitor Management

### Test 2.1: Monitor Status

```bash
# Check monitor status
hifzdefend monitor status

# Expected output:
# Monitor Status
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Monitor           | Status  | Events
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EventBus          | STOPPED | 0
# PackageMonitor    | STOPPED | 0
# ...
```

**✅ PASS if**: Command executes without errors, shows monitor list

**❌ FAIL if**: Command crashes, missing monitors, import errors

### Test 2.2: Start Monitors

```bash
# Start all enabled monitors
hifzdefend monitor start

# Expected output:
# Starting monitors...
# ✓ EventBus started
# ✓ PackageMonitor started
# ✓ RegistryMonitor started
# ...
```

**Wait 5 seconds for monitors to initialize**

```bash
# Check status again
hifzdefend monitor status

# Expected: All enabled monitors show "RUNNING"
```

**✅ PASS if**: Monitors start successfully, status shows RUNNING

**❌ FAIL if**: Monitors fail to start, errors in output

### Test 2.3: Stop Monitors

```bash
# Stop all monitors
hifzdefend monitor stop

# Expected output:
# Stopping monitors...
# ✓ All monitors stopped
```

```bash
# Verify stopped
hifzdefend monitor status

# Expected: All monitors show "STOPPED"
```

**✅ PASS if**: Monitors stop cleanly

**❌ FAIL if**: Monitors hang, errors during shutdown

---

## Test Suite 3: Package Manager Security

### Test 3.1: Check Package (npm)

```bash
# Check a popular package
hifzdefend check-package npm lodash

# Expected output:
# Checking package: lodash (npm)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Package: lodash
# Latest Version: 4.17.21
# Status: ✓ Clean
# Threat Score: 0
# Recommendation: Safe to install
```

**✅ PASS if**: Command returns package information, no errors

**❌ FAIL if**: Command fails, API errors (if no API key, should gracefully degrade)

### Test 3.2: Check Package (pip)

```bash
# Check a popular Python package
hifzdefend check-package pip requests

# Expected output similar to above
```

**✅ PASS if**: Package check works for Python packages

**❌ FAIL if**: Command fails or crashes

### Test 3.3: Simulate Typosquatting Detection

```bash
# Start monitors
hifzdefend monitor start

# In a separate terminal, try to "install" a typosquat
# (Note: Don't actually install, just for testing purposes)
# The monitor should detect if you run: npm install reqeusts

# Check alerts
hifzdefend alerts list

# Expected: Should show alert if typosquat was attempted
```

**✅ PASS if**: Typosquatting detection works

**❌ FAIL if**: No detection, monitor not working

---

## Test Suite 4: Threat Intelligence Integration

### Test 4.1: Test API Connections (Without Keys)

```bash
# Test API connections (should work without keys, with degraded functionality)
hifzdefend test-api-keys

# Expected output:
# Testing API connections...
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AbuseIPDB:   ✗ Not configured (no API key)
# VirusTotal:  ✗ Not configured (no API key)
# Snyk:        ✗ Not configured (no API key)
# Socket.dev:  ✗ Not configured (no API key)
# Talos:       ✓ Connected (no key required)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**✅ PASS if**: Command runs, shows "Not configured" for services without keys

**❌ FAIL if**: Command crashes

### Test 4.2: Configure API Key (Optional - if you have keys)

```bash
# Configure VirusTotal API key (example)
hifzdefend config set threat_intel.api_keys.virustotal "YOUR_KEY_HERE"

# Test connection
hifzdefend test-api virustotal

# Expected:
# VirusTotal: ✓ Connected (500/500 requests remaining)
```

**✅ PASS if**: API key configuration works, connection succeeds

**❌ FAIL if**: Configuration fails or connection errors

---

## Test Suite 5: Custom Rules Engine

### Test 5.1: List Rules

```bash
# List active YARA rules
hifzdefend rules list

# Expected output:
# Active Rules
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# (Empty initially, or default rules if any)
```

**✅ PASS if**: Command executes, shows rule list (empty or populated)

**❌ FAIL if**: Command crashes

### Test 5.2: Create Custom YARA Rule

Create a simple test rule:

```bash
# Create custom rule file
cat > test_rule.yar << 'EOF'
rule Test_Rule
{
    meta:
        description = "Test YARA rule"
        author = "Test"
        threat_score = 50

    strings:
        $test = "TESTSTRING123"

    condition:
        $test
}
EOF

# Add rule
hifzdefend rules add test_rule.yar

# List rules again
hifzdefend rules list

# Expected: Test_Rule should appear in list
```

**✅ PASS if**: Rule is added successfully

**❌ FAIL if**: Rule compilation fails

### Test 5.3: Test Rule Against File

```bash
# Create test file with trigger string
echo "TESTSTRING123" > test_file.txt

# Scan with rules
hifzdefend scan test_file.txt

# Expected: Rule should match and detect the test string
```

**✅ PASS if**: Rule matches and reports detection

**❌ FAIL if**: Rule doesn't match or errors occur

```bash
# Cleanup
rm test_rule.yar test_file.txt
hifzdefend rules remove Test_Rule
```

---

## Test Suite 6: Whitelisting & Blocking

### Test 6.1: Whitelist Application

```bash
# Add Git to whitelist
hifzdefend whitelist add "C:\Program Files\Git\cmd\git.exe"

# List whitelisted apps
hifzdefend whitelist list

# Expected: git.exe should appear in whitelist
```

**✅ PASS if**: Application added to whitelist

**❌ FAIL if**: Command fails

### Test 6.2: Check Whitelisted App

```bash
# Check if app is whitelisted
hifzdefend whitelist check "C:\Program Files\Git\cmd\git.exe"

# Expected:
# ✓ Application is whitelisted
```

**✅ PASS if**: Whitelist check works

**❌ FAIL if**: Check fails

---

## Test Suite 7: Alerts & Events

### Test 7.1: List Recent Alerts

```bash
# View recent alerts
hifzdefend alerts list

# Expected output:
# Recent Alerts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Time      | Monitor  | Severity | Description
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# (Shows recent alerts if any, or "No alerts")
```

**✅ PASS if**: Command works, displays alerts or "No alerts"

**❌ FAIL if**: Command crashes

### Test 7.2: Clear Alerts

```bash
# Clear alert history
hifzdefend alerts clear

# Verify cleared
hifzdefend alerts list

# Expected: No alerts
```

**✅ PASS if**: Alerts cleared successfully

**❌ FAIL if**: Clear operation fails

---

## Test Suite 8: Performance & Resource Usage

### Test 8.1: CPU Usage When Idle

```bash
# Start monitors
hifzdefend monitor start

# Wait 10 seconds
# Open Task Manager (Ctrl+Shift+Esc)
# Find python.exe process running HifzDefend
# Monitor CPU usage for 30 seconds
```

**✅ PASS if**: CPU usage < 5%

**❌ FAIL if**: CPU usage > 5% consistently

### Test 8.2: Memory Usage

```bash
# Check memory usage in Task Manager
# Find python.exe process
```

**✅ PASS if**: Memory usage < 200 MB

**❌ FAIL if**: Memory usage > 200 MB or growing over time (memory leak)

### Test 8.3: Stop Monitors

```bash
# Stop monitors after testing
hifzdefend monitor stop
```

---

## Test Suite 9: Integration Tests (Automated)

### Test 9.1: Run Unit Tests

```bash
# Run all unit tests
python scripts/run_tests.py unit

# Expected: All tests pass
```

**✅ PASS if**: All unit tests pass

**❌ FAIL if**: Any test failures

### Test 9.2: Run Integration Tests

```bash
# Run integration tests
python scripts/run_tests.py integration

# Expected: Integration tests pass
```

**✅ PASS if**: Integration tests pass

**❌ FAIL if**: Integration failures

### Test 9.3: Run Performance Benchmarks

```bash
# Run performance benchmarks
python scripts/run_tests.py benchmarks

# Expected:
# - CPU idle: < 5%
# - CPU active: < 15%
# - Event latency: < 100ms
```

**✅ PASS if**: All benchmarks meet targets

**❌ FAIL if**: Any benchmark fails

### Test 9.4: Run False Positive Tests

```bash
# Run false positive tests
python scripts/run_tests.py false-pos

# Expected: False positive rate < 1%
```

**✅ PASS if**: False positive rate < 1%

**❌ FAIL if**: Rate > 1%

---

## Test Suite 10: Error Handling & Edge Cases

### Test 10.1: Invalid Command

```bash
# Try invalid command
hifzdefend invalid-command

# Expected: Clear error message, not crash
```

**✅ PASS if**: Shows helpful error message

**❌ FAIL if**: Crashes with traceback

### Test 10.2: Monitor Start When Already Running

```bash
# Start monitors
hifzdefend monitor start

# Try starting again
hifzdefend monitor start

# Expected: Message like "Monitors already running" or graceful restart
```

**✅ PASS if**: Handles gracefully

**❌ FAIL if**: Crashes or corrupts state

### Test 10.3: API Timeout (No Internet)

```bash
# Disconnect from internet (or use airplane mode)
hifzdefend test-api-keys

# Expected: Timeout errors handled gracefully, "Connection failed" messages
```

**✅ PASS if**: Graceful error handling

**❌ FAIL if**: Hangs or crashes

---

## Test Results Summary

### Quick Test Run (5 minutes)

Essential tests for basic functionality:

```bash
# 1. Verify installation
hifzdefend --version
hifzdefend status

# 2. Test monitor commands
hifzdefend monitor status
hifzdefend monitor start
sleep 5
hifzdefend monitor status
hifzdefend monitor stop

# 3. Test package check
hifzdefend check-package npm lodash

# 4. Test API keys
hifzdefend test-api-keys

# 5. Test rules
hifzdefend rules list

# 6. Test whitelist
hifzdefend whitelist list

# 7. Test alerts
hifzdefend alerts list

# 8. Run unit tests
python scripts/run_tests.py unit
```

### Full Test Run (30 minutes)

Run all test suites above sequentially.

### Automated Test Run (10 minutes)

```bash
# Run all automated tests
python scripts/run_tests.py all
```

---

## Test Results Template

```
Date: __________
Tester: __________
Environment: Windows __ / Python __.__

Test Suite 1 (Core Functionality):
- Test 1.1: [ ] PASS [ ] FAIL
- Test 1.2: [ ] PASS [ ] FAIL
- Test 1.3: [ ] PASS [ ] FAIL

Test Suite 2 (Monitor Management):
- Test 2.1: [ ] PASS [ ] FAIL
- Test 2.2: [ ] PASS [ ] FAIL
- Test 2.3: [ ] PASS [ ] FAIL

Test Suite 3 (Package Security):
- Test 3.1: [ ] PASS [ ] FAIL
- Test 3.2: [ ] PASS [ ] FAIL
- Test 3.3: [ ] PASS [ ] FAIL

Test Suite 4 (Threat Intelligence):
- Test 4.1: [ ] PASS [ ] FAIL
- Test 4.2: [ ] PASS [ ] FAIL

Test Suite 5 (Custom Rules):
- Test 5.1: [ ] PASS [ ] FAIL
- Test 5.2: [ ] PASS [ ] FAIL
- Test 5.3: [ ] PASS [ ] FAIL

Test Suite 6 (Whitelist/Block):
- Test 6.1: [ ] PASS [ ] FAIL
- Test 6.2: [ ] PASS [ ] FAIL

Test Suite 7 (Alerts):
- Test 7.1: [ ] PASS [ ] FAIL
- Test 7.2: [ ] PASS [ ] FAIL

Test Suite 8 (Performance):
- Test 8.1: [ ] PASS [ ] FAIL (CPU: ___%)
- Test 8.2: [ ] PASS [ ] FAIL (RAM: ___ MB)

Test Suite 9 (Integration):
- Test 9.1: [ ] PASS [ ] FAIL
- Test 9.2: [ ] PASS [ ] FAIL
- Test 9.3: [ ] PASS [ ] FAIL
- Test 9.4: [ ] PASS [ ] FAIL

Test Suite 10 (Error Handling):
- Test 10.1: [ ] PASS [ ] FAIL
- Test 10.2: [ ] PASS [ ] FAIL
- Test 10.3: [ ] PASS [ ] FAIL

Overall Result: [ ] READY FOR RELEASE [ ] NEEDS FIXES

Issues Found:
1. ___________________________
2. ___________________________
3. ___________________________
```

---

## Known Issues / Expected Failures

1. **Monitor Start Without ClamAV**: If ClamAV daemon is not running, monitors will start but some features may be limited. This is expected.

2. **API Tests Without Keys**: All API tests will show "Not configured" without API keys. This is expected and graceful degradation is working correctly.

3. **Docker Tests Without Docker**: If Docker Desktop is not installed, docker monitor will be disabled. This is expected.

4. **Admin-Required Tests**: Registry monitor may require administrator privileges on some systems.

---

## Troubleshooting Failed Tests

### Import Errors

```bash
# Reinstall in editable mode
pip install -e ".[dev]"
```

### Monitor Won't Start

```bash
# Check logs
type "%LOCALAPPDATA%\HifzDefend\logs\monitoring.log"

# Verify configuration
hifzdefend config-show monitoring
```

### Tests Fail

```bash
# Run specific test with verbose output
pytest tests/test_monitoring/test_event_bus.py -vv

# Check test logs
pytest --log-cli-level=DEBUG
```

### Performance Tests Fail

Performance can vary by system. If tests fail:
- Close other applications
- Run on AC power (not battery)
- Adjust thresholds in `pytest.ini` if needed

---

**Next Step**: Run the quick test (5 minutes) to verify basic functionality before beta release!
