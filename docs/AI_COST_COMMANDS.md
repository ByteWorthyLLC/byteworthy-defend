# AI Cost Monitoring Commands

## Overview

HifzDefend v0.2.0 includes powerful cost monitoring commands to help you track and optimize your Claude API usage.

---

## Commands

### `hifzdefend ai stats`

Display comprehensive AI usage statistics.

**Usage:**
```powershell
hifzdefend ai stats
```

**Output:**
```
AI Usage Statistics

API Usage:
  Model: claude-sonnet-4-5
  Total requests: 45
  Successful requests: 43
  Failed requests: 2
  Cached responses: 18

Token Usage:
  Input tokens: 12,450
  Output tokens: 8,320
  Total tokens: 20,770

Cost Information:
  Input cost: $0.0374
  Output cost: $0.1248
  Total cost: $0.1622

Rate Limiting:
  Max requests/hour: 100
  Requests this hour: 12
  Remaining this hour: 88

Cache Status:
  Caching enabled: Yes
  Cache TTL: 24.0 hours
  Cache directory: C:\Users\...\AppData\Local\HifzDefend\cache
  Cached entries: 18
  Cache size: 2.45 MB

Projections:
  Average cost/request: $0.0036
  Est. cost for 100 requests: $0.36
  Est. monthly cost (1000 req): $3.60
```

**What It Shows:**
- **API Usage**: Request counts and success rate
- **Token Usage**: Input/output token breakdown
- **Cost Information**: Detailed cost breakdown
- **Rate Limiting**: Current rate limit status
- **Cache Status**: Cache effectiveness
- **Projections**: Cost estimates based on usage

---

### `hifzdefend ai cost`

Display detailed cost breakdown with pricing information.

**Usage:**
```powershell
hifzdefend ai cost
```

**Output:**
```
AI Cost Breakdown

                   Cost Analysis
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric        ┃       Value ┃ Cost (USD)  ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ Input Tokens  │      12,450 │     $0.0374 │
│ Output Tokens │       8,320 │     $0.1248 │
│ Total         │      20,770 │     $0.1622 │
└───────────────┴─────────────┴─────────────┘

Pricing (per 1M tokens):
  Model: claude-sonnet-4-5
  Input: $3.00
  Output: $15.00

Request Breakdown:
  Total requests: 45
  Successful: 43
  Failed: 2
  From cache: 18

Cache Savings:
  Estimated savings: $0.0648
  Cached responses: 18

Budget Recommendations:
  Low usage - well within budget

For real-time costs, visit: https://console.anthropic.com/settings/costs
```

**What It Shows:**
- **Cost Table**: Visual breakdown of costs
- **Pricing Info**: Current model pricing
- **Request Stats**: Success/failure breakdown
- **Cache Savings**: Money saved by caching
- **Budget Status**: Usage level assessment
- **Optimization Tips**: Personalized suggestions

---

### `hifzdefend ai reset-cache`

Clear the AI response cache to free up disk space or reset costs.

**Usage:**
```powershell
hifzdefend ai reset-cache
```

**Interactive Prompt:**
```
Clear AI Cache

Cache directory: C:\Users\...\AppData\Local\HifzDefend\cache
Cached entries: 18
Cache size: 2.45 MB

Are you sure you want to clear the cache? [y/N]: y

[OK] Cleared 18 cache entries
Note: Cost statistics are stored separately and not affected

Note: Vector database not cleared: C:\Users\...\data\vector_db
To clear vector DB, delete the directory manually:
  Remove-Item -Recurse 'C:\Users\...\data\vector_db'
```

**What It Does:**
- Deletes all cached API responses
- Frees up disk space
- Does NOT reset cost statistics
- Does NOT clear vector database (logs remain searchable)
- Requires confirmation before deleting

**When to Use:**
- Free up disk space
- Test fresh API responses
- Troubleshoot caching issues
- After major config changes

---

### `hifzdefend ai test`

Test Claude API connection and configuration.

**Usage:**
```powershell
hifzdefend ai test
```

**Output (Success):**
```
Testing Claude API Connection

Configuration:
  API key: sk-ant-api03...xyz
  Model: claude-sonnet-4-5
  Max tokens: 4096
  Timeout: 30s
  Caching: Enabled

Testing connection...
Sending test request to Claude...

[OK] Connection successful!

Response:
  OK

Usage:
  Input tokens: 12
  Output tokens: 5
  Test cost: $0.000111

All systems operational!

You can now use:
  • hifzdefend analyze-script <file>
  • hifzdefend query "<question>"
  • hifzdefend explain "<threat>"
```

**Output (Failure):**
```
Testing Claude API Connection

Configuration:
  API key: sk-ant-api03...xyz
  Model: claude-sonnet-4-5
  Max tokens: 4096
  Timeout: 30s
  Caching: Enabled

Testing connection...
Sending test request to Claude...

[FAIL] Connection failed

Error: Invalid authentication credentials

Troubleshooting:
  • Check your API key is correct
  • Verify key is active at: https://console.anthropic.com/settings/keys
  • Try generating a new API key
```

**What It Tests:**
- API key validity
- Network connectivity
- Model accessibility
- Configuration correctness
- Response time

**Common Error Scenarios:**

1. **Authentication Error**
   - Invalid or expired API key
   - Solution: Generate new key

2. **Rate Limit Error**
   - Too many requests
   - Solution: Wait and retry

3. **Timeout Error**
   - Network issues
   - Solution: Check internet connection

4. **API Unavailable**
   - Service outage
   - Solution: Check Anthropic status page

---

## Usage Examples

### Daily Cost Check

```powershell
# Check your daily usage
hifzdefend ai cost

# View detailed statistics
hifzdefend ai stats
```

