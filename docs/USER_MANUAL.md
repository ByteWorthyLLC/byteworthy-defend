# HifzDefend User Manual

**Version 0.3.0** | **Updated: January 2026**

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard](#dashboard)
3. [Scanner](#scanner)
4. [Quarantine](#quarantine)
5. [Real-Time Protection](#real-time-protection)
6. [AI Assistant](#ai-assistant)
7. [License Management](#license-management)
8. [Settings](#settings)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## Getting Started

### First Launch

When you first open HifzDefend:

1. **Welcome Screen** appears with setup wizard
2. **License Activation** (if you have a key)
3. **Update Virus Definitions** automatically
4. **Initial Scan** recommended

### System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Storage**: 500 MB for application + space for quarantine
- **Internet**: Required for updates and AI features

---

## Dashboard

The Dashboard shows your system's security status at a glance.

### Status Overview

**Protection Badge**
- 🟢 **Protected**: All systems active
- 🟡 **Paused**: Protection temporarily disabled
- 🔴 **Disabled**: Protection turned off
- ⚫ **Error**: Service issue

### Statistics

- **Total Scans**: Lifetime scan count
- **Threats Found**: All detected threats
- **Files Quarantined**: Currently isolated files
- **System Status**: ClamAV engine status

### Threat Timeline

Line chart showing threats detected over the last 7 days.

### Recent Scans

List of last 5 scans with:
- Scan path
- Timestamp
- Status (completed, failed)
- Threats found

---

## Scanner

### Quick Scan

Scans critical system areas:

1. Click **Scanner** in sidebar
2. Select **Quick Scan**
3. Wait for completion
4. Review results

**Scans**: Downloads, Desktop, System folders

### Full Scan

Comprehensive system scan:

1. Select **Full Scan**
2. Choose drives (C:, D:, etc.)
3. Estimated time: 1-4 hours
4. Run during off-hours recommended

### Custom Scan

Scan specific files or folders:

1. Click **Custom Scan**
2. Enter path or browse
3. Click **Start Scan**

**Examples**:
- `C:\Users\YourName\Downloads`
- `D:\Projects`
- `C:\Users\YourName\Documents\file.exe`

### Scan Results

After scan completes:
- ✅ **Clean**: No threats
- ⚠️ **Threats Found**: See quarantine
- ❌ **Failed**: Check logs

**Threat Details**:
- File path
- Threat name (e.g., "Win.Trojan.Generic")
- Action taken (quarantined/deleted)

---

## Quarantine

Isolated files are stored safely here.

### View Quarantined Files

**Table Columns**:
- **File Name**: Original filename
- **Original Path**: Where it was found
- **Threat Name**: Malware type
- **Date**: When quarantined
- **Size**: File size

### Restore File

⚠️ **Warning**: Only restore if you're certain it's safe!

1. Select file
2. Click **Restore** (↻ icon)
3. Confirm action
4. File returns to original location

### Delete Permanently

Removes file from quarantine:

1. Select file
2. Click **Delete** (🗑️ icon)
3. Confirm (cannot be undone)

### Auto-Quarantine

When enabled (Settings → Quarantine):
- Threats automatically isolated
- Original file removed
- Notification displayed

---

## Real-Time Protection

Monitors your system continuously.

### What It Protects

- **File Downloads**: Scans as they download
- **File Execution**: Checks before running
- **USB Drives**: Scans when inserted
- **Network Activity**: Monitors suspicious connections
- **Registry Changes**: Detects malicious modifications

### Monitor Types

#### Ransomware Monitor
Detects file encryption patterns:
- Mass file modifications
- Suspicious extensions (.encrypted, .locked)
- Backup deletion attempts

#### Crypto Miner Monitor
Identifies mining malware:
- High CPU/GPU usage
- Known mining pools
- Coinminer signatures

#### PowerShell Monitor
Watches script execution:
- Encoded commands
- Download-execute patterns
- Privilege escalation

#### Network Monitor
Tracks connections:
- Command & Control servers
- Known malicious IPs
- Data exfiltration

### Enable/Disable

**Enable Protection**:
1. Dashboard → Protection Status
2. Click **Enable**
3. Badge turns green

**Disable (Temporary)**:
1. Protection Status → **Pause**
2. Select duration (15m, 1h, until restart)
3. Requires confirmation

⚠️ **Never disable permanently** unless troubleshooting!

---

## AI Assistant

Powered by Claude AI for advanced threat analysis.

### Ask Questions

Natural language security queries:

**Examples**:
- "What threats were found today?"
- "Is this file safe to run?"
- "Explain the last quarantined threat"
- "How do I protect against ransomware?"

### Analyze Suspicious Files

1. Go to **AI Assistant**
2. Enter file path
3. Click **Analyze**
4. Get detailed report

**Report Includes**:
- Behavior analysis
- Code inspection
- Risk assessment
- Recommendations

### AI Cost

- **Trial**: 50 analyses
- **Personal**: Unlimited basic
- **Professional**: Unlimited advanced
- **Cached Responses**: Free

View usage: **AI Stats** button

---

## License Management

### Activate License

1. **License** page
2. Enter license key: `XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`
3. Click **Activate**
4. Features unlock immediately

### License Types

| Feature | Trial | Personal | Professional | Enterprise |
|---------|-------|----------|--------------|------------|
| Duration | 14 days | Annual | Annual | Custom |
| Devices | 1 | 1 | 3 | 10+ |
| Scans/Day | 50 | Unlimited | Unlimited | Unlimited |
| AI Analysis | ✓ | ✓ | ✓ | ✓ |
| Real-Time | Basic | Full | Full | Full |
| Cloud Backup | ✗ | ✓ | ✓ | ✓ |
| Priority Support | ✗ | Email | 24/7 | Dedicated |

### Renew License

**Before Expiration**:
- Notification 7 days prior
- Click **Renew** button
- Complete purchase

**After Expiration**:
- Features downgrade to trial
- Scans limited to 50/day
- Reactivate anytime

### Deactivate

Removes license from this device:

1. **License** page
2. **Deactivate License**
3. Confirm action
4. Can reactivate on different device

---

## Settings

### Scanning Settings

**Max File Size**
- Default: 100 MB (104857600 bytes)
- Larger files skipped
- Increase if needed

**Scan Archives**
- ZIP, RAR, 7Z files
- Enable: Slower but thorough
- Disable: Faster scans

**Excluded Paths**
Add paths to skip:
```
C:\Windows\System32
C:\Program Files\TrustedApp
```

One path per line.

### Quarantine Settings

**Enable Quarantine**
- ✓ Recommended
- Isolates threats safely
- Allows restoration

**Auto-Quarantine**
- Automatic isolation
- No user confirmation
- Faster protection

### ClamAV Connection

**Read-only** (configured during install):
- Host: localhost
- Port: 3310
- Timeout: 60s

Contact support if issues.

### Updates

**Auto-Check**: Daily
**Auto-Download**: Yes (recommended)
**Auto-Install**: No (user chooses)

**Check Now**: Manual update check

### Privacy

**Analytics**
- ✓ Help improve HifzDefend
- Anonymous usage data
- No personal information
- Opt-out anytime

**Crash Reports**
- Diagnostic information
- Error logs only
- Helps fix bugs

---

## Troubleshooting

### Protection Won't Enable

**Symptoms**: Badge stays red/gray

**Solutions**:
1. Check ClamAV service:
   ```cmd
   sc query clamd
   ```
2. Restart service:
   ```cmd
   sc start clamd
   ```
3. Reinstall ClamAV
4. Contact support

### Scans Fail

**Symptoms**: "Scan failed" error

**Solutions**:
1. Check file permissions
2. Verify path exists
3. Exclude from Windows Defender
4. Update virus definitions
5. Check logs: `%LOCALAPPDATA%\HifzDefend\logs`

### AI Features Don't Work

**Symptoms**: "AI analysis failed"

**Solutions**:
1. Check internet connection
2. Verify license includes AI
3. Check API rate limits
4. Restart application
5. Contact support

### High CPU Usage

**Symptoms**: System slowdown during scan

**Solutions**:
- Schedule scans during idle time
- Enable "Low Priority" mode (Settings)
- Exclude large folders
- Close other applications
- Upgrade to SSD

### False Positives

**Symptoms**: Safe files quarantined

**Solutions**:
1. Restore file from quarantine
2. Add to exclusions (Settings)
3. Report to HifzDefend team
4. Update virus definitions

---

## FAQ

### General

**Q: Is HifzDefend free?**
A: 14-day trial, then paid licenses available.

**Q: Does it replace Windows Defender?**
A: Can work alongside or replace it. Exclusions recommended.

**Q: How often should I scan?**
A: Weekly full scans + real-time protection.

**Q: Is my data private?**
A: Yes. Optional anonymous analytics only.

### Licensing

**Q: Can I use one license on multiple PCs?**
A: Personal: 1 device, Professional: 3 devices.

**Q: What happens after trial expires?**
A: Features limited. Purchase license to continue.

**Q: Do I need internet for license?**
A: Only for activation. Works offline after.

### Technical

**Q: Which antivirus engine does it use?**
A: ClamAV (open-source, trusted).

**Q: How does AI analysis work?**
A: Claude AI analyzes file behavior and code.

**Q: Can I run it on Windows 7?**
A: No. Windows 10/11 required.

**Q: Does it scan network drives?**
A: Yes, specify UNC path (\\\\server\\share).

### Troubleshooting

**Q: Scan is very slow**
A: Large files/archives slow scans. Exclude if safe.

**Q: Real-time protection uses too much RAM**
A: Adjust monitor settings or disable some.

**Q: It conflicts with my antivirus**
A: Add mutual exclusions or use only one.

---

## Getting Help

### Support Channels

**Email**: support@hifzdefend.com
- Response time: 24-48 hours (Personal), 4-24 hours (Professional)

**Documentation**: https://docs.hifzdefend.com

**Community Forum**: https://community.hifzdefend.com

**GitHub**: https://github.com/byteworthy/Hafz-Defend/issues

### Before Contacting Support

1. Check this manual
2. Search FAQ
3. Review logs
4. Note error messages
5. List steps to reproduce

### Include in Support Request

- HifzDefend version (Help → About)
- Windows version
- License type
- Error message/screenshot
- Steps to reproduce
- Log files (if applicable)

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Dashboard | Ctrl+1 |
| Scanner | Ctrl+2 |
| Quarantine | Ctrl+3 |
| Settings | Ctrl+, |
| Help | F1 |
| Refresh | F5 |

---

## Glossary

**ClamAV**: Open-source antivirus engine
**Quarantine**: Isolated storage for threats
**Real-Time Protection**: Continuous monitoring
**Signature**: Virus pattern definition
**False Positive**: Safe file detected as threat
**Threat**: Malware, virus, or suspicious file
**YARA**: Pattern matching language

---

**© 2026 ByteWorthy. All Rights Reserved.**

*HifzDefend - Preserving Your Digital Safety*
