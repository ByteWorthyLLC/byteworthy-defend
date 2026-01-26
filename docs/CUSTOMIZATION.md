# HifzDefend Customization Guide

Complete guide to customizing HifzDefend with custom rules, signatures, whitelists, and advanced configurations.

## Table of Contents

- [Overview](#overview)
- [YARA Custom Signatures](#yara-custom-signatures)
- [File Type Blocking](#file-type-blocking)
- [Application Whitelisting](#application-whitelisting)
- [Custom Threat Intelligence](#custom-threat-intelligence)
- [Advanced Configuration](#advanced-configuration)
- [Rule Sharing & Import](#rule-sharing--import)

---

## Overview

HifzDefend provides extensive customization capabilities:

1. **YARA Rules** - Write custom malware signatures
2. **File Blocking** - Block specific file types or patterns
3. **Application Whitelisting** - Trust specific applications
4. **Custom Blocklists** - Block domains, IPs, file hashes
5. **Configuration Tuning** - Adjust detection thresholds
6. **Response Actions** - Define automated responses

---

## YARA Custom Signatures

### What is YARA?

YARA is a pattern-matching tool designed for malware identification. HifzDefend uses YARA to define **custom threat signatures** beyond ClamAV's database.

### YARA Rules Directory

```
C:\Users\richa\AppData\Local\HifzDefend\signatures\
├── custom\           # Your custom rules
│   ├── malware.yar
│   ├── ransomware.yar
│   └── cryptominer.yar
├── community\        # Imported community rules
│   └── (community rules)
└── islamic_content\  # Integrity checks for Islamic content
    └── integrity_checks.yar
```

### Writing Your First YARA Rule

#### Example 1: Detect Suspicious PowerShell

**File**: `signatures/custom/powershell_malware.yar`

```yara
rule Suspicious_PowerShell_Download
{
    meta:
        description = "Detects PowerShell downloading and executing scripts"
        author = "Your Name"
        date = "2026-01-25"
        severity = "high"
        threat_score = 85

    strings:
        $download1 = "DownloadString" nocase
        $download2 = "DownloadFile" nocase
        $download3 = "Net.WebClient" nocase
        $exec1 = "Invoke-Expression" nocase
        $exec2 = "IEX" nocase
        $obfuscation = "-enc" nocase

    condition:
        any of ($download*) and any of ($exec*) or $obfuscation
}
```

#### Example 2: Detect Keylogger

**File**: `signatures/custom/keylogger.yar`

```yara
rule Generic_Keylogger
{
    meta:
        description = "Detects common keylogger patterns"
        author = "HifzDefend Community"
        threat_score = 95
        severity = "critical"

    strings:
        // Windows API calls for keyboard hooks
        $api1 = "SetWindowsHookExA" nocase
        $api2 = "SetWindowsHookExW" nocase
        $api3 = "GetAsyncKeyState" nocase
        $api4 = "GetKeyState" nocase

        // Common keylogger strings
        $log1 = "[ENTER]" nocase
        $log2 = "[SHIFT]" nocase
        $log3 = "[CTRL]" nocase
        $log4 = "keylog" nocase

        // File operations
        $file1 = "CreateFileA" nocase
        $file2 = "WriteFile" nocase

    condition:
        2 of ($api*) and 2 of ($log*) and any of ($file*)
}
```

#### Example 3: Detect Crypto-Miner

**File**: `signatures/custom/cryptominer.yar`

```yara
rule XMRig_CryptoMiner
{
    meta:
        description = "Detects XMRig cryptocurrency miner"
        author = "HifzDefend"
        threat_score = 90
        severity = "critical"

    strings:
        // XMRig-specific strings
        $xmrig1 = "xmrig" nocase
        $xmrig2 = "randomx" nocase
        $xmrig3 = "donate-level" nocase

        // Mining pool connections
        $pool1 = "stratum+tcp://" nocase
        $pool2 = "pool.minexmr.com" nocase
        $pool3 = "supportxmr.com" nocase

        // Monero wallet address pattern
        $wallet = /4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}/

    condition:
        any of ($xmrig*) or any of ($pool*) or $wallet
}
```

### Adding Custom Rules

**Method 1: CLI Command**

```bash
# Add single rule file
hifzdefend rules add "C:\Path\To\malware.yar"

# Add directory of rules
hifzdefend rules add "C:\Path\To\signatures\"
```

**Method 2: Manual Copy**

```bash
# Copy to custom signatures directory
copy malware.yar "%LOCALAPPDATA%\HifzDefend\signatures\custom\"

# Reload rules
hifzdefend rules reload
```

**Method 3: Configuration File**

```toml
# config/hifzdefend.toml
[rules]
custom_signatures_path = "C:\\Users\\richa\\AppData\\Local\\HifzDefend\\signatures\\custom"
yara_rules_enabled = true
auto_reload_on_change = true
```

### Managing YARA Rules

```bash
# List all active rules
hifzdefend rules list

# Example output:
# Rule Name                    | Source      | Severity | Enabled
# -------------------------------------------------------------------------
# Suspicious_PowerShell_Download | custom      | high     | ✓
# Generic_Keylogger             | custom      | critical | ✓
# XMRig_CryptoMiner             | custom      | critical | ✓
# WannaCry_Ransomware           | community   | critical | ✓

# Disable specific rule
hifzdefend rules disable "Generic_Keylogger"

# Enable rule
hifzdefend rules enable "Generic_Keylogger"

# Remove rule
hifzdefend rules remove "XMRig_CryptoMiner"

# Test rule against file
hifzdefend rules test "malware.yar" "C:\Path\To\suspicious.exe"
```

### YARA Rule Best Practices

1. **Use Descriptive Metadata**:
   ```yara
   meta:
       description = "Clear description of what this detects"
       author = "Your Name"
       date = "2026-01-25"
       threat_score = 85  # 0-100
       severity = "high"  # info, warning, high, critical
   ```

2. **Test Rules Thoroughly**:
   ```bash
   # Test against known malware samples (EICAR)
   hifzdefend rules test "myRule.yar" "eicar.txt"

   # Test against clean files
   hifzdefend rules test "myRule.yar" "C:\Windows\System32\notepad.exe"
   ```

3. **Avoid Overly Broad Patterns**:
   ```yara
   # BAD: Too generic
   strings:
       $s1 = "http://"

   # GOOD: More specific
   strings:
       $download = "http://" nocase
       $exec = "cmd.exe /c" nocase
   condition:
       $download and $exec
   ```

4. **Use Context in Conditions**:
   ```yara
   condition:
       // Require multiple indicators, not just one
       2 of ($api*) and any of ($suspicious*)
   ```

---

## File Type Blocking

### Context-Aware File Blocking

HifzDefend can block file types based on **location** - allowing executables in `Program Files` but blocking them in `Downloads`.

### Configuration

```toml
[rules.file_blocking]
enabled = true
blocked_extensions = [".scr", ".pif", ".bat", ".cmd", ".vbs", ".js"]
context_aware = true

# Location-based rules
[rules.file_blocking.locations]
# Block executables in Downloads
"C:\\Users\\*\\Downloads" = [".exe", ".dll", ".scr", ".pif"]

# Block scripts in Temp
"C:\\Users\\*\\AppData\\Local\\Temp" = [".bat", ".cmd", ".vbs", ".ps1"]

# Allow everything in Program Files
"C:\\Program Files" = []
"C:\\Program Files (x86)" = []
```

### Blocking Rules Examples

#### Block All Unsigned Executables

```toml
[rules.file_blocking]
block_unsigned_executables = true
require_microsoft_signature = false  # If true, only allow Microsoft-signed

# Exceptions for unsigned apps you trust
unsigned_whitelist = [
    "C:\\MyApp\\myapp.exe",
]
```

#### Block Files by Hash

```toml
[rules.file_blocking.hash_blocklist]
sha256 = [
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # Example hash
]
```

#### Block Files by Pattern

```toml
[rules.file_blocking.name_patterns]
blocked_patterns = [
    ".*crack.*\\.exe",     # Matches: keygen_crack.exe
    ".*keygen.*",          # Matches: keygen.exe
    ".*hack.*",            # Matches: hack_tool.bat
]
```

### Managing File Blocking

```bash
# Block file type globally
hifzdefend rules block-extension .scr

# Block file type in specific location
hifzdefend rules block-extension .exe --location "C:\Users\richa\Downloads"

# Unblock file type
hifzdefend rules unblock-extension .exe

# List blocked extensions
hifzdefend rules list-blocked

# Example output:
# Extension | Context              | Blocked
# ----------------------------------------------
# .scr      | Global               | ✓
# .pif      | Global               | ✓
# .exe      | C:\Users\*\Downloads | ✓
```

---

## Application Whitelisting

### Whitelist Modes

**Blacklist Mode (Default)**: Allow everything except known threats
**Whitelist Mode**: Block everything except explicitly allowed apps

### Configuration

```toml
[rules.app_whitelist]
enabled = true
whitelist_mode = false  # false = blacklist, true = whitelist

# Allowed applications
whitelisted_apps = [
    "C:\\Program Files\\Git\\cmd\\git.exe",
    "C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe",
    "C:\\Users\\richa\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
]

# Whitelist by publisher (code signing certificate)
whitelisted_publishers = [
    "Microsoft Corporation",
    "Docker Inc",
]

# Verification methods
verify_signatures = true
check_file_hash = true
allow_unsigned_in_program_files = true
```

### Hash-Based Whitelisting

```toml
[rules.app_whitelist.hashes]
# SHA256 hashes of trusted executables
sha256 = [
    "abc123...",  # Git
    "def456...",  # Docker
]
```

### Managing Whitelist

```bash
# Add application to whitelist
hifzdefend whitelist add "C:\Path\To\App.exe"

# Add by publisher
hifzdefend whitelist add-publisher "Microsoft Corporation"

# Remove from whitelist
hifzdefend whitelist remove "C:\Path\To\App.exe"

# List whitelisted apps
hifzdefend whitelist list

# Example output:
# Application                              | Publisher              | Hash Verified
# -------------------------------------------------------------------------------------
# C:\Program Files\Git\cmd\git.exe        | GitHub, Inc.           | ✓
# C:\Program Files\Docker\Docker\...       | Docker Inc             | ✓

# Check if app is whitelisted
hifzdefend whitelist check "C:\Path\To\App.exe"
```

### Automatic Whitelisting

```toml
[rules.app_whitelist.auto]
# Automatically whitelist apps from these locations
auto_whitelist_paths = [
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\Windows\\System32",
]

# Require signatures for auto-whitelist
require_signatures = true
```

---

## Custom Threat Intelligence

### IP Blocklist

```toml
[threat_intel.custom_blocklist]
enabled = true

# Block specific IPs
blocked_ips = [
    "1.2.3.4",
    "5.6.7.8",
]

# Block IP ranges (CIDR)
blocked_cidr = [
    "192.168.1.0/24",
    "10.0.0.0/8",
]
```

```bash
# Add IP to blocklist
hifzdefend blocklist add-ip 1.2.3.4

# Add IP range
hifzdefend blocklist add-cidr 192.168.1.0/24

# Remove from blocklist
hifzdefend blocklist remove-ip 1.2.3.4

# List blocked IPs
hifzdefend blocklist list
```

### Domain Blocklist

```toml
[threat_intel.custom_blocklist]
# Block specific domains
blocked_domains = [
    "evil-malware-site.com",
    "phishing-scam.org",
]

# Block domain patterns
blocked_domain_patterns = [
    ".*\\.ru$",        # Block all .ru domains (example)
    ".*-crack\\..*",   # Block domains with "crack" in subdomain
]
```

```bash
# Add domain to blocklist
hifzdefend blocklist add-domain "evil-site.com"

# Remove domain
hifzdefend blocklist remove-domain "evil-site.com"

# Check if domain is blocked
hifzdefend blocklist check-domain "suspicious.com"
```

### File Hash Blocklist

```toml
[threat_intel.custom_blocklist]
# Block files by SHA256 hash
blocked_hashes = [
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
]
```

```bash
# Add file hash to blocklist
hifzdefend blocklist add-hash "abc123..."

# Block file directly (calculates hash)
hifzdefend blocklist add-file "C:\Path\To\malware.exe"

# Check if hash is blocked
hifzdefend blocklist check-hash "abc123..."
```

---

## Advanced Configuration

### Automated Response Actions

```toml
[rules.automated_responses]
enabled = true

# Auto-quarantine on critical threats
auto_quarantine_critical = true
auto_quarantine_high = false

# Auto-terminate processes
auto_kill_process_critical = true
auto_kill_process_high = false

# Auto-backup on ransomware detection
auto_backup_on_ransomware = true

# Auto-block network connections
auto_block_malicious_ips = true

# Notifications
desktop_notification_critical = true
desktop_notification_high = true
desktop_notification_warning = false
email_notification_critical = true  # Requires email config
```

### Custom Detection Thresholds

```toml
# Package manager sensitivity
[monitoring.package_manager]
typosquat_threshold = 3  # Levenshtein distance (lower = more sensitive)
unknown_package_score = 30  # Base score for unknown packages

# Ransomware sensitivity
[monitoring.ransomware]
file_modification_threshold = 50  # Files per 10 seconds
shadow_copy_deletion_score = 100  # Always critical

# Crypto-miner sensitivity
[monitoring.cryptominer]
cpu_threshold = 80  # % sustained CPU
gpu_threshold = 70  # % sustained GPU
network_pool_score = 90  # Score for mining pool connection

# Registry monitor sensitivity
[monitoring.registry]
new_startup_entry_score = 80
new_service_score = 70
firewall_change_score = 60
```

### Notification Configuration

```toml
[notifications]
enabled = true

# Desktop notifications (Windows Action Center)
desktop_alerts = true
desktop_alert_duration = 10  # seconds

# Email notifications
email_alerts = true
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_username = "your-email@gmail.com"
smtp_password = "your-app-password"
email_recipients = ["admin@example.com"]

# Slack notifications
slack_webhook = ""

# Alert levels
alert_on_info = false
alert_on_warning = true
alert_on_high = true
alert_on_critical = true
```

### Performance Tuning

```toml
[monitoring]
# Check interval (seconds) - higher = less resource usage
check_interval = 60

# Event queue size
max_events_per_minute = 100

# Worker threads
event_bus_workers = 4

# Enable/disable monitors to reduce overhead
[monitoring.package_manager]
enabled = true

[monitoring.docker]
enabled = false  # Disable if you don't use Docker

[monitoring.ide]
enabled = true

# Adjust monitoring scope
[monitoring.ransomware]
monitored_directories = [
    "C:\\Users\\richa\\Documents",  # Only monitor important dirs
]
```

---

## Rule Sharing & Import

### Importing Community Rules

```bash
# Import from GitHub
hifzdefend rules import https://github.com/Yara-Rules/rules/archive/master.zip

# Import from local file
hifzdefend rules import "C:\Downloads\community_rules.zip"

# Import specific rule
hifzdefend rules import "https://raw.githubusercontent.com/user/repo/rule.yar"
```

### Exporting Your Rules

```bash
# Export all custom rules
hifzdefend rules export "C:\Backup\my_rules.zip"

# Export specific rule
hifzdefend rules export "Suspicious_PowerShell_Download" "C:\Backup\ps_rule.yar"

# Export configuration
hifzdefend config export "C:\Backup\my_config.toml"
```

### Sharing Rules

**Share via GitHub**:

1. Create repository: `hifzdefend-custom-rules`
2. Add your `.yar` files
3. Share URL for others to import:
   ```bash
   hifzdefend rules import https://github.com/username/hifzdefend-custom-rules/archive/main.zip
   ```

**Share via File**:

```bash
# Package your rules
hifzdefend rules package "my_rules.zip"

# Include metadata
hifzdefend rules package "my_rules.zip" --include-metadata --author "Your Name"
```

### Rule Repositories

**Official Community Rules**:
- `https://github.com/HifzDefend/community-rules` (example)
- `https://github.com/Yara-Rules/rules`

**Islamic Content Integrity**:
- `https://github.com/HifzDefend/islamic-integrity-rules` (example)

---

## Examples & Templates

### Template: Custom Malware Family Detection

```yara
rule MyMalwareFamily_Variant1
{
    meta:
        description = "Detects MyMalwareFamily variant 1"
        author = "Your Name"
        date = "2026-01-25"
        threat_score = 95
        severity = "critical"
        family = "MyMalwareFamily"
        reference = "https://malware-analysis.com/report-123"

    strings:
        // String indicators
        $s1 = "unique_string_1" nocase
        $s2 = "unique_string_2" wide

        // Hex patterns
        $hex1 = { 6A 40 68 00 30 00 00 }

        // Regular expressions
        $regex1 = /https?:\/\/[a-z0-9]+\.malware\.com/ nocase

    condition:
        uint16(0) == 0x5A4D and  // PE file (MZ header)
        filesize < 5MB and
        2 of ($s*) and
        ($hex1 or $regex1)
}
```

### Template: Context-Aware File Blocking

```toml
[rules.file_blocking.custom_contexts]
# Block executables in user writeable directories
[[rules.file_blocking.custom_contexts.rules]]
location_pattern = "C:\\Users\\*\\AppData\\Local\\Temp\\*"
blocked_extensions = [".exe", ".dll", ".scr", ".bat", ".cmd"]
severity = "high"
message = "Executable in Temp directory blocked"

# Block scripts in Downloads
[[rules.file_blocking.custom_contexts.rules]]
location_pattern = "C:\\Users\\*\\Downloads\\*"
blocked_extensions = [".vbs", ".js", ".ps1", ".bat"]
severity = "high"
message = "Script in Downloads directory blocked"

# Allow digitally signed files everywhere
[[rules.file_blocking.custom_contexts.rules]]
require_signature = true
allow_unsigned = false
exceptions = ["C:\\MyCompany\\"]
```

### Template: Custom Notification Action

```toml
[rules.automated_responses.custom_actions]
# Auto-backup Documents on high-severity threats
[[rules.automated_responses.custom_actions]]
trigger = "severity:high"
action = "backup"
target = "C:\\Users\\richa\\Documents"
destination = "D:\\Backups\\HifzDefend\\Documents"
message = "Auto-backup triggered due to high-severity threat"

# Auto-block process and alert
[[rules.automated_responses.custom_actions]]
trigger = "threat_score:>=90"
actions = ["kill_process", "quarantine", "notify_email"]
message = "Critical threat detected - process terminated and quarantined"
```

---

## Troubleshooting Customizations

### YARA Rule Not Working

```bash
# Verify rule syntax
hifzdefend rules validate "myRule.yar"

# Test rule against sample
hifzdefend rules test "myRule.yar" "sample.exe"

# Check if rule is loaded
hifzdefend rules list | findstr "MyRuleName"

# View rule compilation errors
type "%LOCALAPPDATA%\HifzDefend\logs\rules_engine.log"
```

### Whitelist Not Being Applied

```bash
# Check whitelist status
hifzdefend whitelist list

# Verify file signature
hifzdefend whitelist verify "C:\Path\To\App.exe"

# Check configuration
hifzdefend config show rules.app_whitelist
```

### Blocklist Not Blocking

```bash
# Verify IP is in blocklist
hifzdefend blocklist check-ip 1.2.3.4

# Check if network monitor is enabled
hifzdefend monitor status | findstr "network"

# Test connection blocking
hifzdefend test block-connection 1.2.3.4:443
```

---

## Best Practices

1. **Start Simple**: Begin with default configurations, customize as needed
2. **Test Rules**: Always test YARA rules against known samples before deploying
3. **Use Whitelists**: Whitelist your development tools to reduce false positives
4. **Regular Updates**: Update custom rules weekly, threat intelligence daily
5. **Backup Configurations**: Export your custom rules and configs regularly
6. **Document Changes**: Add comments to YARA rules explaining detection logic
7. **Community Sharing**: Share useful rules with the HifzDefend community

---

**Last Updated**: 2026-01-25
**Version**: Phase 1.5
