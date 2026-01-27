# HifzDefend FAQ (Frequently Asked Questions)

## Table of Contents
- [General Questions](#general-questions)
- [Licensing & Pricing](#licensing--pricing)
- [Installation & Setup](#installation--setup)
- [Features & Functionality](#features--functionality)
- [Technical Questions](#technical-questions)
- [Troubleshooting](#troubleshooting)
- [Privacy & Security](#privacy--security)
- [Comparison](#comparison)

---

## General Questions

### What is HifzDefend?
HifzDefend is a professional Windows antivirus solution built on ClamAV with AI-powered malware analysis, real-time protection, and behavioral monitoring.

### What does "Hifz" mean?
"حفظ" (Hifz) is Arabic for "protection" or "preservation," reflecting our mission to preserve your digital safety.

### Is HifzDefend free?
HifzDefend offers a 14-day free trial with limited features. After that, paid licenses start at $49/year.

### Do I need to uninstall my current antivirus?
Not necessarily. HifzDefend can run alongside Windows Defender with proper exclusions. However, running multiple real-time protection services may impact performance.

### What's the difference between HifzDefend and other antivirus software?
- **AI-Powered**: Claude AI for advanced threat analysis
- **Open Core**: Built on trusted open-source ClamAV
- **Privacy-First**: No data collection without consent
- **Developer-Friendly**: Protects against supply chain attacks, malicious packages
- **Transparent**: Open development, community-driven

---

## Licensing & Pricing

### What license types are available?

| License | Price | Devices | Duration |
|---------|-------|---------|----------|
| Trial | Free | 1 | 14 days |
| Personal | $49/year | 1 | Annual |
| Professional | $99/year | 3 | Annual |
| Enterprise | Custom | 10+ | Custom |

### Can I upgrade my license?
Yes! Upgrade anytime from your account dashboard. You'll only pay the prorated difference.

### Do licenses auto-renew?
Yes, annual licenses auto-renew. You can disable this in account settings.

### What happens when my license expires?
Your protection continues with trial limitations (50 scans/day, no AI features) until renewed.

### Can I get a refund?
Yes, 30-day money-back guarantee. No questions asked.

### Do you offer discounts?
- **Students**: 50% off Personal license
- **Nonprofits**: Custom pricing
- **Annual prepay**: Save 20% vs monthly
- **Volume licensing**: Contact sales

### Can I transfer my license to a new computer?
Yes! Deactivate on the old device, then activate on the new one.

---

## Installation & Setup

### What are the system requirements?
- **OS**: Windows 10 or 11 (64-bit)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Storage**: 500 MB + quarantine space
- **Internet**: For updates and AI features

### Do I need ClamAV installed separately?
No, the HifzDefend installer includes ClamAV automatically.

### How do I install HifzDefend?
1. Download installer from https://hifzdefend.com/download
2. Run `HifzDefend-0.3.0-Setup.exe`
3. Follow installation wizard
4. Enter license key (or start trial)
5. Run initial scan

### Can I install on multiple computers?
Yes, depending on your license (Personal: 1, Professional: 3, Enterprise: 10+).

### Does installation require administrator rights?
Yes, for installing services and setting up real-time protection.

### How do I uninstall?
Settings → Apps → HifzDefend → Uninstall
Or run: `C:\Program Files\HifzDefend\Uninstall.exe`

---

## Features & Functionality

### What scanning options are available?
- **Quick Scan**: Critical areas (~5-10 min)
- **Full Scan**: Entire system (~1-4 hours)
- **Custom Scan**: Specific files/folders
- **Scheduled Scans**: Automatic daily/weekly

### How does real-time protection work?
Monitors in real-time:
- File downloads
- File execution
- USB drives
- Network activity
- Registry changes
- PowerShell scripts

### What is AI-powered analysis?
Claude AI analyzes suspicious files by examining:
- Code structure
- Behavior patterns
- Known malware signatures
- Anomaly detection

### How accurate is threat detection?
- **Signature-based**: 99.9% for known malware
- **AI-based**: 95% for zero-day threats
- **Behavioral**: 90% for new variants
- **False positive rate**: <0.1%

### What types of threats does it detect?
- Viruses and worms
- Trojans and backdoors
- Ransomware
- Spyware and adware
- Crypto miners
- Rootkits
- Phishing attempts
- Malicious scripts
- Supply chain attacks

### Can it remove existing infections?
Yes! Run a full scan to detect and quarantine threats. Most threats are automatically removed.

### What's the difference between quarantine and delete?
- **Quarantine**: Isolates the file safely; can be restored
- **Delete**: Permanently removes the file; cannot be recovered

### Does it protect against ransomware?
Yes, with multiple layers:
- Signature detection
- Behavioral monitoring
- File encryption pattern detection
- Automatic backups (cloud backup on paid plans)

### Can it scan network drives?
Yes, specify UNC paths: `\\server\share\folder`

### Does it work offline?
Yes for scans. Internet required for:
- Virus definition updates
- AI analysis
- License activation (one-time)

---

## Technical Questions

### Which antivirus engine does HifzDefend use?
ClamAV - a trusted open-source antivirus engine used by millions.

### How often are virus definitions updated?
Multiple times daily. Auto-update can be configured (default: every 24 hours).

### What programming languages is it built with?
- **Backend**: Python 3.10+
- **Frontend**: TypeScript/React
- **Engine**: ClamAV (C)

### Can I integrate it with my own software?
Yes! REST API available for Professional and Enterprise licenses. Documentation: https://docs.hifzdefend.com/api

### Does it support command-line usage?
Yes:
```cmd
hifzdefend scan C:\path\to\scan
hifzdefend status
hifzdefend update
```

### Can I customize scan settings?
Yes, via Settings:
- Max file size
- Archive scanning
- Excluded paths
- Scan priority

### Does it log scan results?
Yes, detailed JSON logs at:
`%LOCALAPPDATA%\HifzDefend\logs`

### Can I export scan reports?
Yes, from Scanner → Scan History → Export (CSV, PDF, JSON)

---

## Troubleshooting

### Why is my scan slow?
- Large files/archives slow scans
- Disable archive scanning for speed
- Schedule during idle time
- Exclude safe folders

### Why does it say "ClamAV not running"?
1. Check service: `sc query clamd`
2. Start service: `sc start clamd`
3. Reinstall if needed

### I'm getting false positives. What should I do?
1. Restore file from quarantine
2. Add to exclusions (Settings → Excluded Paths)
3. Report to us: support@hifzdefend.com
4. Update virus definitions

### Real-time protection won't enable
1. Check Windows Defender conflicts
2. Verify admin permissions
3. Restart HifzDefend service
4. Check logs for errors

### AI analysis returns "Failed"
1. Check internet connection
2. Verify license includes AI
3. Check API status: https://status.hifzdefend.com
4. Contact support

### License activation fails
1. Check license key is correct
2. Verify internet connection
3. Check device is not already activated
4. Contact support: support@hifzdefend.com

---

## Privacy & Security

### What data does HifzDefend collect?
**With Analytics Enabled** (opt-in):
- Anonymous usage statistics
- Crash reports (diagnostic data only)
- Performance metrics

**Never Collected**:
- Personal information
- File contents
- Browsing history
- Passwords or credentials

### Is my data sent to the cloud?
Only if enabled:
- **Cloud Backup**: Quarantined files (encrypted)
- **AI Analysis**: File hashes and metadata (not content)
- **Analytics**: Anonymous usage data

All data encrypted in transit (TLS 1.3).

### Can I use HifzDefend completely offline?
Yes, after initial license activation. Disable:
- Auto-updates
- AI analysis
- Cloud backup
- Analytics

### Is the source code open?
Partially:
- **Core scanner**: Open source (GitHub)
- **AI integration**: Proprietary
- **Web dashboard**: Open source

### How is quarantine encrypted?
AES-256 encryption with hardware-backed keys (TPM when available).

### Do you share data with third parties?
No. Never. Your data is yours.

### Where are servers located?
- Primary: United States (AWS us-east-1)
- Backup: Europe (AWS eu-west-1)
- Data residency options available for Enterprise

---

## Comparison

### HifzDefend vs Windows Defender?
| Feature | HifzDefend | Windows Defender |
|---------|------------|------------------|
| Virus Engine | ClamAV | Microsoft |
| AI Analysis | ✓ Claude AI | ✗ |
| Behavioral Monitoring | ✓ Advanced | ✓ Basic |
| Cloud Backup | ✓ | ✗ |
| API Access | ✓ | ✗ |
| Open Source | Partial | ✗ |
| Cost | Paid | Free |

### HifzDefend vs Norton/McAfee?
- **Lighter**: Lower resource usage
- **Privacy**: No forced telemetry
- **Transparent**: Open development
- **Modern**: AI-powered analysis
- **Price**: More affordable

### HifzDefend vs Malwarebytes?
- **Real-time**: Continuous protection (not just on-demand)
- **AI**: Advanced threat analysis
- **Integrated**: One solution vs. multiple tools
- **Open**: ClamAV engine vs. proprietary

---

## Additional Questions

### Can HifzDefend run as a Windows Service?
Yes, automatically installed as a service for real-time protection.

### Does it support multiple user accounts?
Yes, protection applies system-wide to all users.

### Can I white list specific applications?
Yes, Settings → Excluded Paths. Add application folder.

### Does it protect web browsers?
Indirectly:
- Scans downloads automatically
- Blocks malicious scripts
- DNS monitoring for phishing

### Can it scan email attachments?
Yes, if saved to disk. Email clients themselves aren't monitored.

### Does it slow down my computer?
Minimal impact:
- **Idle**: <50 MB RAM, <1% CPU
- **Scanning**: 200-500 MB RAM, 20-40% CPU
- **Real-time**: <100 MB RAM, 2-5% CPU

### How do I report a bug?
https://github.com/byteworthy/Hafz-Defend/issues

### How do I request a feature?
https://community.hifzdefend.com/features

### Can I become an affiliate?
Yes! Email: affiliates@hifzdefend.com

### Do you offer training for enterprises?
Yes, included with Enterprise licenses.

---

## Still Have Questions?

**Support**: support@hifzdefend.com
**Community**: https://community.hifzdefend.com
**Documentation**: https://docs.hifzdefend.com
**Twitter**: @HifzDefend

---

**© 2026 ByteWorthy. All Rights Reserved.**
