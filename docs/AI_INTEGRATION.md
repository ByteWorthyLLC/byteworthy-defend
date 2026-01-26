# HifzDefend AI Integration

AI-powered threat analysis and natural language query interface using Claude.

## Overview

HifzDefend v0.2.0 introduces Claude AI integration for:

- **Script Analysis**: Analyze PowerShell, Batch, and Python scripts for threats
- **Network Behavior Analysis**: Detect malicious network patterns
- **Plain Language Explanations**: Understand threats in simple terms
- **Natural Language Queries**: Ask questions about security logs
- **Incident Report Generation**: Auto-generate human-readable incident reports

## Features

### 1. Claude-Powered Threat Analyzer

Analyzes scripts and network behavior using Claude AI:

```bash
# Analyze a PowerShell script
hifzdefend analyze-script suspicious.ps1

# Analyze with specific type
hifzdefend analyze-script malware.bat --type batch

# Save analysis report
hifzdefend analyze-script script.py --save
```

**What it detects:**
- Obfuscation or encoding
- Network connections
- File system modifications
- Registry changes
- Process execution
- Privilege escalation
- Data exfiltration

**Output:**
- Threat level (safe, suspicious, malicious, critical)
- Confidence score
- Plain language summary
- Threat indicators
- Actionable recommendations

### 2. Natural Language Query Interface

Ask questions about your security logs using natural language:

```bash
# Single query
hifzdefend query "what threats were detected today?"
hifzdefend query "show me all PowerShell alerts"
hifzdefend query "are there any network anomalies?"

# Interactive mode
hifzdefend query --interactive
```

**How it works:**
1. Security logs are indexed with semantic embeddings
2. Your question is converted to a vector embedding
3. Relevant logs are retrieved using similarity search
4. Claude generates a natural language answer with context

**Example queries:**
- "What threats were detected in the last 24 hours?"
- "Show me all high-severity events"
- "Are there any suspicious PowerShell activities?"
- "What files were quarantined this week?"
- "Explain the registry changes detected yesterday"

### 3. Plain Language Threat Explanations

Get simple explanations of threats:

```bash
hifzdefend explain THR-001
hifzdefend explain "Trojan.Win32.Generic"
```

**Example explanation:**
```
This is a generic Trojan horse malware.

What is it?
A Trojan disguises itself as legitimate software but secretly performs
malicious actions like stealing data, installing backdoors, or downloading
additional malware.

Why is it dangerous?
It can give attackers remote control of your computer, steal passwords
and personal files, and download more malicious software without your
knowledge.

How did it get here?
Likely from downloading files from untrusted sources, opening email
attachments, or clicking malicious links.

What should you do?
1. Keep the file quarantined (do not restore it)
2. Run a full system scan
3. Change your important passwords
4. Monitor your accounts for suspicious activity
```

## Setup

### 1. Install Dependencies

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install AI dependencies
pip install anthropic>=0.40.0 chromadb>=0.4.0 sentence-transformers>=2.2.0
```

### 2. Get Claude API Key

1. Sign up at https://console.anthropic.com/
2. Create an API key
3. Set as environment variable:

```powershell
# PowerShell (temporary - current session)
$env:CLAUDE_API_KEY = "sk-ant-api03-your-api-key-here"

# PowerShell (permanent - user)
[Environment]::SetEnvironmentVariable("CLAUDE_API_KEY", "sk-ant-api03-your-key", "User")

# Verify it's set
echo $env:CLAUDE_API_KEY
```

Or add to config file:

```toml
[ai.claude]
api_key = "sk-ant-api03-your-api-key-here"
```

**Security Note:** Never commit API keys to git. Always use environment variables for production.

### 3. Configure AI Features

Edit `%LOCALAPPDATA%\HifzDefend\hifzdefend.toml`:

```toml
[ai]
enabled = true

[ai.claude]
enabled = true
api_key = "${CLAUDE_API_KEY}"  # Reads from environment variable
model = "claude-sonnet-4-20250514"
max_tokens = 2048
temperature = 0.3
timeout = 30

