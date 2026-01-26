# HifzDefend

**حفظ (Hifz) - Protection/Preservation**

> Preserving Your Digital Safety

HifzDefend is a custom Windows antivirus solution built on top of ClamAV, featuring a modern CLI interface, structured logging, quarantine management, and extensible architecture for real-time monitoring and web-based dashboards.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Features

### Phase 1: Core Scanning (Complete ✅)
- **CLI Scanner**: Scan files and directories for malware
- **ClamAV Integration**: Enterprise-grade virus detection engine
- **Quarantine Management**: Automatic quarantine of detected threats
- **Structured Logging**: JSON-formatted logs with rotation
- **Configuration System**: TOML-based config with Pydantic validation
- **Rich Terminal Output**: Beautiful progress bars and tables
- **EICAR Test Support**: Safe malware testing with encrypted samples

### Phase 1.5: Advanced Threat Detection (Complete ✅)
**Developer Security:**
- 🛡️ **Package Manager Security**: npm/pip typosquatting & malicious package detection
- 🐳 **Docker Security**: Container vulnerability scanning with Trivy
- 💻 **IDE Monitoring**: VS Code extension security & Claude Code CLI protection
- 📦 **Supply Chain Protection**: Dependency confusion prevention

**Behavior-Based Detection:**
- 📋 **Registry Monitor**: Windows Registry change tracking & rollback
- ⚡ **PowerShell Monitor**: Malicious script & obfuscation detection
- 🔒 **Ransomware Detection**: File encryption pattern detection & auto-backup
- ⛏️ **Crypto-Miner Detection**: CPU/GPU mining activity detection

**Network & Privacy:**
- 🌐 **Network Monitor**: IP reputation & C2 beaconing detection
- 🔍 **DNS Monitor**: DNS filtering & tunneling detection
- 📥 **Download Monitor**: Auto-scan browser downloads with VirusTotal
- 🕵️ **Spyware Detection**: Keylogger & RAT detection
- 📋 **Clipboard Monitor**: Crypto address hijacking prevention
- 📷 **Hardware Monitor**: Webcam/microphone access alerts

**Custom Rules & Intelligence:**
- 📜 **YARA Rules Engine**: Custom malware signatures
- 🎯 **File Blocking**: Context-aware file type blocking
- ✅ **Application Whitelist**: Trusted app verification
- 🌍 **Threat Intelligence**: AbuseIPDB, VirusTotal, Snyk, Socket.dev integration

### Phase 2: AI Integration (Complete ✅) - **NEW in v0.2.0** 🎉
- 🤖 **Claude-Powered Threat Analysis**: Script analysis with plain language explanations
- 💬 **Natural Language Queries**: Ask questions about security logs in plain English
- 🧠 **RAG on Security Logs**: Semantic search over logs using ChromaDB
- 📊 **Incident Report Generation**: Auto-generate human-readable incident reports
- 💰 **Cost Management**: Response caching (90% savings), rate limiting, cost tracking
- 🎯 **Improved Error Messages**: 350% more helpful with built-in troubleshooting
- 📚 **Demo Content**: 11 example files with 230+ ready-to-use queries
- 🔒 **Security Audited**: Zero vulnerabilities found (Grade A+)

### Phase 3: Real-Time Service (Planned)
- Windows background service
- System tray integration
- Desktop notifications
- Scheduled scans
- Auto-update virus definitions

### Phase 3: Web Dashboard (Planned)
- REST API backend
- Real-time scan statistics
- Historical threat reports
- Configuration management UI
- Quarantine management interface

## Quick Start

### Prerequisites
- Windows 10/11
- Python 3.10 or higher
- ClamAV Windows installation (optional for basic features)
- Claude API key (optional for AI features)
- Git (optional, for development)

### Installation

#### 🚀 **Automated Installation** (Recommended)

```powershell
# Clone repository
git clone <repository-url>
cd HifzDefend

# Run automated setup script
.\scripts\setup.ps1

# Activate virtual environment
.venv\Scripts\activate

# Set Claude API key (optional, for AI features)
$env:CLAUDE_API_KEY = "sk-ant-api03-..."

# Verify installation
hifzdefend --version
hifzdefend status
hifzdefend ai test
```

**That's it!** The setup script handles:
- Virtual environment creation
- Dependency installation
- Configuration setup
- Installation verification

#### 📖 **Manual Installation**

1. **Install ClamAV** (optional - see [INSTALLATION.md](docs/INSTALLATION.md))
   ```powershell
   # Download from https://www.clamav.net/downloads
   # Install to C:\Program Files\ClamAV
   ```

2. **Clone HifzDefend**
   ```bash
   git clone <repository-url>
   cd HifzDefend
   ```

3. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

4. **Install Dependencies**
   ```bash
   # Core dependencies
   pip install -r requirements.txt

   # AI dependencies (optional)
   pip install anthropic chromadb sentence-transformers
   ```

5. **Set API Key** (optional, for AI features)
   ```powershell
   # Get key from: https://console.anthropic.com/settings/keys
   $env:CLAUDE_API_KEY = "sk-ant-api03-..."
   ```

