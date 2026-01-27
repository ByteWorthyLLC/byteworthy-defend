# HifzDefend

**حفظ (Hifz) - Protection/Preservation**

> Preserving Your Digital Safety

HifzDefend is a custom Windows antivirus solution built on top of ClamAV, featuring a modern CLI interface, structured logging, quarantine management, and extensible architecture for real-time monitoring and web-based dashboards.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Features

### Phase 1: MVP ✅
- **CLI Scanner**: Scan files and directories for malware
- **ClamAV Integration**: Enterprise-grade virus detection engine
- **Quarantine Management**: Automatic quarantine of detected threats
- **Structured Logging**: JSON-formatted logs with rotation
- **Configuration System**: TOML-based config with Pydantic validation
- **Rich Terminal Output**: Beautiful progress bars and tables
- **EICAR Test Support**: Safe malware testing with encrypted samples

### Phase 2: Web Application ✅ (v0.2.0)
- **FastAPI Backend**: REST API with async support
- **React TypeScript Frontend**: Modern, responsive web UI
- **Real-time Dashboard**: Live statistics and threat timeline
- **Scan Management**: Start and monitor scans from web browser
- **Quarantine UI**: Manage quarantined files with restore/delete
- **Settings Panel**: Configure scanning and quarantine options
- **WebSocket Support**: Real-time updates (infrastructure ready)

### Phase 3: Real-Time Monitoring (Planned)
- File system monitoring with watchdog
- Auto-scan on file creation/modification
- Desktop notifications
- Scheduled scans
- Automatic virus definition updates

## Quick Start

### Prerequisites
- Windows 10/11
- Python 3.10 or higher
- ClamAV Windows installation
- Git (optional, for development)

### Installation

1. **Install ClamAV** (see [INSTALLATION.md](docs/INSTALLATION.md) for details)
   ```powershell
   # Download from https://www.clamav.net/downloads
   # Install to C:\Program Files\ClamAV
   ```

2. **Clone or Download HifzDefend**
   ```bash
   git clone <repository-url>
   cd HifzDefend
   ```

3. **Run Bootstrap Script**
   ```bash
   python scripts/bootstrap_dev.py
   ```

4. **Activate Virtual Environment**
   ```powershell
   .venv\Scripts\activate
   ```

5. **Set Up Windows Defender Exclusions** (Administrator PowerShell)
   ```powershell
   .\scripts\setup_defender_exclusions.ps1
   ```

6. **Start ClamAV Daemon**
   ```powershell
   cd "C:\Program Files\ClamAV"
   .\clamd.exe
   ```

7. **Verify Installation**
   ```bash
   hifzdefend --version
   hifzdefend status
   ```

## Usage

### Web Application (NEW in v0.2.0)

Start the web application with a single command:

```bash
hifzdefend web
```

This will:
- Start the FastAPI backend server
- Serve the React frontend
- Automatically open your browser to http://localhost:8000

**Web Features:**
- **Dashboard**: Real-time statistics and threat timeline
- **Scan Management**: Start scans and monitor progress
- **Quarantine**: Manage quarantined files
- **Settings**: Configure scanning and quarantine options

**Options:**
```bash
hifzdefend web --host 0.0.0.0 --port 8000  # Custom host/port
hifzdefend web --reload                    # Enable auto-reload for development
```

### CLI Commands

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
HifzDefend
├── Core Scanner (ClamAV Integration)
├── Configuration System (TOML + Pydantic)
├── Logging (JSON Structured Logs)
├── Scan Engine (Orchestration + Quarantine)
├── CLI Interface (Click + Rich)
└── Testing (Pytest + EICAR)
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

- [Installation Guide](docs/INSTALLATION.md) - Detailed setup instructions
- [Usage Guide](docs/USAGE.md) - Complete CLI reference and examples
- [Development Guide](docs/DEVELOPMENT.md) - Contributing and development workflow
- [Architecture Guide](docs/ARCHITECTURE.md) - System design and components
- [Security Guide](docs/SECURITY.md) - Security considerations and best practices

## Roadmap

- [x] **v0.1.0** - MVP CLI Scanner (Phase 1)
  - [x] ClamAV integration
  - [x] File/directory scanning
  - [x] Quarantine management
  - [x] Configuration system
  - [x] Structured logging
  - [x] Test suite

- [ ] **v0.2.0** - Real-Time Monitoring (Phase 2)
  - [ ] File system monitoring
  - [ ] Auto-scan on file events
  - [ ] Desktop notifications
  - [ ] Scheduled scans
  - [ ] Auto-update definitions

- [ ] **v0.3.0** - Web Dashboard (Phase 3)
  - [ ] REST API backend
  - [ ] Web UI (React)
  - [ ] Real-time statistics
  - [ ] Report viewer
  - [ ] Configuration UI

- [ ] **v1.0.0** - Production Ready
  - [ ] Performance optimization
  - [ ] Windows service
  - [ ] Installer package
  - [ ] Documentation site
  - [ ] CI/CD pipeline

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