# Caching (reduces costs)
cache_responses = true
cache_ttl = 3600  # 1 hour
cache_path = "%LOCALAPPDATA%\\HifzDefend\\data\\cache\\claude"

# Cost controls
max_requests_per_hour = 100
warn_at_cost = 10.00   # USD
stop_at_cost = 50.00   # USD
log_api_costs = true

[ai.natural_language]
enabled = true
embedding_model = "all-MiniLM-L6-v2"
vector_db_path = "%LOCALAPPDATA%\\HifzDefend\\data\\vector_db"
max_context_results = 5
```

## Cost Management

### Pricing (Claude Sonnet 4)

- **Input**: $3 per million tokens (~$0.003 per 1K tokens)
- **Output**: $15 per million tokens (~$0.015 per 1K tokens)

### Cost Reduction Strategies

#### 1. Response Caching

Caching is **enabled by default** and can reduce costs by 80-90% for repeated queries:

```toml
[ai.claude]
cache_responses = true
cache_ttl = 3600  # Cache for 1 hour
```

**How it works:**
- First query: Full API call (~2000 tokens = $0.036)
- Subsequent queries (within TTL): Cached ($0.00)

#### 2. Rate Limiting

Prevent runaway costs with hourly limits:

```toml
[ai.claude]
max_requests_per_hour = 100  # Max 100 requests/hour
warn_at_cost = 10.00         # Warning at $10
stop_at_cost = 50.00         # Stop at $50
```

#### 3. Cost Tracking

Monitor costs in real-time:

```bash
# Costs shown after each query
hifzdefend query "what threats today?"
# Output: API Cost: $0.0234 (1,234 in, 789 out)
```

View logs for cumulative costs:

```bash
# Check logs for cost tracking
cat %LOCALAPPDATA%\HifzDefend\logs\hifzdefend.log | grep "API request tracked"
```

### Estimated Monthly Costs

**Light Usage** (10 queries/day):
- 300 queries/month
- ~$5-10/month

**Medium Usage** (50 queries/day):
- 1,500 queries/month
- ~$20-30/month

**Heavy Usage** (200 queries/day):
- 6,000 queries/month
- ~$80-100/month

**With caching** (80% cache hit rate):
- Light: ~$1-2/month
- Medium: ~$4-6/month
- Heavy: ~$16-20/month

## Architecture

### Components

```
AI Integration
├── Claude Analyzer (claude_analyzer.py)
│   ├── Script analysis
│   ├── Network behavior analysis
│   ├── Incident report generation
│   └── Plain language explanations
│
├── Natural Language Interface (nl_interface.py)
│   ├── Vector database (ChromaDB)
│   ├── Semantic search
│   └── RAG (Retrieval Augmented Generation)
│
└── Response Cache (cache.py)
    ├── TTL-based expiration
    ├── Hash-based keys
    └── Automatic cleanup
```

### Data Flow: Script Analysis

```
1. User: hifzdefend analyze-script malware.ps1
   │
2. Read script content
   │
3. Build analysis prompt
   │
4. Check cache (hash of prompt + model + temperature)
   │
   ├─→ Cache HIT → Return cached response
   │
   └─→ Cache MISS → Call Claude API
       │
       ├─→ Send prompt to Claude
       ├─→ Receive analysis (JSON)
       ├─→ Cache response (TTL: 1 hour)
       └─→ Return analysis
   │
5. Parse & display results
   │
6. Track API costs
```

### Data Flow: Natural Language Query

```
1. User: hifzdefend query "what threats today?"
   │
2. Generate query embedding (sentence-transformers)
   │
3. Search vector database (ChromaDB)
   │
   ├─→ Find top 5 relevant log entries
   │
4. Build RAG prompt (question + context logs)
   │
5. Call Claude API (with caching)
   │
   ├─→ Claude analyzes logs
   └─→ Generates natural language answer
   │