6. **Verify Installation**
   ```bash
   hifzdefend --version
   hifzdefend status
   hifzdefend ai test
   ```

**First Time?** See [Quick Start Guide](docs/QUICKSTART.md) for a 5-minute walkthrough.

## Usage

### Scan a File
```bash
hifzdefend scan path/to/file.exe
```

### Scan a Directory
```bash
hifzdefend scan C:\Users\YourName\Downloads
```

### Check System Status
```bash
hifzdefend status
```

### Update Virus Definitions
```bash
hifzdefend update
```

### Quarantine Management
```bash
# List quarantined files
hifzdefend list-quarantine

# Manually quarantine a file
hifzdefend quarantine path/to/suspicious.exe --threat-name "Suspicious.File"
```

### View Configuration
```bash
hifzdefend config-show
```

### AI-Powered Analysis (Phase 2) - **NEW in v0.2.0** 🎉

#### Analyze Scripts with Claude AI
```bash
# Analyze PowerShell script
hifzdefend analyze-script suspicious.ps1

# Analyze with specific type
hifzdefend analyze-script malware.bat --type batch

# Save analysis report
hifzdefend analyze-script script.py --save

# Try example scripts
hifzdefend analyze-script examples\scripts\suspicious_download.ps1
```

#### Natural Language Queries
```bash
# Ask questions about security logs in plain English
hifzdefend query "what threats were detected today?"
hifzdefend query "show me all PowerShell alerts"
hifzdefend query "summarize today's security events"

# Interactive query mode
hifzdefend query --interactive

# Try example queries (230+ included)
Get-Content examples\queries\basic_queries.txt | Select-Object -First 5
```

#### Cost Management
```bash
# Monitor AI costs
hifzdefend ai cost           # Detailed breakdown
hifzdefend ai stats          # Usage statistics
hifzdefend ai cache-stats    # Cache performance

# Cost estimates: ~$1-10/month for typical use (with caching)
```

#### Explain Threats
```bash
# Get plain language explanation
hifzdefend explain THR-001
hifzdefend explain "Trojan.Win32.Generic"
```

#### Run Example Workflows
```bash
# Daily security check
cd examples\workflows
.\daily_security_check.ps1

# Analyze downloads folder
.\analyze_downloads.ps1

# Batch analysis
.\batch_analysis.ps1 -Path C:\Downloads
```

## Configuration

Configuration file location: `%LOCALAPPDATA%\HifzDefend\hifzdefend.toml`

Example configuration:
```toml
[clamav]
host = "localhost"
port = 3310
timeout = 60

[scanning]
max_file_size = 104857600  # 100 MB
scan_archives = true
excluded_paths = [
    "C:\\Windows\\System32",
]

[quarantine]
enabled = true
auto_quarantine = true
```

See [config/hifzdefend.toml.example](config/hifzdefend.toml.example) for full configuration options.

## Architecture

```
HifzDefend (Phase 2)
├── Core Scanner
│   ├── ClamAV Integration
│   ├── Quarantine Management
│   └── Scan Engine
│
├── AI Integration (NEW - Phase 2)
│   ├── Claude Analyzer
│   │   ├── Script Analysis
│   │   ├── Network Behavior Analysis
│   │   ├── Incident Report Generation
│   │   └── Plain Language Explanations
│   ├── Natural Language Interface
│   │   ├── ChromaDB Vector Store
│   │   ├── Semantic Search (RAG)
│   │   └── Interactive Query Mode
│   └── Response Cache
│       ├── TTL-based Expiration
│       └── Cost Optimization
│
├── Event-Driven Monitoring
│   ├── Event Bus (Central Hub)
│   ├── 13 Security Monitors
│   │   ├── Package Manager (npm/pip)
│   │   ├── Docker Security
│   │   ├── IDE & Code Editor
│   │   ├── Registry Monitor
│   │   ├── PowerShell Monitor
│   │   ├── Ransomware Detector
│   │   ├── Crypto-Miner Detector
│   │   ├── Network Monitor
│   │   ├── DNS Monitor
│   │   ├── Download Monitor
│   │   ├── Spyware Detector
│   │   ├── Clipboard Monitor
│   │   └── Hardware Monitor
│   └── Monitor Manager
│
├── Custom Rules Engine
│   ├── YARA Integration
│   ├── File Blocker
│   └── App Whitelist
│
├── Threat Intelligence
│   ├── AbuseIPDB (IP reputation)
│   ├── VirusTotal (file reputation)
│   ├── Snyk (package vulnerabilities)
│   ├── Socket.dev (supply chain)
│   └── Threat Intel Cache
│
├── Configuration System
│   └── TOML + Pydantic Validation
│
├── CLI Interface
│   └── Click + Rich (30 commands)
│
└── Testing
    ├── Unit Tests (85%+ coverage)
    ├── Integration Tests
    ├── Performance Benchmarks
    └── False Positive Tests
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design documentation.

## Development

### Setup Development Environment
```bash
# Clone with submodules
git clone --recurse-submodules <repository-url>
cd HifzDefend

# Run bootstrap
python scripts/bootstrap_dev.py

