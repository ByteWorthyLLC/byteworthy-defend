# HifzDefend Examples

This directory contains example scripts and queries to help you learn how to use HifzDefend's AI-powered features.

---

## 📁 Directory Contents

```
examples/
├── README.md                          # This file
├── scripts/                           # Example PowerShell/Batch scripts
│   ├── benign_system_check.ps1       # Safe system check script
│   ├── suspicious_download.ps1       # Script that triggers warnings
│   ├── obfuscated_malicious.ps1      # Fake malware for demo (clearly marked)
│   └── python_crypto_miner.py        # Python cryptominer example
├── queries/                           # Natural language query examples
│   ├── basic_queries.txt             # Simple questions for beginners
│   ├── advanced_queries.txt          # Complex analysis queries
│   └── forensic_queries.txt          # Incident investigation queries
└── workflows/                         # Complete workflow examples
    ├── daily_security_check.ps1      # Daily routine script
    ├── analyze_downloads.ps1         # Scan downloads folder
    └── batch_analysis.ps1            # Analyze multiple scripts

```

---

## 🚀 Quick Start

### 1. Set Your API Key

```powershell
$env:CLAUDE_API_KEY = "sk-ant-api03-your-key-here"
```

### 2. Test with Benign Script

```powershell
# Analyze a safe script
cd examples/scripts
hifzdefend analyze-script benign_system_check.ps1
```

### 3. Try Natural Language Queries

```powershell
# Ask about the system
hifzdefend query "what is hifzdefend?"
hifzdefend query "what threats were detected today?"
```

### 4. Get Threat Explanations

```powershell
# Learn about threats
hifzdefend explain "ransomware"
hifzdefend explain "cryptominer"
```

---

## 📝 Example Scripts

### Benign Script
**File**: `scripts/benign_system_check.ps1`
- Safe PowerShell script for testing
- Checks system information
- **Expected Result**: Clean/Safe

### Suspicious Script
**File**: `scripts/suspicious_download.ps1`
- Downloads files from internet
- May trigger warnings
- **Expected Result**: Suspicious/Warning

### Malicious (Demo Only)
**File**: `scripts/obfuscated_malicious.ps1`
- **FAKE** malware for demonstration
- Clearly marked as non-functional
- **Expected Result**: High risk

---

## 💬 Example Queries

See `queries/basic_queries.txt` for ready-to-use questions:

```
what is hifzdefend?
what threats were detected today?
show me all PowerShell alerts
did any files get quarantined?
what domains were blocked?
summarize today's security events
```

---

## 🔄 Example Workflows

### Daily Security Check
**File**: `workflows/daily_security_check.ps1`

```powershell
# Run daily security routine
cd examples/workflows
.\daily_security_check.ps1
```

This script:
1. Tests AI connection
2. Checks recent threats
3. Analyzes downloads folder
4. Shows cost summary

### Batch Analysis
**File**: `workflows/batch_analysis.ps1`

```powershell
# Analyze multiple scripts at once
cd examples/workflows
.\batch_analysis.ps1 C:\Path\To\Scripts
```

---

## 💰 Cost Estimates

Analyzing these examples will cost approximately:

| Activity | Cost | Notes |
|----------|------|-------|
| Analyze benign script | $0.003-0.010 | Small file |
| Analyze suspicious script | $0.005-0.015 | Medium file |
| Analyze malicious script | $0.010-0.025 | Larger, complex |
| Natural language query | $0.001-0.005 | Per query |
| Threat explanation | $0.001-0.003 | Per threat |
| **Total for all examples** | **~$0.05-0.10** | One-time |

**Note**: Cached responses cost $0, so repeating examples is free!

---

## 🧪 Testing Scenarios

### Scenario 1: First-Time User
```powershell
# 1. Set API key
$env:CLAUDE_API_KEY = "sk-ant-..."

# 2. Test connection
hifzdefend ai test

# 3. Analyze safe script
hifzdefend analyze-script examples/scripts/benign_system_check.ps1

# 4. Check costs
hifzdefend ai cost
```

### Scenario 2: Suspicious File Found
```powershell
# 1. Analyze the file
hifzdefend analyze-script suspicious_file.ps1

# 2. Get threat details
hifzdefend explain "trojan"

# 3. Query for similar threats
hifzdefend query "show me all trojan detections"
```

### Scenario 3: Daily Security Routine
```powershell
# 1. Run automated checks
.\workflows\daily_security_check.ps1

# 2. Review AI usage
hifzdefend ai stats

# 3. Optimize costs
hifzdefend ai cost
```

---

## 📚 Learning Path

### Beginner (30 minutes)
1. Read `docs/QUICKSTART.md`
2. Analyze `benign_system_check.ps1`
3. Try 3-5 basic queries
4. Check cost with `hifzdefend ai cost`

### Intermediate (1 hour)
1. Analyze `suspicious_download.ps1`
2. Compare with `obfuscated_malicious.ps1`
3. Try advanced queries
4. Run `daily_security_check.ps1`

### Advanced (2 hours)
1. Analyze your own scripts
2. Create custom queries
3. Build batch analysis workflows
4. Optimize caching and costs

---

## ⚠️ Important Notes

### Fake Malware
- All "malicious" scripts in this folder are **NON-FUNCTIONAL**
- Clearly marked with `[DEMO ONLY - NOT REAL MALWARE]`
- Safe to analyze and study
- Do NOT modify to make them functional

### Best Practices
- Always set API key before testing
- Test connection first: `hifzdefend ai test`
- Monitor costs: `hifzdefend ai cost`
- Enable caching for repeated analyses
- Read documentation: `docs/AI_USAGE.md`

### Privacy
- Example scripts don't access real files
- No data is collected or sent anywhere except Claude API
- API responses may be cached locally
- See `docs/TROUBLESHOOTING.md` for privacy info

---

## 🆘 Need Help?

### Quick References
- **Installation**: `docs/QUICKSTART.md`
- **AI Features**: `docs/AI_USAGE.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **Cost Monitoring**: `docs/AI_COST_COMMANDS.md`
- **Quick Reference**: `AI_COMMANDS_QUICK_REFERENCE.md`

### Common Issues
- **"AI features not available"**: Install dependencies
- **"API key not set"**: Set `CLAUDE_API_KEY`
- **First query slow**: ChromaDB initialization (normal)
- **High costs**: Check cache settings

### Get Support
- Check documentation first
- Review troubleshooting guide
- Test with example scripts
- Verify API key with `hifzdefend ai test`

---

## 🎯 What's Next?

After trying these examples:

1. **Analyze your own files**
   ```powershell
   hifzdefend analyze-script C:\Path\To\YourScript.ps1
   ```

2. **Create custom queries**
   - Ask about your specific security needs
   - Query your own log data
   - Investigate specific threats

3. **Build workflows**
   - Automate daily checks
   - Batch process multiple files
   - Integrate with existing tools

4. **Optimize costs**
   - Enable caching (default)
   - Use Haiku model for simple tasks
   - Monitor with `hifzdefend ai cost`

---

## 📊 Feedback

These examples are designed to help you learn. If you:
- Find issues
- Have suggestions
- Need more examples
- Want specific scenarios

Please let us know!

---

**Happy learning!** 🛡️

Explore these examples to master HifzDefend's AI-powered security features.

---

*Last updated: 2026-01-26*
*Part of HifzDefend v0.2.0*
