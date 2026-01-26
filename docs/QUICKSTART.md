# HifzDefend Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will help you install and start using HifzDefend's AI-powered malware detection.

---

## Prerequisites

- **Windows 10/11** (64-bit)
- **Python 3.11+** ([Download here](https://www.python.org/downloads/))
- **Claude API Key** (for AI features)

---

## Step 1: Installation

### Option A: Automated Installation (Recommended)

```powershell
# Navigate to the HifzDefend directory
cd C:\Users\YourUsername\Documents\HifzDefend

# Run the installation script
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

### Option B: Manual Installation

```powershell
# 1. Create a virtual environment
python -m venv .venv312

# 2. Activate the virtual environment
.venv312\Scripts\activate

# 3. Install HifzDefend with all dependencies
pip install -e ".[dev]"

# 4. Install AI dependencies
pip install anthropic chromadb sentence-transformers

# 5. Verify installation
hifzdefend --version
```

---

## Step 2: Get Your Claude API Key

1. Go to [Anthropic Console](https://console.anthropic.com/settings/keys)
2. Sign up or log in
3. Click "Create Key"
4. Copy your API key (starts with `sk-ant-api03-...`)

---

## Step 3: Configure API Key

### Option A: Environment Variable (Recommended)

```powershell
# Set permanently for your user account
[Environment]::SetEnvironmentVariable("CLAUDE_API_KEY", "sk-ant-api03-YOUR-KEY-HERE", "User")

# Restart your terminal for changes to take effect
```

### Option B: .env File

Create a `.env` file in the HifzDefend directory:

```env
CLAUDE_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

---

## Step 4: Verify Installation

Test that everything is working:

```powershell
# Check version
hifzdefend --version

# View help
hifzdefend --help

# Test AI connection (if API key is set)
hifzdefend query "what is hifzdefend?"
```

---

## Step 5: Your First Scan

### Analyze a Script with AI

```powershell
# Create a test script
echo "Write-Host 'Hello, World!'" > test.ps1

# Analyze it with Claude
hifzdefend analyze-script test.ps1
```

**Expected Output:**
```
Claude Script Analyzer
Analyzing: test.ps1

Analysis Results:

Threat Level: SAFE
Confidence: 95.0%

Summary:
This is a benign PowerShell script that simply prints "Hello, World!" to the console.

API Cost: $0.0012 (150 in, 75 out)
```

### Ask Security Questions

```powershell
# Query your security logs
hifzdefend query "what threats were detected today?"

# Explain a threat
hifzdefend explain "Trojan.Win32.Generic"
```

### Scan Files with ClamAV

```powershell
# Scan a directory
hifzdefend scan Downloads

# Scan with report
hifzdefend scan Downloads --save-report
```

**Note:** ClamAV integration requires `clamd` daemon running. See [Troubleshooting](TROUBLESHOOTING.md#clamav-not-running) if you see connection errors.

---

## Common Commands

| Command | Description |
|---------|-------------|
| `hifzdefend --help` | Show all available commands |
| `hifzdefend --version` | Show version information |
| `hifzdefend status` | Check system status |
| `hifzdefend analyze-script <file>` | Analyze a script with AI |
| `hifzdefend query "<question>"` | Ask security questions |
| `hifzdefend explain "<threat>"` | Get threat explanation |
| `hifzdefend scan <path>` | Scan files/directories |
| `hifzdefend monitor status` | Check monitor status |
| `hifzdefend rules list` | List detection rules |

---

## What's Next?

### Learn More
- **[AI Features Guide](AI_USAGE.md)** - Deep dive into AI capabilities
- **[Troubleshooting](TROUBLESHOOTING.md)** - Fix common issues
- **[Full Documentation](../README.md)** - Complete feature list

### Configure HifzDefend
```powershell
# View current configuration
hifzdefend config-show

# Edit configuration file
notepad config\hifzdefend.toml
```

### Monitor Your System
```powershell
# Start real-time monitoring
hifzdefend monitor start

# View monitor status
hifzdefend monitor status

# Stop monitoring
hifzdefend monitor stop
```

---

## Cost Management

Claude API usage is pay-per-use:

| Operation | Approximate Cost |
|-----------|------------------|
| Script analysis | $0.001 - $0.005 |
| Security query | $0.0005 - $0.002 |
| Threat explanation | $0.0003 - $0.001 |

**Default safety limits:**
- **Max requests/hour:** 100
- **Cached responses:** Enabled (reduces costs)
- **Cost tracking:** Enabled by default

View your usage:
```powershell
hifzdefend ai-cost  # Show cost breakdown
hifzdefend ai-stats # Show usage statistics
```

---

## Need Help?

- **Errors?** Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- **Questions?** See [AI Usage Guide](AI_USAGE.md)
- **Issues?** [Report on GitHub](https://github.com/yourusername/hifzdefend/issues)

---

## Quick Troubleshooting

### "API key not set"
```powershell
# Set your API key
$env:CLAUDE_API_KEY = "sk-ant-api03-YOUR-KEY"
```

### "AI features not available"
```powershell
# Install AI dependencies
pip install anthropic chromadb sentence-transformers
```

### "ClamAV daemon not running"
```powershell
# ClamAV is optional for AI features
# AI analysis works without ClamAV
# To install ClamAV: See full docs
```

---

## Example Workflow

```powershell
# 1. Analyze a suspicious downloaded script
hifzdefend analyze-script Downloads\installer.ps1

# 2. If it looks suspicious, ask Claude for more info
hifzdefend explain "PowerShell Download-Execute Pattern"

# 3. Check if similar threats were detected recently
hifzdefend query "show me all suspicious PowerShell scripts from today"

# 4. Scan the entire Downloads folder
hifzdefend scan Downloads --save-report
```

---

**Ready to protect your system? Let's go! 🛡️**

For detailed AI features, see the [AI Usage Guide](AI_USAGE.md).