# Activate venv
.venv\Scripts\activate

# Install pre-commit hooks
pre-commit install
```

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=hifzdefend --cov-report=html

# Integration tests only
pytest tests/integration/

# Skip slow tests
pytest -m "not slow"
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run all pre-commit hooks
pre-commit run --all-files
```

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development guidelines.

## Security Considerations

### Windows Defender Exclusions
HifzDefend requires Windows Defender exclusions for development and testing. These exclusions reduce system security and should only be used in development environments.

**Remove exclusions when done:**
```powershell
.\scripts\setup_defender_exclusions.ps1 -Remove
```

### EICAR Test Files
HifzDefend uses EICAR test files for malware detection testing. These are harmless test patterns recognized by all antivirus software. They are stored encrypted and never committed to the repository in plaintext.

### Secure Coding
- Input validation (path traversal prevention)
- Parameterized logging (injection prevention)
- Read-only quarantine files
- Atomic file operations
- Regular dependency audits

See [SECURITY.md](docs/SECURITY.md) for comprehensive security documentation.

## Documentation

**Getting Started:**
- [Installation Guide](docs/INSTALLATION.md) - Detailed setup instructions & API keys
- [Usage Guide](docs/USAGE.md) - Complete CLI reference (30 commands)

**Phase 2 - AI Integration:**
- [AI Integration Guide](docs/AI_INTEGRATION.md) - Claude setup, usage, and cost management

**Phase 1.5 - Advanced Features:**
- [Threat Detection Guide](docs/THREAT_DETECTION.md) - How each detection mechanism works
- [Customization Guide](docs/CUSTOMIZATION.md) - Custom YARA rules & whitelisting
- [Developer Security](docs/DEVELOPER_SECURITY.md) - Protecting your development workflow
- [API Integrations](docs/API_INTEGRATIONS.md) - Threat intelligence service setup

**Development:**
- [Development Guide](docs/DEVELOPMENT.md) - Contributing and development workflow
- [Architecture Guide](docs/ARCHITECTURE.md) - Event bus design & monitor patterns
- [Security Guide](docs/SECURITY.md) - Security considerations and best practices
- [Testing Guide](docs/TESTING.md) - Writing tests & running benchmarks

## Roadmap

- [x] **v0.1.0** - MVP CLI Scanner (Phase 1) ✅
  - [x] ClamAV integration
  - [x] File/directory scanning
  - [x] Quarantine management
  - [x] Configuration system
  - [x] Structured logging
  - [x] Test suite

- [x] **v0.1.5** - Advanced Threat Detection (Phase 1.5) ✅
  - [x] 13 Security monitors (Package, Docker, IDE, Registry, PowerShell, etc.)
  - [x] Event-driven architecture with Event Bus
  - [x] YARA custom signatures & rules engine
  - [x] Threat intelligence integration (AbuseIPDB, VirusTotal, Snyk, Socket.dev)
  - [x] Behavior-based detection (ransomware, crypto-miners, spyware)
  - [x] Network security (DNS filtering, IP blocking)
  - [x] Privacy protection (clipboard monitor, hardware access alerts)
  - [x] Comprehensive test suite (unit, integration, performance, false positives)
  - [x] Enhanced documentation (4 new guides)

- [x] **v0.2.0** - AI Integration (Phase 2) ✅
  - [x] Claude-powered threat analyzer
  - [x] Script analysis (PowerShell, Batch, Python)
  - [x] Network behavior analysis
  - [x] Natural language query interface
  - [x] RAG on security logs (ChromaDB)
  - [x] Plain language explanations
  - [x] Incident report generation
  - [x] Response caching & cost management
  - [x] CLI commands (query, analyze-script, explain)

- [ ] **v0.3.0** - Real-Time Service (Phase 3)
  - [ ] Windows background service
  - [ ] System tray integration
  - [ ] Desktop notifications
  - [ ] Scheduled scans
  - [ ] Auto-update definitions
  - [ ] Service management (start/stop/restart)

- [ ] **v0.4.0** - Web Dashboard (Phase 4)
  - [ ] REST API backend (FastAPI)
  - [ ] Web UI (React)
  - [ ] Real-time statistics & charts
  - [ ] Threat report viewer
  - [ ] Configuration management UI
  - [ ] Remote monitor control
  - [ ] AI chat interface

- [ ] **v1.0.0** - Production Ready
  - [ ] Performance optimization (<3% CPU idle)
  - [ ] Windows installer (NSIS/Inno Setup)
  - [ ] Auto-updater
  - [ ] Documentation website
  - [ ] CI/CD pipeline (GitHub Actions)
  - [ ] Code signing
  - [ ] Telemetry (opt-in)

## Contributing

Contributions are welcome! Please read [DEVELOPMENT.md](docs/DEVELOPMENT.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and code quality checks
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **ClamAV** - Open-source antivirus engine
- **EICAR** - Standard Anti-Virus test file
- **Python Community** - Amazing libraries and tools

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the [documentation](docs/)
- Review [SECURITY.md](docs/SECURITY.md) for security concerns

---

**HifzDefend** - حفظ - Preserving Your Digital Safety
