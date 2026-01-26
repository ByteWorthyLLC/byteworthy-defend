# HifzDefend Troubleshooting Guide

## 🔧 Common Issues and Solutions

This guide helps you fix common problems with HifzDefend.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [API Key Problems](#api-key-problems)
3. [ClamAV Connection Errors](#clamav-connection-errors)
4. [AI Feature Errors](#ai-feature-errors)
5. [ChromaDB Issues](#chromadb-issues)
6. [Performance Problems](#performance-problems)
7. [Unicode/Encoding Errors](#unicodeencoding-errors)
8. [Cost Concerns](#cost-concerns)

---

## Installation Issues

### Problem: "Python not found"

**Symptoms:**
```
'python' is not recognized as an internal or external command
```

**Solution:**
```powershell
# Download Python from https://www.python.org/downloads/
# Make sure to check "Add Python to PATH" during installation

# Verify installation
python --version  # Should show Python 3.11+
```

### Problem: "pip install fails"

**Symptoms:**
```
ERROR: Could not build wheels for package-name
```

**Solution:**
```powershell
# Update pip
python -m pip install --upgrade pip setuptools wheel

# Try installing again
pip install -e ".[dev]"

# If still fails, install build tools
# Download Visual Studio Build Tools from Microsoft
```

### Problem: "Virtual environment activation fails"

**Symptoms:**
```
cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
# Allow script execution (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate again
.venv312\Scripts\activate
```

---

## API Key Problems

### Problem: "CLAUDE_API_KEY not set"

**Symptoms:**
```
[ERROR] Claude API key not set
Set environment variable: CLAUDE_API_KEY=sk-ant-api03-...
```

**Solution:**
```powershell
# Option 1: Temporary (current session only)
$env:CLAUDE_API_KEY = "sk-ant-api03-YOUR-KEY-HERE"

# Option 2: Permanent (recommended)
[Environment]::SetEnvironmentVariable("CLAUDE_API_KEY", "sk-ant-api03-YOUR-KEY", "User")

# Restart your terminal
# Verify it's set
echo $env:CLAUDE_API_KEY
```

### Problem: "Invalid API key format"

**Symptoms:**
```
ValueError: Invalid API key format
```

**Solution:**
```powershell
# Check your API key format
# Valid: sk-ant-api03-... (starts with sk-ant-)
# Invalid: Any other format

# Get a new key from: https://console.anthropic.com/settings/keys
```

### Problem: "API authentication failed"

**Symptoms:**
```
anthropic.AuthenticationError: Invalid API key
```

**Solution:**
1. Verify your API key is correct
2. Check if your API key is still active at https://console.anthropic.com/settings/keys
3. Make sure there are no extra spaces or quotes
4. Try generating a new API key

---

## ClamAV Connection Errors

### Problem: "ClamAV daemon not running"

**Symptoms:**
```
[FAIL] ClamAV daemon: Not running
Expected at: localhost:3310
```

**Understanding:**
- ClamAV is **optional** for AI features
- AI script analysis works **without** ClamAV
- ClamAV is only needed for traditional antivirus scanning

**Solutions:**

#### Option 1: Use AI Features Only (Recommended)
```powershell
# You can use all AI features without ClamAV:
hifzdefend analyze-script file.ps1  # ✅ Works
hifzdefend query "what threats today?"  # ✅ Works
hifzdefend explain "trojan"  # ✅ Works

# These require ClamAV:
hifzdefend scan Downloads  # ❌ Needs ClamAV
hifzdefend status  # ❌ Shows ClamAV error
```

#### Option 2: Install ClamAV
```powershell
# 1. Download ClamAV for Windows
# https://www.clamav.net/downloads

# 2. Install and configure
# Extract to C:\Program Files\ClamAV

# 3. Configure clamd.conf
# Set: TCPSocket 3310
# Set: TCPAddr localhost

# 4. Start the daemon
cd "C:\Program Files\ClamAV"
.\clamd.exe

# 5. Update virus definitions
.\freshclam.exe
```

### Problem: "Connection timeout"

**Symptoms:**
```
Error 10061: No connection could be made
```

**Solution:**
```powershell
# Check if clamd is running
Get-Process clamd -ErrorAction SilentlyContinue

# Check if port 3310 is listening
netstat -an | findstr "3310"

# Restart clamd
taskkill /IM clamd.exe /F
cd "C:\Program Files\ClamAV"
.\clamd.exe
```

---

## AI Feature Errors

### Problem: "AI features not available"

**Symptoms:**
```
[ERROR] AI features not available
Install AI dependencies: pip install anthropic chromadb sentence-transformers
```

**Solution:**
```powershell
# Activate your virtual environment
.venv312\Scripts\activate

# Install AI dependencies
pip install anthropic chromadb sentence-transformers

# Verify installation
python -c "import anthropic; import chromadb; print('AI ready!')"
```

### Problem: "Claude AI is disabled"

**Symptoms:**
```
[ERROR] Claude AI is disabled
Enable in config: [ai.claude] enabled = true
```

**Solution:**
```powershell
# Edit your config file
notepad config\hifzdefend.toml

# Make sure these are set to true:
[ai]
enabled = true

[ai.claude]
enabled = true
script_analysis = true
plain_language_explanations = true

# Save and try again
```

### Problem: "Script analysis is disabled"

**Symptoms:**
```
[ERROR] Script analysis is disabled
Enable in config: [ai.claude] script_analysis = true
```

**Solution:**
```powershell
# Edit config
notepad config\hifzdefend.toml

# Set:
[ai.claude]
script_analysis = true

# Save and restart
```

---

## ChromaDB Issues

### Problem: "ChromaDB not available"

**Symptoms:**
```
⚠️ ChromaDB not available. Install: pip install chromadb
```

**Solution:**
```powershell
# Install ChromaDB
pip install chromadb

# If installation fails, try:
pip install --upgrade pip
pip install chromadb --no-cache-dir
```

### Problem: "ChromaDB database corruption"

**Symptoms:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solution:**
```powershell
# Delete the corrupted database
Remove-Item -Recurse -Force data\vector_db

# It will be recreated automatically
hifzdefend query "test"
```

### Problem: "Permission denied on vector_db"

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: 'data/vector_db'
```

**Solution:**
```powershell
# Check if another process is using it
Get-Process | Where-Object {$_.Path -like "*HifzDefend*"}

# Close all HifzDefend processes
# Then try again
```

---

## Performance Problems

### Problem: "Commands are very slow"

**Symptoms:**
- `hifzdefend status` takes 30+ seconds
- Commands hang or timeout

**Solution:**
```powershell
# Check if ClamAV connection is timing out
# This is the most common cause

# Option 1: Disable ClamAV connection check temporarily
# (Not yet implemented - coming in v0.2.1)

# Option 2: Start ClamAV so connection succeeds
.\clamd.exe

# Option 3: Use only AI commands (don't need ClamAV)
hifzdefend analyze-script file.ps1  # Fast
hifzdefend query "question"  # Fast
```

### Problem: "AI queries are slow"

**Symptoms:**
- Queries take 10+ seconds
- Analysis takes 30+ seconds

**Solution:**
```powershell
# This is normal for large scripts/queries
# Optimize by:

# 1. Enable caching (default)
[ai.claude]
cache_responses = true

# 2. Use smaller script files
# Break large files into modules

# 3. Use Haiku model (faster, cheaper)
[ai.claude]
model = "claude-haiku-4"
```

### Problem: "High memory usage"

**Symptoms:**
- Python using 500MB+ RAM
- System slowdown

**Solution:**
```powershell
# ChromaDB can use memory for embeddings
# Clear cache periodically:
hifzdefend ai-reset-cache

# Reduce embedding model size in config:
[ai.natural_language]
embedding_model = "all-MiniLM-L6-v2"  # Small model
```

---

## Unicode/Encoding Errors

### Problem: "'charmap' codec can't encode character"

**Symptoms:**
```
Fatal error: 'charmap' codec can't encode character '\u2717'
```

**Solution:**
```powershell
# This has been fixed in v0.2.0
# Make sure you're using the latest version:
hifzdefend --version

# If still seeing errors:
$env:PYTHONIOENCODING = "utf-8"

# Or run in Windows Terminal instead of cmd.exe
```

### Problem: "Unicode characters not displaying"

**Symptoms:**
- Squares or question marks instead of symbols
- Garbled output

**Solution:**
```powershell
# Use Windows Terminal (recommended)
# Download from Microsoft Store

# Or enable UTF-8 in cmd.exe:
chcp 65001
```

---

## Cost Concerns

### Problem: "API costs are high"

**Symptoms:**
- Unexpected charges
- Cost warnings

**Solution:**
```powershell
# Check your usage:
hifzdefend ai-cost

# Common causes:
# 1. Analyzing very large scripts
#    Solution: Break into smaller files

# 2. Cache disabled
#    Solution: Enable in config
[ai.claude]
cache_responses = true

# 3. Too many unique queries
#    Solution: Reuse similar queries

# 4. Using Opus model
#    Solution: Switch to Sonnet or Haiku
[ai.claude]
model = "claude-haiku-4"  # Cheapest

# Set strict limits:
[ai.claude]
max_requests_per_hour = 50  # Lower limit
```

### Problem: "Rate limit exceeded"

**Symptoms:**
```
⚠️ API cost limit reached ($50)
RateLimitError: Rate limit exceeded
```

**Solution:**
```powershell
# Wait 1 hour for limit to reset

# Or adjust limits in config:
[ai.claude]
max_requests_per_hour = 200  # Increase if needed

# Check usage:
hifzdefend ai-stats

# Reset cost tracking:
hifzdefend ai-reset-cache
```

---

## Other Issues

### Problem: "Module not found" errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'package'
```

**Solution:**
```powershell
# Make sure virtual environment is activated
.venv312\Scripts\activate

# Reinstall dependencies
pip install -e ".[dev]"
```

### Problem: "Config file not found"

**Symptoms:**
```
FileNotFoundError: config/hifzdefend.toml
```

**Solution:**
```powershell
# Create default config
mkdir config -ErrorAction SilentlyContinue
hifzdefend config-show > config\hifzdefend.toml

# Or copy example config
cp config\hifzdefend.example.toml config\hifzdefend.toml
```

### Problem: "Log files growing too large"

**Symptoms:**
- Disk space warnings
- logs/ folder is huge

**Solution:**
```powershell
# Clear old logs (safe)
Remove-Item logs\* -Filter "*.log.old"

# Or configure log rotation in config:
[logging]
max_bytes = 10485760  # 10MB
backup_count = 3  # Keep 3 old logs
```

---

## Still Need Help?

### Diagnostic Information

When reporting issues, include:

```powershell
# System info
hifzdefend --version
python --version
pip list | findstr "anthropic\|chromadb\|clamd"

# Config
hifzdefend config-show

# Logs (last 20 lines)
Get-Content logs\hifzdefend.log -Tail 20
```

### Get Support

1. **Check existing issues**: [GitHub Issues](https://github.com/yourusername/hifzdefend/issues)
2. **Read documentation**: [README.md](../README.md)
3. **Open a new issue**: Include diagnostic info above
4. **Email support**: contact@hifzdefend.local (coming soon)

---

## Quick Reference: Common Solutions

| Problem | Quick Fix |
|---------|-----------|
| API key error | `$env:CLAUDE_API_KEY = "sk-ant-..."` |
| ClamAV not running | Use AI features only (they don't need ClamAV) |
| AI not available | `pip install anthropic chromadb sentence-transformers` |
| ChromaDB error | `rm -r data\vector_db` |
| Slow performance | Use AI commands instead of status/scan |
| High costs | Enable caching, use Haiku model |
| Unicode errors | Use Windows Terminal, update to v0.2.0 |
| Module not found | `.venv312\Scripts\activate` then `pip install -e ".[dev]"` |

---

## Preventive Maintenance

### Weekly Checks
```powershell
# Check costs
hifzdefend ai-cost

# Check logs
Get-Content logs\hifzdefend.log -Tail 50

# Update dependencies
pip install --upgrade anthropic chromadb
```

### Monthly Tasks
```powershell
# Clear old logs
Remove-Item logs\*.log.old

# Clear AI cache
hifzdefend ai-reset-cache

# Review configuration
hifzdefend config-show
```

---

**Still stuck?** [Open an issue](https://github.com/yourusername/hifzdefend/issues) with detailed error messages and diagnostic info.