### Before Large Batch Operations

```powershell
# Test connection first
hifzdefend ai test

# Check current cost
hifzdefend ai cost

# Run your batch operation
Get-ChildItem *.ps1 | ForEach-Object {
    hifzdefend analyze-script $_.FullName
}

# Check new cost
hifzdefend ai cost
```

### Monthly Maintenance

```powershell
# Review monthly costs
hifzdefend ai cost

# Check cache efficiency
hifzdefend ai stats

# Clear old cache (optional)
hifzdefend ai reset-cache
```

### Troubleshooting Setup

```powershell
# Test if API is working
hifzdefend ai test

# If test fails, check configuration
hifzdefend config-show | Select-String "ai"

# View detailed stats to diagnose issues
hifzdefend ai stats
```

---

## Cost Optimization Tips

### 1. Enable Caching (Default)

Caching saves 90%+ on repeated queries:

```toml
[ai.claude]
cache_responses = true
cache_ttl = 86400  # 24 hours
```

**Savings Example:**
- First analysis: $0.005
- Repeat analysis (cached): $0.000
- 20 repeats saved: ~$0.10

### 2. Use Appropriate Model

Choose model based on task complexity:

| Task | Model | Cost/MTok (In/Out) | When to Use |
|------|-------|-------------------|-------------|
| Simple queries | Haiku | $0.25/$1.25 | Quick checks |
| Standard analysis | Sonnet | $3/$15 | Default |
| Complex analysis | Opus | $15/$75 | Critical threats |

**Switch models:**
```toml
[ai.claude]
model = "claude-haiku-4"  # Cheapest
# model = "claude-sonnet-4-5"  # Balanced
# model = "claude-opus-4-5"  # Most capable
```

### 3. Set Rate Limits

Prevent accidental overage:

```toml
[ai.claude]
max_requests_per_hour = 50  # Lower for safety
```

### 4. Monitor Regularly

```powershell
# Daily check
hifzdefend ai cost

# Weekly review
hifzdefend ai stats
```

### 5. Batch Similar Operations

Cache works best with similar queries:

```powershell
# Analyze all scripts at once
Get-ChildItem *.ps1 | ForEach-Object {
    hifzdefend analyze-script $_.FullName
}
```

---

## Understanding Costs

### Pricing (January 2025)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude Haiku 4 | $0.25 | $1.25 |
| Claude Sonnet 4.5 | $3.00 | $15.00 |
| Claude Opus 4.5 | $15.00 | $75.00 |

### Typical Operation Costs (Sonnet)

| Operation | Tokens (In/Out) | Typical Cost |
|-----------|----------------|--------------|
| Small script analysis | 500 / 300 | $0.006 |
| Large script analysis | 2000 / 800 | $0.018 |
| Security query | 1000 / 400 | $0.009 |
| Threat explanation | 300 / 250 | $0.005 |
| Interactive session (10 turns) | 5000 / 3000 | $0.060 |

### Monthly Cost Estimates

**Light Use (Personal):**
- 20 script analyses
- 50 queries
- 10 explanations
- **Total: ~$1-2/month**

**Moderate Use (Professional):**
- 100 script analyses
- 200 queries
- 50 explanations
- **Total: ~$5-10/month**

**Heavy Use (Enterprise):**
- 500+ script analyses
- 1000+ queries
- 200+ explanations
- **Total: ~$30-50/month**

---

## Troubleshooting

### "AI features not available"

```powershell
# Install dependencies
pip install anthropic chromadb sentence-transformers
```

### "Claude API key not set"

```powershell
# Set key
$env:CLAUDE_API_KEY = "sk-ant-api03-..."

# Test it
hifzdefend ai test
```

### "Permission denied on cache"

```powershell
# Close all HifzDefend processes
Get-Process | Where-Object {$_.Path -like "*HifzDefend*"} | Stop-Process

# Try again
hifzdefend ai reset-cache
```

### Stats show $0.00 costs

This is normal for:
- New installation (no usage yet)
- After cache clear (stats persist separately)
- Cached responses only (no new API calls)

Check actual usage at: https://console.anthropic.com/settings/costs

---

## Integration with Other Commands

### With Script Analysis

```powershell
# Check cost before
hifzdefend ai cost

# Analyze script
hifzdefend analyze-script suspicious.ps1

# Check cost after
hifzdefend ai cost
```

### With Natural Language Queries

```powershell
# Test API first
hifzdefend ai test

# Run query
hifzdefend query "what threats today?"

# Check stats
hifzdefend ai stats
```

### Automated Monitoring

```powershell
# Daily cost report script
$date = Get-Date -Format "yyyy-MM-dd"
hifzdefend ai cost > "cost-report-$date.txt"
```

---

## FAQ

**Q: Do cost commands count against my usage?**
A: No, checking stats/costs doesn't make API calls.

**Q: How often are stats updated?**
A: Stats update in real-time after each API call.

**Q: Can I export cost data?**
A: Yes, redirect output to file: `hifzdefend ai cost > costs.txt`

**Q: Does clearing cache reset costs?**
A: No, cost statistics are tracked separately.

**Q: Where are stats stored?**
A: In the ClaudeAnalyzer's internal state and cache metadata.

**Q: Can I set cost alerts?**
A: Not yet - planned for v0.3.0.

---

## Next Steps

- **[Quick Start Guide](QUICKSTART.md)** - Installation
- **[AI Usage Guide](AI_USAGE.md)** - Full AI features
- **[Troubleshooting](TROUBLESHOOTING.md)** - Fix issues

---

**Monitor your costs responsibly!** 💰

Check your usage regularly at: https://console.anthropic.com/settings/costs
