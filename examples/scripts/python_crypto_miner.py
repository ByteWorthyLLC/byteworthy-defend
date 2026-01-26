#!/usr/bin/env python3
# ============================================================================
# ⚠️ DEMO ONLY - NOT REAL MALWARE ⚠️
# python_crypto_miner.py
# ============================================================================
# Purpose: Demonstrates cryptominer malware patterns for AI analysis testing
# Status: FAKE MALWARE - Non-functional, for demonstration only
# Expected Analysis: Should be classified as MALICIOUS (Cryptominer)
# ============================================================================

"""
FAKE Cryptocurrency Miner Demo

This is a NON-FUNCTIONAL demonstration of what a cryptominer might look like.
It shows the patterns and techniques used by real cryptominers, but doesn't
actually mine cryptocurrency.

**THIS IS NOT REAL MALWARE**
- All mining code is commented out or placeholder
- No actual mining will occur
- Safe to analyze with HifzDefend

FOR EDUCATIONAL/TESTING PURPOSES ONLY
"""

import os
import sys
import time
import hashlib
import random
from datetime import datetime

# ========================
# SUSPICIOUS PATTERN #1: Process name disguise
# ========================

# Real cryptominers disguise themselves as legitimate processes
FAKE_PROCESS_NAMES = [
    "svchost.exe",
    "csrss.exe",
    "System",
    "audiodg.exe",
    "dwm.exe"
]

print("[DEMO] Cryptominer Demo - NOT FUNCTIONAL")
print("[DEMO] Would disguise as:", random.choice(FAKE_PROCESS_NAMES))

# ========================
# SUSPICIOUS PATTERN #2: Mining pool configuration
# ========================

# Configuration for mining pool (all fake/placeholder)
MINING_CONFIG = {
    "pool_url": "pool.minexmr.com:443",  # Fake
    "wallet_address": "4AbCdEf1234567890GhIjKlMnOpQrStUvWxYz...",  # Placeholder
    "algorithm": "RandomX",  # Monero mining algorithm
    "threads": os.cpu_count(),  # Use all CPU cores
    "priority": "low",  # Low priority to avoid detection
}

print("\n[DEMO] Mining Configuration:")
print(f"[DEMO]   Pool: {MINING_CONFIG['pool_url']}")
print(f"[DEMO]   Algorithm: {MINING_CONFIG['algorithm']}")
print(f"[DEMO]   Threads: {MINING_CONFIG['threads']}")
print("[DEMO]   (Not actually configured)")

# ========================
# SUSPICIOUS PATTERN #3: CPU usage monitoring
# ========================

def fake_get_cpu_usage():
    """Fake CPU monitoring to avoid detection"""
    # Real cryptominers throttle when user is active
    print("\n[DEMO] Would monitor CPU usage to avoid detection")
    print("[DEMO]   - Throttle when user active")
    print("[DEMO]   - Full speed when idle")
    print("[DEMO]   (Not actually monitoring)")
    return random.randint(20, 30)  # Fake low usage

# ========================
# SUSPICIOUS PATTERN #4: Persistence mechanism
# ========================

def fake_install_persistence():
    """Fake persistence installation"""
    print("\n[DEMO] Persistence mechanisms:")

    # Windows
    if sys.platform == "win32":
        print("[DEMO]   Would add to:")
        print("[DEMO]     - Registry Run key")
        print("[DEMO]     - Scheduled Task")
        print("[DEMO]     - Startup folder")

    # Linux
    elif sys.platform == "linux":
        print("[DEMO]   Would add to:")
        print("[DEMO]     - ~/.config/autostart/")
        print("[DEMO]     - /etc/systemd/system/")
        print("[DEMO]     - Cron jobs")

    print("[DEMO]   (Not actually installing)")

# ========================
# SUSPICIOUS PATTERN #5: Network communication
# ========================

def fake_connect_mining_pool():
    """Fake mining pool connection"""
    print("\n[DEMO] Mining Pool Connection:")
    print(f"[DEMO]   Connecting to: {MINING_CONFIG['pool_url']}")
    print("[DEMO]   Protocol: Stratum")
    print("[DEMO]   (Not actually connecting)")

    # Simulate connection
    time.sleep(0.5)
    print("[DEMO]   Status: [SIMULATED] Connected")

# ========================
# MALICIOUS PATTERN #1: Mining loop
# ========================

def fake_mining_loop():
    """Fake mining loop (does not actually mine)"""
    print("\n[DEMO] Mining Loop Started:")
    print("[DEMO]   Algorithm: RandomX (Monero)")
    print("[DEMO]   (Not actually mining)")

    # Simulate mining for demo
    for i in range(5):
        # Real malware would:
        # 1. Fetch work from pool
        # 2. Perform cryptographic hashing
        # 3. Submit shares to pool
        # 4. Earn cryptocurrency

        fake_hash = hashlib.sha256(str(time.time()).encode()).hexdigest()

        print(f"[DEMO]   Block {i+1}/5: Hash={fake_hash[:16]}...")
        print(f"[DEMO]   CPU: {fake_get_cpu_usage()}% | Hashrate: [FAKE] 150 H/s")

        time.sleep(1)

    print("[DEMO]   Mining loop complete (simulated only)")

