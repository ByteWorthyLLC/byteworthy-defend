# HifzDefend Usage Guide

Complete guide to using HifzDefend for malware scanning and quarantine management.

## Table of Contents
- [CLI Commands](#cli-commands)
- [Scanning](#scanning)
- [Quarantine Management](#quarantine-management)
- [Security Monitoring (Phase 1.5)](#security-monitoring-phase-15)
  - [Monitor Management](#monitor-management)
  - [Alert Management](#alert-management)
  - [Custom Rules Management](#custom-rules-management)
  - [Threat Intelligence Checks](#threat-intelligence-checks)
  - [Application Whitelist](#application-whitelist)
- [Status and Maintenance](#status-and-maintenance)
- [Configuration](#configuration)
- [Logs and Reports](#logs-and-reports)
- [Tips and Best Practices](#tips-and-best-practices)

## CLI Commands

### General Syntax
```bash
hifzdefend [OPTIONS] COMMAND [ARGS]...
```

### Available Commands

**Basic Commands:**
- `scan` - Scan files or directories
- `status` - Display system status
- `update` - Update virus definitions
- `quarantine` - Manually quarantine a file
- `list-quarantine` - List quarantined files
- `config-show` - Display current configuration

**Monitoring Commands (Phase 1.5):**
- `monitor` - Manage security monitors
  - `monitor start` - Start all enabled monitors
  - `monitor stop` - Stop all monitors
  - `monitor status` - Display monitor status
  - `monitor enable <name>` - Enable specific monitor
  - `monitor disable <name>` - Disable specific monitor

**Alert Commands:**
- `alerts` - Manage security alerts
  - `alerts list` - List recent security alerts
  - `alerts clear` - Clear alert history

**Rules Commands:**
- `rules` - Manage custom detection rules
  - `rules list` - List active detection rules
  - `rules add <file>` - Add custom YARA rule
  - `rules remove <name>` - Remove custom rule

**Threat Intelligence Commands:**
- `threat-intel` - Check threat intelligence
  - `threat-intel check ip <address>` - Check IP reputation
  - `threat-intel check file <hash>` - Check file hash reputation
  - `threat-intel check package <name>` - Check package security

**Whitelist Commands:**
- `whitelist` - Manage application whitelist
  - `whitelist add <path>` - Add application to whitelist
  - `whitelist remove <path>` - Remove application from whitelist

### Global Options
- `--version` - Show version and exit
- `--help` - Show help message and exit

## Scanning

### Scan a Single File
```bash
hifzdefend scan path/to/file.exe
```

**Example Output:**
```
HifzDefend Scanner
Scanning: path/to/file.exe

Scan Results:
Files scanned: 1
Duration: 0.23 seconds

✓ No threats detected
```

### Scan a Directory
```bash
# Scan Downloads folder
hifzdefend scan C:\Users\YourName\Downloads

# Scan with relative path
hifzdefend scan ./src
```

**Example Output:**
```
HifzDefend Scanner
Scanning: C:\Users\YourName\Downloads

Scanning... ━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

Scan Results:
Files scanned: 156
Duration: 12.34 seconds

✓ No threats detected
```

### Scan with Report Saving
```bash
# Save report even if no threats found
hifzdefend scan --save-report path/to/scan
```

Reports are automatically saved when threats are detected.

### What Gets Scanned

HifzDefend scans based on configuration rules:

**Included:**
- All files under specified path
- Recursively scans subdirectories (if enabled)
- Compressed archives (if enabled)

**Excluded:**
- Files exceeding `max_file_size` (default: 100 MB)
- Files in `excluded_paths`
- Files with `excluded_extensions`
- System directories (by default)

## Quarantine Management

### Automatic Quarantine

When a threat is detected and `auto_quarantine` is enabled:
```bash
hifzdefend scan suspicious_file.exe
```

**Output:**
```
Scan Results:
Files scanned: 1
Duration: 0.45 seconds

⚠ Threats found: 1

┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ File                    ┃ Threat         ┃ Quarantined ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ suspicious_file.exe     │ Trojan.Generic │ Yes         │
└─────────────────────────┴────────────────┴─────────────┘

Report saved: C:\Users\...\reports\scan_report_20260125_143022.json
```

The infected file is moved to quarantine and the original is removed.

### Manual Quarantine
```bash
hifzdefend quarantine path/to/file.exe --threat-name "Suspicious.Behavior"
```

**Output:**
```
Quarantine File
File: path/to/file.exe
Threat: Suspicious.Behavior

✓ File quarantined successfully
Quarantine ID: a3f8b2e1-9d4c-4a7b-8e5f-1c2d3e4f5a6b
Hash: 5d41402abc4b2a76b9719d911017c592
```

### List Quarantined Files
```bash
hifzdefend list-quarantine
```

**Output:**
```
Quarantined Files

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Quarantine ID                      ┃ File                ┃ Size    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ a3f8b2e1-9d4c-4a7b-8e5f-1c2d3e...  │ *.quarantined       │ 25.3 KB │
│ b7e9c3f2-4d8a-4b2c-9f6e-2d3f4a...  │ *.quarantined       │ 12.7 KB │
└────────────────────────────────────┴─────────────────────┴─────────┘

Total: 2 files
```

### Quarantine Directory

Default location: `%LOCALAPPDATA%\HifzDefend\quarantine`

Quarantined files:
- Have `.quarantined` extension
- Are read-only (chmod 0444)
- Cannot be executed
- Named with UUID for safety

## Security Monitoring (Phase 1.5)

### Monitor Management

#### Start All Monitors
```bash
hifzdefend monitor start
```

**Output:**
```
Starting Security Monitors

✓ All monitors started

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
┃ Monitor            ┃ Status   ┃ Events ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
│ package_monitor    │ Running  │ 0      │
│ docker_monitor     │ Running  │ 0      │
│ registry_monitor   │ Running  │ 0      │
└────────────────────┴──────────┴────────┘

Note: Monitors running in background. Use 'hifzdefend monitor stop' to stop.
```

#### Stop All Monitors
```bash
hifzdefend monitor stop
```

**Output:**
```
Stopping Security Monitors

✓ All monitors stopped
```

#### Check Monitor Status
```bash
hifzdefend monitor status
```

**Output:**
```
Monitor Status

Event Bus:
  Status: Running
  Events processed: 42
  Queue size: 0

┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Monitor              ┃ Status   ┃ Enabled ┃ Events ┃ Last Check       ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ package_monitor      │ Running  │ Yes     │ 5      │ 2026-01-25 14:30 │
│ docker_monitor       │ Running  │ Yes     │ 2      │ 2026-01-25 14:29 │
│ registry_monitor     │ Running  │ Yes     │ 0      │ 2026-01-25 14:28 │
│ powershell_monitor   │ Stopped  │ No      │ 0      │ Never            │
└──────────────────────┴──────────┴─────────┴────────┴──────────────────┘
```

#### Enable/Disable Monitors
```bash
# Enable a monitor
hifzdefend monitor enable package_monitor

# Disable a monitor
hifzdefend monitor disable powershell_monitor
```

**Note:** Currently requires manual configuration file editing. Future versions will support runtime configuration.

### Alert Management

#### List Recent Alerts
```bash
# List all recent alerts
hifzdefend alerts list

# Limit number of alerts
hifzdefend alerts list --limit 10

# Filter by severity
hifzdefend alerts list --severity critical
```

**Output:**
```
Security Alerts

2026-01-25 14:30:45 WARNING package_monitor: Potentially malicious package installed: evil-package@1.0.0
2026-01-25 14:25:12 CRITICAL ransomware_monitor: Mass file encryption detected in C:\Users\YourName\Documents
2026-01-25 14:20:33 INFO docker_monitor: Container started: nginx:latest
```

**Note:** Alerts are currently logged to `hifzdefend.log`. Future versions will have dedicated alert storage.

#### Clear Alert History
```bash
hifzdefend alerts clear
```

### Custom Rules Management

#### List Active Rules
```bash
hifzdefend rules list
```

**Output:**
```
Active Detection Rules

YARA Rules:
  Custom signatures path: C:\Users\...\HifzDefend\signatures\custom

File Blocking Rules:
  Status: Enabled
  Blocked extensions: .scr, .pif, .bat
  Context-aware: True

Application Whitelist:
  Mode: Blacklist
  Whitelisted apps: 3
```

#### Add Custom YARA Rule
```bash
hifzdefend rules add path/to/custom_rule.yar
```

**Example YARA Rule:**
```yara
rule SuspiciousPowerShell {
    meta:
        description = "Detects obfuscated PowerShell"
        author = "Your Name"
        date = "2026-01-25"

    strings:
        $s1 = "IEX" ascii
        $s2 = "DownloadString" ascii
        $s3 = "New-Object Net.WebClient" ascii

    condition:
        2 of ($s*)
}
```

**Output:**
```
Adding Custom Rule
Rule file: path/to/custom_rule.yar

✓ Rule added: custom_rule.yar

Note: Restart monitors for changes to take effect
```

#### Remove Custom Rule
```bash
hifzdefend rules remove custom_rule.yar
```

**Output:**
```
Removing Custom Rule
Rule: custom_rule.yar

✓ Rule removed: custom_rule.yar

Note: Restart monitors for changes to take effect
```

### Threat Intelligence Checks

#### Check IP Reputation
```bash
hifzdefend threat-intel check ip 1.2.3.4
```

**Output:**
```
Threat Intelligence Check
Type: ip
Value: 1.2.3.4

Results:
Source: abuseipdb
Threat Level: CRITICAL
Threat Score: 90/100

Details:
  is_whitelisted: False
  is_tor: False
  total_reports: 150
  country_code: XX
  isp: Unknown ISP
```

#### Check File Hash Reputation
```bash
hifzdefend threat-intel check file a1b2c3d4e5f6...
```

**Output:**
```
Threat Intelligence Check
Type: file
Value: a1b2c3d4e5f6...

Results:
Source: virustotal
Threat Level: MALICIOUS
Threat Score: 75/100

Details:
  malicious: 45
  suspicious: 5
  undetected: 20
  total_engines: 70
```

#### Check Package Security
```bash
# Check npm package
hifzdefend threat-intel check package lodash@4.17.0

# Check PyPI package
hifzdefend threat-intel check package requests==2.28.0
```

**Output:**
```
Threat Intelligence Check
Type: package
Value: lodash@4.17.0

Results:
Source: snyk
Threat Level: MALICIOUS
Threat Score: 60/100

Details:
  vulnerability_count: 2
  severity_counts: {'high': 1, 'medium': 1}
```

### Application Whitelist

#### Add Application to Whitelist
```bash
hifzdefend whitelist add "C:\Program Files\TrustedApp\app.exe"
```

**Output:**
```
Adding to Whitelist
Application: C:\Program Files\TrustedApp\app.exe

Note: Configuration persistence not yet implemented
To whitelist, add to your configuration file:
  [rules.app_whitelist]
  whitelisted_apps = [
    "C:\Program Files\TrustedApp\app.exe",
  ]
```

#### Remove Application from Whitelist
```bash
hifzdefend whitelist remove "C:\Program Files\TrustedApp\app.exe"
```

## Status and Maintenance

### Check System Status
```bash
hifzdefend status
```

**Output:**
```
HifzDefend Status

✓ ClamAV daemon: Running
Version: ClamAV 0.103.8/26823/Fri Jan 24 08:12:15 2026

Configuration:
  Log directory: C:\Users\...\AppData\Local\HifzDefend\logs
  Report directory: C:\Users\...\AppData\Local\HifzDefend\reports
  Quarantine: Enabled
  Quarantine directory: C:\Users\...\AppData\Local\HifzDefend\quarantine
```

### Update Virus Definitions
```bash
hifzdefend update
```

**Output:**
```
Updating Virus Definitions

✓ Virus definitions updated successfully
ClamAV update process started at Fri Jan 24 14:30:45 2026
```

**Note**: This runs `freshclam` which must be in your PATH.

### View Configuration
```bash
hifzdefend config-show
```

**Output:**
```json
{
  "clamav": {
    "host": "localhost",
    "port": 3310,
    "timeout": 60
  },
  "scanning": {
    "max_file_size": 104857600,
    "scan_archives": true,
    ...
  },
  ...
}
```

## Configuration

### Configuration File Location

Default: `%LOCALAPPDATA%\HifzDefend\hifzdefend.toml`

Windows example: `C:\Users\YourName\AppData\Local\HifzDefend\hifzdefend.toml`

### Creating Custom Configuration

1. Copy example configuration:
   ```bash
   copy config\hifzdefend.toml.example %LOCALAPPDATA%\HifzDefend\hifzdefend.toml
   ```

2. Edit the file in your favorite text editor

3. Changes take effect immediately (no restart needed)

### Configuration Options

#### ClamAV Settings
```toml
[clamav]
host = "localhost"      # ClamAV daemon host
port = 3310            # ClamAV daemon port
timeout = 60           # Connection timeout (seconds)
```

#### Scanning Settings
```toml
[scanning]
max_file_size = 104857600  # Maximum file size (100 MB)
scan_archives = true       # Scan ZIP, RAR, etc.
scan_recursively = true    # Scan subdirectories
follow_symlinks = false    # Follow symbolic links

excluded_paths = [
    "C:\\Windows\\System32",
    "C:\\MyProject\\.venv",
]

excluded_extensions = [".log", ".tmp"]
```

#### Logging Settings
```toml
[logging]
level = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
log_dir = "%LOCALAPPDATA%\\HifzDefend\\logs"
max_log_size = 10485760  # 10 MB
backup_count = 5
format = "json"  # json or text
```

#### Quarantine Settings
```toml
[quarantine]
enabled = true
quarantine_dir = "%LOCALAPPDATA%\\HifzDefend\\quarantine"
auto_quarantine = true  # Automatically quarantine threats
```

#### Reporting Settings
```toml
[reporting]
report_dir = "%LOCALAPPDATA%\\HifzDefend\\reports"
save_clean_scans = false  # Save reports for clean scans
report_format = "json"    # json, html, text
```

### Environment Variables

You can override configuration file location:
```bash
set HIFZDEFEND_CONFIG=C:\custom\path\config.toml
hifzdefend status
```

## Logs and Reports

### Log Files

Location: `%LOCALAPPDATA%\HifzDefend\logs`

**Main Log**: `hifzdefend.log`
- All application events
- JSON formatted
- Rotates at 10 MB
- Keeps 5 backups

**Audit Log**: `audit.log`
- Security events only
- Threat detections
- Quarantine actions
- Rotates at 50 MB
- Keeps 20 backups

**Example Log Entry:**
```json
{
  "timestamp": "2026-01-24 14:30:45",
  "level": "WARNING",
  "logger": "hifzdefend.core.scanner",
  "module": "scanner",
  "function": "scan_file",
  "line": 145,
  "message": "Threat detected in suspicious.exe: Trojan.Generic",
  "file_path": "C:\\Downloads\\suspicious.exe",
  "threat_name": "Trojan.Generic",
  "file_hash": "5d41402abc4b2a76b9719d911017c592",
  "action": "threat_detected"
}
```

### Scan Reports

Location: `%LOCALAPPDATA%\HifzDefend\reports`

**Filename Format**: `scan_report_YYYYMMDD_HHMMSS_<scan_id>.json`

**Example Report:**
```json
{
  "scan_id": "a3f8b2e1",
  "start_time": "2026-01-24T14:30:45.123456",
  "end_time": "2026-01-24T14:30:57.654321",
  "duration_seconds": 12.53,
  "files_scanned": 156,
  "total_size_bytes": 45678901,
  "threats_found": 1,
  "threats": [
    {
      "file_path": "C:\\Downloads\\suspicious.exe",
      "threat_name": "Trojan.Generic",
      "file_hash": "5d41402abc4b2a76b9719d911017c592",
      "quarantined": true,
      "detected_at": "2026-01-24T14:30:46.789012"
    }
  ],
  "errors": [],
  "scanned_files": ["..."]
}
```

## Tips and Best Practices

### Regular Scanning

1. **Scan Downloads folder regularly:**
   ```bash
   hifzdefend scan %USERPROFILE%\Downloads
   ```

2. **Scan USB drives before use:**
   ```bash
   hifzdefend scan D:\
   ```

3. **Scan after installing new software:**
   ```bash
   hifzdefend scan "C:\Program Files\NewApp"
   ```

### Update Virus Definitions

Update definitions at least daily:
```bash
hifzdefend update
```

Consider creating a scheduled task for automatic updates.

### Monitor Logs

Regularly check logs for suspicious activity:
```bash
# View recent threats
findstr "threat_detected" %LOCALAPPDATA%\HifzDefend\logs\audit.log
```

### Configuration Tips

1. **Exclude trusted directories** to speed up scans:
   ```toml
   excluded_paths = [
       "C:\\Windows\\System32",
       "C:\\TrustedApp",
   ]
   ```

2. **Adjust file size limit** for specific needs:
   ```toml
   max_file_size = 524288000  # 500 MB for video files
   ```

3. **Enable detailed logging** for troubleshooting:
   ```toml
   level = "DEBUG"
   ```

### False Positives

If a clean file is flagged:

1. Verify it's actually clean (check file source, hash)
2. Temporarily disable auto-quarantine
3. Report false positive to ClamAV team
4. Add to exclusions if trusted:
   ```toml
   excluded_paths = ["C:\\TrustedApp\\falseflag.dll"]
   ```

### Performance

For faster scans:
- Exclude large directories you trust
- Disable archive scanning if not needed
- Increase max_file_size threshold
- Scan during off-hours

## Troubleshooting

### Scan Taking Too Long

**Solutions:**
- Add exclusions for large, trusted directories
- Reduce `max_file_size` to skip very large files
- Disable `scan_archives` if not needed

### False Positives

**Solutions:**
- Update virus definitions (may be fixed)
- Check file hash on VirusTotal
- Add to exclusions if trusted

### Quarantine Full

**Solutions:**
- Review and delete old quarantine entries
- Increase quarantine directory disk space
- Manually remove old `.quarantined` files

### ClamAV Connection Errors

**Solutions:**
- Ensure clamd.exe is running
- Check `hifzdefend status`
- Restart ClamAV daemon
- Verify port 3310 is not blocked

## Next Steps

- Review [SECURITY.md](SECURITY.md) for security best practices
- Check [DEVELOPMENT.md](DEVELOPMENT.md) if contributing
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
