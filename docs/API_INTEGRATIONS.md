# HifzDefend API Integrations Guide

Complete guide to integrating external threat intelligence services, API configuration, and best practices for third-party service usage.

## Table of Contents

- [Overview](#overview)
- [Supported Services](#supported-services)
- [API Key Setup](#api-key-setup)
- [Service Configurations](#service-configurations)
- [Rate Limiting & Quotas](#rate-limiting--quotas)
- [Caching Strategy](#caching-strategy)
- [Graceful Degradation](#graceful-degradation)
- [Privacy Considerations](#privacy-considerations)
- [Troubleshooting](#troubleshooting)

---

## Overview

HifzDefend integrates with external threat intelligence services to enhance detection capabilities:

- **IP Reputation**: AbuseIPDB, Talos Intelligence
- **File Reputation**: VirusTotal
- **Package Security**: Snyk, Socket.dev
- **Domain Intelligence**: Talos, OpenDNS
- **Vulnerability Data**: CVE databases, NVD

### Why Use External Services?

1. **Real-Time Threat Intelligence**: Access to constantly updated threat databases
2. **Community Knowledge**: Benefit from global security community insights
3. **Zero-Day Protection**: Detect newly discovered threats immediately
4. **Reduced False Positives**: Cross-reference multiple sources for accuracy

### Privacy-First Approach

- **Optional**: All external integrations are optional
- **Local-First**: HifzDefend works fully offline with ClamAV only
- **Minimal Data Sharing**: Only hashes and metadata sent (never file contents)
- **Transparent**: Clear documentation on what data is shared

---

## Supported Services

### IP Reputation Services

#### 1. AbuseIPDB
- **Purpose**: Check IP addresses for malicious activity
- **Free Tier**: 1,000 requests/day
- **Paid Tier**: 100,000 requests/day ($20/month)
- **Website**: https://www.abuseipdb.com

#### 2. Talos Intelligence
- **Purpose**: IP/domain reputation from Cisco
- **Free Tier**: Unlimited (rate limited)
- **Paid Tier**: Enterprise access
- **Website**: https://talosintelligence.com

### File Reputation Services

#### 3. VirusTotal
- **Purpose**: Multi-engine malware scanning
- **Free Tier**: 4 requests/minute (500/day)
- **Paid Tier**: 1,000 requests/minute ($100/month)
- **Website**: https://www.virustotal.com

### Package Security Services

#### 4. Snyk
- **Purpose**: npm/pip package vulnerability scanning
- **Free Tier**: 200 tests/month
- **Paid Tier**: Unlimited ($0/month for open source)
- **Website**: https://snyk.io

#### 5. Socket.dev
- **Purpose**: Supply chain security for npm
- **Free Tier**: 100 package checks/month
- **Paid Tier**: Unlimited ($25/month)
- **Website**: https://socket.dev

### Domain Intelligence

#### 6. OpenDNS
- **Purpose**: DNS filtering and threat blocking
- **Free Tier**: Personal use (limited)
- **Paid Tier**: Business plans
- **Website**: https://www.opendns.com

---

## API Key Setup

### Obtaining API Keys

#### AbuseIPDB

1. Visit https://www.abuseipdb.com
2. Sign up for free account
3. Navigate to **Account** → **API**
4. Click **Create Key**
5. Copy API key (format: `abc123...`)

#### VirusTotal

1. Visit https://www.virustotal.com
2. Sign up or log in
3. Click your profile → **API Key**
4. Copy API key (format: `abc123...`)

#### Snyk

1. Visit https://snyk.io
2. Sign up for free account
3. Navigate to **Settings** → **General**
4. Copy API token (format: `abc123...`)

#### Socket.dev

1. Visit https://socket.dev
2. Sign up for account
3. Go to **Settings** → **API Keys**
4. Generate new API key

### Configuring API Keys

**Method 1: Configuration File** (Recommended for personal use)

```toml
# config/hifzdefend.toml
[threat_intel.api_keys]
abuseipdb = "your_abuseipdb_key_here"
virustotal = "your_virustotal_key_here"
snyk = "your_snyk_token_here"
socket_dev = "your_socket_dev_key_here"
```

**Method 2: Environment Variables** (Recommended for teams/CI)

```bash
# Windows (PowerShell)
$env:HIFZDEFEND_ABUSEIPDB_KEY = "your_key"
$env:HIFZDEFEND_VIRUSTOTAL_KEY = "your_key"
$env:HIFZDEFEND_SNYK_TOKEN = "your_token"
$env:HIFZDEFEND_SOCKET_DEV_KEY = "your_key"

# Windows (Command Prompt)
set HIFZDEFEND_ABUSEIPDB_KEY=your_key
set HIFZDEFEND_VIRUSTOTAL_KEY=your_key
```

Add to system environment variables for persistence:
```powershell
[System.Environment]::SetEnvironmentVariable('HIFZDEFEND_ABUSEIPDB_KEY', 'your_key', 'User')
```

**Method 3: CLI Command**

```bash
# Add API key via CLI (stores in config file)
hifzdefend config set threat_intel.api_keys.abuseipdb "your_key"
hifzdefend config set threat_intel.api_keys.virustotal "your_key"

# Verify configuration
hifzdefend config show threat_intel.api_keys
# (Keys are masked: ****1234)
```

### Verifying API Keys

```bash
# Test all configured API keys
hifzdefend test-api-keys

# Example output:
# Testing API connections...
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AbuseIPDB:   ✓ Connected (1,000/1,000 requests remaining)
# VirusTotal:  ✓ Connected (4 req/min, 500/500 daily remaining)
# Snyk:        ✓ Connected (200/200 tests remaining)
# Socket.dev:  ✗ Not configured (skipped)
# Talos:       ✓ Connected (no key required)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Test specific service
hifzdefend test-api abuseipdb
hifzdefend test-api virustotal
```

---

## Service Configurations

### AbuseIPDB Configuration

```toml
[threat_intel.abuseipdb]
enabled = true
api_key = "your_key"

# Minimum confidence score (0-100)
min_confidence = 75

# Maximum age of reports (days)
max_report_age = 30

# Check categories
check_categories = [
    18,  # Brute-Force
    21,  # Malware
    22,  # Botnet
    23,  # Scanner
]

# Rate limiting
max_requests_per_minute = 60  # Free tier: ~4/min effective
max_requests_per_day = 1000   # Free tier limit
```

**Usage Example**:

```python
# Check IP reputation
result = await threat_intel.check_ip_reputation("1.2.3.4")

# Result:
{
    "source": "abuseipdb",
    "ip": "1.2.3.4",
    "abuse_confidence_score": 85,
    "total_reports": 127,
    "last_reported": "2026-01-20",
    "categories": [18, 22],  # Brute-Force, Botnet
    "threat_level": "high",
    "threat_score": 85
}
```

---

### VirusTotal Configuration

```toml
[threat_intel.virustotal]
enabled = true
api_key = "your_key"

# File scanning options
scan_suspicious_downloads = true
scan_new_executables = true

# Minimum detections to consider malicious
min_detections = 5  # Out of ~70 engines

# Detection threshold (percentage)
detection_threshold = 10  # 10% of engines = malicious

# Rate limiting (Free tier)
requests_per_minute = 4
requests_per_day = 500

# Premium features (requires paid API key)
premium_enabled = false
private_scanning = false  # Don't share samples with community
```

**File Hash Lookup**:

```python
# Check file hash against VirusTotal
file_hash = "abc123..."  # SHA256
result = await threat_intel.check_file_reputation(file_hash)

# Result:
{
    "source": "virustotal",
    "sha256": "abc123...",
    "detections": 37,  # Number of engines detecting malware
    "total_engines": 70,
    "detection_rate": 52.8,  # Percentage
    "threat_level": "critical",
    "threat_score": 95,
    "first_seen": "2026-01-15",
    "last_analysis": "2026-01-24",
    "malware_families": ["Trojan.Generic", "Backdoor.Agent"]
}
```

**File Upload** (requires premium):

```python
# Upload file for scanning (Premium only)
result = await threat_intel.upload_file_for_scan("suspicious.exe")
```

---

### Snyk Configuration

```toml
[threat_intel.snyk]
enabled = true
api_token = "your_token"

# Package managers to monitor
npm = true
pip = true
maven = false
nuget = false

# Vulnerability severity levels to alert on
alert_on_low = false
alert_on_medium = false
alert_on_high = true
alert_on_critical = true

# Scan options
scan_on_install = true
scan_dependencies = true
scan_dev_dependencies = false

# Rate limiting
max_tests_per_month = 200  # Free tier
```

**Package Vulnerability Check**:

```python
# Check npm package
result = await threat_intel.check_package_security("lodash", "4.17.20", "npm")

# Result:
{
    "source": "snyk",
    "package": "lodash",
    "version": "4.17.20",
    "vulnerabilities": [
        {
            "id": "SNYK-JS-LODASH-1234567",
            "title": "Prototype Pollution",
            "severity": "high",
            "cvss_score": 7.4,
            "cve": "CVE-2024-12345",
            "fixed_in": "4.17.21",
            "exploit_maturity": "proof-of-concept"
        }
    ],
    "threat_level": "high",
    "threat_score": 75,
    "recommendation": "Upgrade to lodash@4.17.21"
}
```

---

### Socket.dev Configuration

```toml
[threat_intel.socket_dev]
enabled = true
api_key = "your_key"

# Detection categories
detect_install_scripts = true
detect_obfuscated_code = true
detect_network_access = true
detect_filesystem_access = true
detect_shell_access = true

# Supply chain risk scoring
min_risk_score = 70  # 0-100 (higher = riskier)

# Rate limiting
max_checks_per_month = 100  # Free tier
```

**npm Package Analysis**:

```python
# Analyze npm package for supply chain risks
result = await threat_intel.check_package_supply_chain("some-package", "1.0.0")

# Result:
{
    "source": "socket_dev",
    "package": "some-package",
    "version": "1.0.0",
    "risk_score": 85,  # 0-100
    "issues": [
        {
            "type": "network",
            "severity": "high",
            "description": "Package makes network requests during install"
        },
        {
            "type": "filesystem",
            "severity": "medium",
            "description": "Writes to sensitive directories"
        }
    ],
    "threat_level": "high",
    "threat_score": 85,
    "recommendation": "Review package code before installing"
}
```

---

## Rate Limiting & Quotas

### Understanding Rate Limits

| Service | Free Tier | Premium Tier | Reset Period |
|---------|-----------|--------------|--------------|
| AbuseIPDB | 1,000/day | 100,000/day | Daily (UTC) |
| VirusTotal | 4/min, 500/day | 1,000/min | Minute/Daily |
| Snyk | 200 tests/month | Unlimited | Monthly |
| Socket.dev | 100/month | Unlimited | Monthly |
| Talos | Rate limited | N/A | Dynamic |

### Rate Limit Handling

HifzDefend automatically handles rate limits:

1. **Request Queueing**: Queues requests when rate limit reached
2. **Exponential Backoff**: Retries with increasing delays
3. **Graceful Degradation**: Falls back to local detection if quota exceeded
4. **Quota Monitoring**: Tracks remaining quota and warns users

**Configuration**:

```toml
[threat_intel.rate_limiting]
enabled = true

# Queue requests when rate limited
queue_on_limit = true
max_queue_size = 100

# Retry strategy
max_retries = 3
retry_delay = 5  # seconds
backoff_multiplier = 2  # 5s, 10s, 20s

# Graceful degradation
fallback_to_local = true
warn_on_quota_exhausted = true
```

**Quota Monitoring**:

```bash
# Check API quota status
hifzdefend quota status

# Example output:
# API Quota Status
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Service     | Used    | Remaining | Resets
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AbuseIPDB   | 234     | 766       | 18h 23m
# VirusTotal  | 387     | 113       | 6h 45m
# Snyk        | 45      | 155       | 12d 3h
# Socket.dev  | 23      | 77        | 25d 15h
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Set quota alerts
hifzdefend quota set-alert virustotal 100  # Alert when <100 remaining
```

---

## Caching Strategy

### Why Caching?

- **Reduce API Calls**: Save quota by caching results
- **Faster Responses**: Instant results for previously checked items
- **Offline Support**: Use cached data when internet unavailable

### Cache Configuration

```toml
[threat_intel.cache]
enabled = true

# Cache backend
backend = "sqlite"  # Options: sqlite, redis, memory
cache_file = "%LOCALAPPDATA%\\HifzDefend\\cache\\threat_intel.db"

# Cache TTL (Time To Live)
ttl_ip_reputation = 3600       # 1 hour
ttl_file_reputation = 86400    # 24 hours
ttl_package_security = 21600   # 6 hours
ttl_domain_reputation = 7200   # 2 hours

# Cache size limits
max_cache_size_mb = 100
max_entries = 10000

# Eviction policy
eviction_policy = "lru"  # Options: lru, lfu, fifo

# Cache warming (pre-populate with common queries)
warm_cache_on_start = false
```

### Cache Management

```bash
# View cache statistics
hifzdefend cache stats

# Example output:
# Cache Statistics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Total Entries:     1,247
# Cache Size:        12.4 MB
# Hit Rate:          87.3%
# Miss Rate:         12.7%
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# By Type:
#   IP Reputation:     543 entries
#   File Reputation:   432 entries
#   Package Security:  272 entries
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Clear cache
hifzdefend cache clear

# Clear specific cache type
hifzdefend cache clear --type ip_reputation

# Manually add to cache
hifzdefend cache add ip 1.2.3.4 --threat-level high --ttl 3600
```

---

## Graceful Degradation

### Handling Service Unavailability

HifzDefend gracefully handles service failures:

1. **Automatic Fallback**: Uses local detection when API unavailable
2. **User Notification**: Warns when service offline
3. **Retry Logic**: Retries failed requests automatically
4. **Offline Mode**: Full functionality without external services

**Configuration**:

```toml
[threat_intel.graceful_degradation]
enabled = true

# Fallback behavior
fallback_to_local_on_error = true
fallback_to_cache_on_error = true

# Service timeout (seconds)
timeout_connect = 5
timeout_read = 10

# Health checks
health_check_enabled = true
health_check_interval = 300  # 5 minutes

# Notification
notify_on_service_down = true
notify_on_service_restored = true
```

**Service Health Monitoring**:

```bash
# Check service health
hifzdefend health-check

# Example output:
# Threat Intelligence Service Health
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Service      | Status | Latency | Uptime
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AbuseIPDB    | ✓ UP   | 127ms   | 99.9%
# VirusTotal   | ✓ UP   | 245ms   | 98.7%
# Snyk         | ✗ DOWN | N/A     | 95.2%
# Socket.dev   | ✓ UP   | 89ms    | 99.5%
# Talos        | ✓ UP   | 156ms   | 99.8%
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Privacy Considerations

### What Data is Shared?

| Service | Data Sent | Data NOT Sent |
|---------|-----------|---------------|
| AbuseIPDB | IP addresses only | File contents, usernames |
| VirusTotal | File hashes (SHA256) | Full files (unless uploaded), paths |
| Snyk | Package name + version | Code, .env files |
| Socket.dev | Package name + version | Source code |
| Talos | IP addresses, domains | File contents |

### Privacy Configuration

```toml
[threat_intel.privacy]
# Anonymization
anonymize_requests = false  # Use proxy/VPN if enabled

# Limit data sharing
share_file_hashes_only = true  # Never upload full files
share_package_names_only = true  # Never share code

# Opt-out of data sharing with community
virustotal_share_samples = false  # Don't share files with VT community
abuseipdb_contribute_reports = false  # Don't submit new IPs

# Local-only mode (no external API calls)
local_only_mode = false
```

### GDPR Compliance

HifzDefend is GDPR-compliant:

- **Consent**: External services are opt-in
- **Data Minimization**: Only necessary data is sent
- **Transparency**: Clear documentation of data sharing
- **User Control**: Easy to disable any service
- **Data Retention**: Cache can be cleared anytime

**Disable all external services**:

```toml
[threat_intel]
enabled = false  # Disables all external API integrations
```

---

## Troubleshooting

### Common Issues

#### API Key Not Working

```bash
# Test API key
hifzdefend test-api virustotal

# Error: Invalid API key
# Solution:
# 1. Verify key is correct (copy from VirusTotal account)
# 2. Check for extra spaces: "abc123 " ← space at end
# 3. Ensure key is active (not expired or revoked)
# 4. Try regenerating key from service dashboard
```

#### Rate Limit Exceeded

```bash
# Error: Rate limit exceeded (429 Too Many Requests)

# Check quota
hifzdefend quota status

# Solutions:
# 1. Wait for quota reset
# 2. Enable caching to reduce API calls
# 3. Upgrade to paid tier
# 4. Disable specific monitors to reduce load
```

#### Service Timeout

```bash
# Error: Connection timeout

# Check internet connection
ping api.abuseipdb.com

# Solutions:
# 1. Check firewall/antivirus not blocking HifzDefend
# 2. Increase timeout in config
# 3. Try different network (VPN may interfere)
```

#### Cache Corruption

```bash
# Error: Cache read error

# Clear cache
hifzdefend cache clear

# Rebuild cache
hifzdefend cache rebuild
```

---

## Advanced Topics

### Custom API Integration

You can extend HifzDefend with custom threat intelligence sources:

**Example**: Integrate custom threat feed

```python
# src/hifzdefend/threat_intel/custom_api.py

from hifzdefend.threat_intel.base import ThreatIntelAPI

class CustomThreatAPI(ThreatIntelAPI):
    """Custom threat intelligence integration."""

    def __init__(self, config):
        super().__init__(config)
        self.api_url = "https://custom-api.com/v1"
        self.api_key = config.api_keys.custom_api

    async def check_ip_reputation(self, ip: str) -> dict:
        """Check IP against custom threat feed."""
        response = await self.session.get(
            f"{self.api_url}/ip/{ip}",
            headers={"X-API-Key": self.api_key}
        )
        data = await response.json()

        return {
            "source": "custom_api",
            "ip": ip,
            "threat_level": data.get("threat_level"),
            "threat_score": data.get("score"),
            "details": data
        }
```

Register in config:

```toml
[threat_intel.custom_sources]
enabled = true

[[threat_intel.custom_sources.apis]]
name = "custom_api"
module = "hifzdefend.threat_intel.custom_api"
class = "CustomThreatAPI"
api_key = "your_key"
```

---

## Best Practices

1. **Start with Free Tiers**: Test services before upgrading
2. **Enable Caching**: Reduce API calls and costs
3. **Monitor Quotas**: Set alerts before hitting limits
4. **Prioritize Services**: Enable only what you need
5. **Regular Updates**: Check for new service features
6. **API Key Security**: Store keys in environment variables
7. **Test Integrations**: Verify connections regularly
8. **Graceful Degradation**: Always have local fallback

---

## Service Comparison

| Feature | AbuseIPDB | VirusTotal | Snyk | Socket.dev |
|---------|-----------|------------|------|------------|
| **Purpose** | IP reputation | File scanning | Vuln scanning | Supply chain |
| **Free Tier** | ✓ Good | ✓ Limited | ✓ Good | ✓ Limited |
| **Accuracy** | High | Very High | High | High |
| **Speed** | Fast | Medium | Fast | Fast |
| **Coverage** | IPs only | Files/URLs | Packages | npm only |
| **Cost** | $20/mo | $100/mo | Free (OSS) | $25/mo |

---

**Last Updated**: 2026-01-25
**Version**: Phase 1.5