# ========================
# MALICIOUS PATTERN #2: Stealth techniques
# ========================

def fake_stealth_techniques():
    """Fake stealth/evasion techniques"""
    print("\n[DEMO] Stealth Techniques:")

    techniques = [
        "Process name obfuscation",
        "Low CPU priority",
        "Pause when Task Manager opened",
        "Hide from process list",
        "Disable Windows Defender notifications",
        "Encrypt network traffic",
        "Use legitimate-looking certificates",
        "Randomize connection intervals"
    ]

    for technique in techniques:
        print(f"[DEMO]   ✗ {technique}")

    print("[DEMO]   (Not actually applying)")

# ========================
# MALICIOUS PATTERN #3: Anti-analysis
# ========================

def fake_anti_analysis():
    """Fake anti-analysis techniques"""
    print("\n[DEMO] Anti-Analysis Checks:")

    checks = {
        "Virtual Machine": False,  # Would check for VM
        "Debugger": False,         # Would check for debuggers
        "Sandbox": False,          # Would check for sandbox
        "Analysis Tools": False    # Would check for analysis tools
    }

    for check, detected in checks.items():
        status = "[DETECTED]" if detected else "[NOT DETECTED]"
        print(f"[DEMO]   {check}: {status}")

    print("[DEMO]   (Not actually checking)")
    print("[DEMO]   Real malware would exit if any detected")

# ========================
# MALICIOUS PATTERN #4: Resource monitoring
# ========================

def fake_monitor_resources():
    """Fake resource monitoring"""
    print("\n[DEMO] Resource Monitoring:")
    print("[DEMO]   Would monitor:")
    print("[DEMO]     - CPU temperature")
    print("[DEMO]     - Power consumption")
    print("[DEMO]     - Network bandwidth")
    print("[DEMO]     - Memory usage")
    print("[DEMO]   To optimize mining and avoid detection")
    print("[DEMO]   (Not actually monitoring)")

# ========================
# MALICIOUS PATTERN #5: Update mechanism
# ========================

def fake_check_updates():
    """Fake update checker"""
    print("\n[DEMO] Update Mechanism:")
    print("[DEMO]   Would check for updates from:")
    print("[DEMO]     C2 Server: update-server.onion")
    print("[DEMO]   Could download:")
    print("[DEMO]     - New miner versions")
    print("[DEMO]     - Additional payloads")
    print("[DEMO]     - Configuration updates")
    print("[DEMO]   (Not actually checking)")

# ========================
# MAIN EXECUTION
# ========================

def main():
    """Main execution (all fake/demo only)"""
    print("=" * 60)
    print("⚠️  CRYPTOCURRENCY MINER DEMO ⚠️")
    print("=" * 60)
    print("\n**THIS IS NOT REAL MALWARE**")
    print("Demonstration of cryptominer patterns for HifzDefend testing\n")

    # Demonstrate patterns (all simulated)
    fake_anti_analysis()
    fake_install_persistence()
    fake_stealth_techniques()
    fake_connect_mining_pool()
    fake_monitor_resources()
    fake_mining_loop()
    fake_check_updates()

    # Summary
    print("\n" + "=" * 60)
    print("⚠️  DEMO COMPLETE ⚠️")
    print("=" * 60)
    print("\nThis script demonstrated cryptominer patterns:")
    print("  ✗ Process name disguising")
    print("  ✗ Mining pool configuration")
    print("  ✗ CPU usage monitoring")
    print("  ✗ Persistence mechanisms")
    print("  ✗ Network communication")
    print("  ✗ Mining loop simulation")
    print("  ✗ Stealth techniques")
    print("  ✗ Anti-analysis checks")
    print("  ✗ Resource monitoring")
    print("  ✗ Update mechanisms")
    print("\n**CRITICAL**: No actual mining occurred!")
    print("All operations were simulated for demonstration.")
    print("\nUse this to test HifzDefend's cryptominer detection.\n")

# ========================
# HifzDefend Analysis Notes
# ========================
"""
This script should be flagged as MALICIOUS (Cryptominer) because:

1. Mining pool configuration (pool URLs, wallet addresses)
2. Multi-threaded CPU-intensive operations
3. Persistence mechanisms (Registry, Scheduled Tasks, Autostart)
4. Network communication to mining pools (Stratum protocol)
5. Process name obfuscation/disguising
6. CPU usage monitoring to avoid detection
7. Stealth techniques (low priority, pausing, hiding)
8. Anti-analysis/anti-VM checks
9. Resource monitoring
10. C2 communication for updates

Indicators of Compromise (IoCs):
- Connection to known mining pools (*.minexmr.com)
- RandomX algorithm usage (Monero mining)
- High CPU usage over extended periods
- Network connections on port 443 to suspicious domains
- Persistence in startup locations
- Process name matches system processes but behaves differently

Recommended Action: IMMEDIATE QUARANTINE
Risk Level: HIGH
Classification: Cryptocurrency Miner (CoinMiner)
Threat Family: Monero Miner

**REMINDER**: This is a DEMO SCRIPT for testing purposes only.
No actual mining code is executed.
"""

if __name__ == "__main__":
    main()
