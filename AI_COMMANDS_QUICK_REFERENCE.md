# AI Commands Quick Reference Card

## 🚀 New in v0.2.0: Cost Monitoring Commands

---

## Commands Overview

| Command | Purpose | Example |
|---------|---------|---------|
| `hifzdefend ai test` | Test API connection | `hifzdefend ai test` |
| `hifzdefend ai stats` | View usage statistics | `hifzdefend ai stats` |
| `hifzdefend ai cost` | View cost breakdown | `hifzdefend ai cost` |
| `hifzdefend ai reset-cache` | Clear response cache | `hifzdefend ai reset-cache` |
| `hifzdefend analyze-script <file>` | Analyze script with AI | `hifzdefend analyze-script malware.ps1` |
| `hifzdefend query "<question>"` | Ask security questions | `hifzdefend query "what threats today?"` |
| `hifzdefend explain "<threat>"` | Get threat explanation | `hifzdefend explain "trojan"` |

---

## Common Workflows

### 🔍 Daily Security Check
```powershell
# Check AI status
hifzdefend ai test

# Query recent threats
hifzdefend query "what threats were detected today?"

# Check costs
hifzdefend ai cost
```

### 📊 Monthly Cost Review
```powershell
# View detailed statistics
hifzdefend ai stats

# Check cost breakdown
hifzdefend ai cost

# Optional: Clear cache
hifzdefend ai reset-cache
```

### 🛡️ Analyze Suspicious File
```powershell
# Test API first
hifzdefend ai test

# Analyze the file
hifzdefend analyze-script suspicious.ps1

# Get more info on threat
hifzdefend explain "threat-name-from-analysis"

# Check cost
hifzdefend ai cost
```

### 🔧 Troubleshooting
```powershell
# Test connection
hifzdefend ai test

# View configuration
hifzdefend config-show | Select-String "ai"

# Check stats for errors
hifzdefend ai stats

# Clear cache if issues
hifzdefend ai reset-cache
```

---

## Quick Cost Reference

### Typical Costs (Sonnet Model)
- **Script analysis:** $0.001 - $0.020
- **Security query:** $0.0005 - $0.005
- **Threat explanation:** $0.0003 - $0.002

### Monthly Estimates
- **Light use:** ~$1-2/month (20 analyses, 50 queries)
- **Moderate use:** ~$5-10/month (100 analyses, 200 queries)
- **Heavy use:** ~$30-50/month (500+ analyses, 1000+ queries)

---

## Error Quick Fixes

| Error | Quick Fix |
|-------|-----------|
| API key not set | `$env:CLAUDE_API_KEY = "sk-ant-..."` |
| AI not available | `pip install anthropic chromadb sentence-transformers` |
| Test fails | Check internet, verify API key at console.anthropic.com |
| Cache permission denied | Close HifzDefend processes, try again |
| High costs | Enable caching, switch to Haiku model |

---

## Configuration Quick Tips

### Switch to Cheaper Model
Edit `config/hifzdefend.toml`:
```toml
[ai.claude]
model = "claude-haiku-4"  # Was: claude-sonnet-4-5
```

### Increase Rate Limit
```toml
[ai.claude]
max_requests_per_hour = 200  # Was: 100
```

### Disable Caching (Not Recommended)
```toml
[ai.claude]
cache_responses = false  # Was: true
```

---

## Help Resources

- **Installation:** `docs/QUICKSTART.md`
- **AI Features:** `docs/AI_USAGE.md`
- **Cost Monitoring:** `docs/AI_COST_COMMANDS.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`
- **All commands:** `hifzdefend --help`
- **AI commands:** `hifzdefend ai --help`

---

## Pro Tips 💡

1. **Test before large batches:** `hifzdefend ai test`
2. **Monitor costs daily:** `hifzdefend ai cost`
3. **Enable caching:** Saves 90% on repeated queries
4. **Use Haiku for simple tasks:** Much cheaper
5. **Check cache savings:** `hifzdefend ai cost` shows savings
6. **Clear cache monthly:** Frees disk space
7. **Set API key permanently:** Use Environment Variables

---

## Quick Installation

```powershell
# Clone or download HifzDefend
cd C:\Users\YourUser\Documents\HifzDefend

# Run installer
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

# Test it works
hifzdefend ai test
```

---

**Need more help?** See full documentation in `docs/` folder.

**Found a bug?** Open an issue on GitHub.

**Happy scanning!** 🛡️