6. Display answer + context
```

### Vector Database (ChromaDB)

**Purpose**: Enable semantic search over security logs

**How it works:**
1. Log entries are converted to vector embeddings
2. Embeddings stored in ChromaDB
3. Queries converted to embeddings
4. Similarity search retrieves relevant logs

**Embedding Model**: all-MiniLM-L6-v2
- Size: 22MB
- Speed: ~50 embeddings/second (CPU)
- Quality: Good for semantic search

## Error Handling

### Graceful Degradation

If Claude API fails, HifzDefend continues with core features:

```toml
[ai.claude]
fallback_on_error = true  # Continue with ClamAV on errors
retry_attempts = 3        # Retry failed requests
retry_delay = 2           # Wait 2 seconds between retries
```

### Common Errors

#### 1. Missing API Key

```
ERROR: Claude API key not set
Set environment variable: CLAUDE_API_KEY=sk-ant-api03-...
```

**Solution:**
```powershell
$env:CLAUDE_API_KEY = "sk-ant-api03-your-key"
```

#### 2. Rate Limit Exceeded

```
ERROR: Rate limit exceeded: 100 requests/hour
```

**Solution:**
- Wait for the hourly window to reset
- Increase limit in config: `max_requests_per_hour = 200`

#### 3. API Timeout

```
WARNING: API timeout on attempt 1/3
```

**Solution:**
- Increase timeout: `timeout = 60`
- Check network connection

## Privacy & Security

### Data Privacy

**What is sent to Claude:**
- Script content (for analysis)
- Security log entries (for queries)
- User questions (for queries)

**What is NOT sent:**
- Personal files (unless explicitly analyzed)
- System information
- API keys or credentials

### Security Best Practices

1. **Never commit API keys to git**
   - Use environment variables
   - Add `.env` to `.gitignore`

2. **Limit API costs**
   - Set `stop_at_cost` limit
   - Monitor usage regularly

3. **Review analyzed content**
   - Don't analyze files with sensitive data
   - Review logs before querying

4. **Use caching**
   - Reduces API calls
   - Faster responses
   - Lower costs

## Troubleshooting

### Check AI Status

```bash
# Verify dependencies installed
pip list | grep -E "anthropic|chromadb|sentence"

# Check config
hifzdefend config-show | grep -A 20 "\[ai\]"

# Test API key
python -c "import os; print('API Key:', os.getenv('CLAUDE_API_KEY', 'NOT SET'))"
```

### Clear Cache

```bash
# Clear Claude response cache
rm -rf %LOCALAPPDATA%\HifzDefend\data\cache\claude\*

# Clear vector database
rm -rf %LOCALAPPDATA%\HifzDefend\data\vector_db\*
```

### Debug Mode

Enable debug logging:

```toml
[logging]
level = "DEBUG"
```

View logs:

```bash
cat %LOCALAPPDATA%\HifzDefend\logs\hifzdefend.log
```

## Limitations

1. **API Dependency**: Requires internet connection and Claude API access
2. **Cost**: API usage has costs (mitigated by caching)
3. **Rate Limits**: Default 100 requests/hour (configurable)
4. **Analysis Accuracy**: AI may occasionally produce false positives/negatives
5. **Context Window**: Limited to ~200K tokens (Claude Sonnet 4)

## Future Enhancements

- **Local LLM Support**: Run models locally (no API costs)
- **Multi-Model Support**: Support for GPT-4, Gemini, etc.
- **Auto-Indexing**: Automatically index logs to vector DB
- **Threat Intelligence Integration**: Combine AI with threat intel APIs
- **Custom Prompts**: User-defined analysis prompts
- **Cost Budgets**: Automatic pause when budget exceeded

## Support

For issues or questions:
- Check logs: `%LOCALAPPDATA%\HifzDefend\logs\`
- Review config: `hifzdefend config-show`
- Report bugs: GitHub Issues
- Documentation: `docs/AI_INTEGRATION.md`

---

**HifzDefend v0.2.0** - AI-Powered Threat Analysis
