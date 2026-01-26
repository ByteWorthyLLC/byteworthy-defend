# HifzDefend Architecture

Technical architecture and design documentation for HifzDefend.

## System Overview

HifzDefend is a modular antivirus solution built on ClamAV with a focus on:
- **Modularity**: Loosely coupled components
- **Extensibility**: Easy to add new features
- **Testability**: Comprehensive test coverage
- **Security**: Defense-in-depth design
- **Performance**: Efficient resource usage

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  CLI (Click) │  │  Web UI      │  │   API        │      │
│  │   + Rich     │  │  (Phase 3)   │  │  (Phase 3)   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
┌─────────┴──────────────────┴──────────────────┴─────────────┐
│                     Application Layer                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Scan Engine (Orchestration)             │   │
│  │  • Scan coordination    • Filtering                  │   │
│  │  • Quarantine mgmt      • Report generation          │   │
│  └────────────────┬────────────────────┬─────────────────┘   │
│                   │                    │                     │
│  ┌────────────────┴───────┐  ┌─────────┴──────────────┐     │
│  │   Configuration        │  │   Monitoring           │     │
│  │   • TOML loader        │  │   • File watcher       │     │
│  │   • Pydantic models    │  │   • Scheduler          │     │
│  │   • Validation         │  │   (Phase 2)            │     │
│  └────────────────────────┘  └────────────────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                     Core Services                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  ClamAV Scanner │  │  Logging        │  │  Utilities  │ │
│  │  • TCP socket   │  │  • JSON logs    │  │  • Hashing  │ │
│  │  • File scan    │  │  • Audit trail  │  │  • Validation│ │
│  │  • Dir scan     │  │  • Rotation     │  │  • Helpers  │ │
│  └────────┬────────┘  └─────────────────┘  └─────────────┘ │
└───────────┼─────────────────────────────────────────────────┘
            │
┌───────────┴─────────────────────────────────────────────────┐
│                  External Dependencies                       │
│  ┌────────────────────┐          ┌─────────────────────┐    │
│  │   ClamAV Daemon    │          │   File System       │    │
│  │   (clamd)          │          │   • Scanned files   │    │
│  │   • Port 3310      │          │   • Quarantine      │    │
│  │   • Virus DB       │          │   • Logs/Reports    │    │
│  └────────────────────┘          └─────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. CLI Layer (`cli/`)

**Responsibility**: User interaction via command-line interface

**Components**:
- `commands.py`: Click command definitions
- Rich console output (progress bars, tables)

**Key Features**:
- Command routing
- Argument parsing
- Output formatting
- Error handling

**Dependencies**: Click, Rich, Core Services

### 2. Core Layer (`core/`)

**Responsibility**: Core business logic and ClamAV integration

#### 2.1 Scanner (`core/scanner.py`)

```python
class ClamAVScanner:
    """Low-level ClamAV integration."""

    def __init__(config: ClamAVConfig)
    def ping() -> bool
    def get_version() -> str
    def scan_file(path) -> ScanResult
    def scan_directory(path) -> List[ScanResult]
```

**Design Decisions**:
- Uses clamd Python library (network socket)
- Stateless connection (reconnects on failure)
- Context manager support for cleanup
- Returns typed ScanResult objects

#### 2.2 Engine (`core/engine.py`)

```python
class ScanEngine:
    """High-level scan orchestration."""

    def __init__(config: HifzDefendConfig)
    def scan_path(path) -> ScanReport
    def quarantine_file(path, threat) -> QuarantineEntry
    def should_scan_file(path) -> bool
```

**Design Decisions**:
- Orchestrates scanning workflow
- Applies filtering rules (size, extensions, paths)
- Manages quarantine operations
- Generates scan reports

### 3. Configuration Layer (`config/`)

**Responsibility**: Configuration management and validation

#### 3.1 Loader (`config/loader.py`)

```python
class HifzDefendConfig(BaseModel):
    clamav: ClamAVConfig
    scanning: ScanningConfig
    monitoring: MonitoringConfig
    logging: LoggingConfig
    reporting: ReportingConfig
    quarantine: QuarantineConfig
```

**Design Decisions**:
- Pydantic for type-safe validation
- TOML format (simpler than YAML, safer than JSON with comments)
- Hierarchical search order (env var → user config → defaults)
- Windows path expansion (`%LOCALAPPDATA%`)

#### 3.2 Validator (`config/validator.py`)

**Responsibility**: Advanced validation logic

- Directory existence checks
- Permission verification
- ClamAV connectivity validation

### 4. Reporting Layer (`reporting/`)

**Responsibility**: Logging and report generation

#### 4.1 Logger (`reporting/logger.py`)

```python
def setup_logger(name, config) -> Logger
def setup_audit_logger(config) -> Logger
def log_scan_event(logger, action, file_path, ...)
```

**Design Decisions**:
- JSON-structured logs (machine-readable)
- Rotating file handlers (10MB main, 50MB audit)
- Separate audit log (longer retention)
- Context fields (file_path, threat_name, hash, scan_id)

#### 4.2 Formatter (`reporting/formatter.py`)

```python
class ScanReport:
    def add_scanned_file(path, size)
    def add_threat(path, threat, hash, quarantined)
    def add_error(path, error)
    def to_dict() -> dict
    def to_json() -> str
    def to_text() -> str
```

**Design Decisions**:
- Immutable scan ID (UUID)
- Tracks scan duration
- Multiple output formats (JSON, text, HTML future)
- Embeds threat metadata

### 5. Monitoring Layer (`monitoring/`) - Phase 2

**Responsibility**: Real-time file system monitoring

**Planned Components**:
- `watcher.py`: Watchdog integration
- `scheduler.py`: Scheduled scans
- `service.py`: Windows service wrapper

### 6. Utilities Layer (`utils/`)

**Responsibility**: Cross-cutting utilities

#### 6.1 Exceptions (`utils/exceptions.py`)

Custom exception hierarchy:
```
HifzDefendError (base)
├── ConfigurationError
├── ScannerError
│   ├── ClamAVConnectionError
│   └── ClamAVTimeoutError
├── QuarantineError
├── ValidationError
│   └── PathTraversalError
└── FileAccessError
```

#### 6.2 Helpers (`utils/helpers.py`)

- `calculate_file_hash()`: SHA256 hashing
- `validate_path()`: Path traversal prevention
- `format_file_size()`: Human-readable sizes
- `expand_windows_path()`: Environment variable expansion

## Data Flow

### Scan Workflow

```
1. User Command
   │
   ├─→ hifzdefend scan /path
   │
2. CLI Layer
   │
   ├─→ Parse arguments
   ├─→ Load configuration
   ├─→ Setup logger
   │
3. Scan Engine
   │
   ├─→ Create ScanReport
   ├─→ Check ClamAV connection
   ├─→ Enumerate files
   │   │
   │   ├─→ Apply filters (size, extensions, paths)
   │   │
   │   └─→ For each file:
   │       │
   │       ├─→ ClamAV Scanner.scan_file()
   │       │   │
   │       │   ├─→ Send file path to clamd (TCP)
   │       │   ├─→ Receive scan result
   │       │   └─→ Return ScanResult
   │       │
   │       ├─→ If infected:
   │       │   ├─→ Calculate file hash
   │       │   ├─→ Quarantine (if auto_quarantine)
   │       │   │   ├─→ Generate UUID
   │       │   │   ├─→ Move file atomically
   │       │   │   └─→ Set read-only permissions
   │       │   └─→ Add to threats list
   │       │
   │       ├─→ Log scan event
   │       └─→ Add to ScanReport
   │
4. Report Generation
   │
   ├─→ Complete ScanReport
   ├─→ Save to disk (JSON)
   │
5. CLI Output
   │
   ├─→ Display results (Rich tables)
   └─→ Show quarantine status
```

### Quarantine Workflow

```
1. Threat Detected
   │
2. Pre-Quarantine
   │
   ├─→ Calculate SHA256 hash
   ├─→ Generate UUID quarantine ID
   │
3. Quarantine Operation
   │
   ├─→ Move file to quarantine dir
   │   (atomic operation via shutil.move)
   │
   ├─→ Rename to UUID.quarantined
   │
   ├─→ Set read-only (chmod 0444)
   │
4. Post-Quarantine
   │
   ├─→ Verify hash matches
   ├─→ Log quarantine event
   ├─→ Return QuarantineEntry
   │
5. Audit Trail
   │
   └─→ JSON log entry with:
       • original_path
       • quarantine_id
       • threat_name
       • file_hash
       • timestamp
```

## Design Patterns

### 1. Dependency Injection

Configuration injected into components:
```python
# Good: Testable, flexible
scanner = ClamAVScanner(config.clamav)
engine = ScanEngine(config)

# Bad: Hard-coded, not testable
scanner = ClamAVScanner("localhost", 3310)
```

### 2. Context Managers

Resource cleanup with `__enter__` / `__exit__`:
```python
with ScanEngine(config) as engine:
    report = engine.scan_path(path)
# Automatically closes ClamAV connection
```

### 3. Factory Pattern

Configuration loading:
```python
def get_config() -> HifzDefendConfig:
    """Factory for configuration singleton."""
    return load_config()
```

### 4. Strategy Pattern (Future)

Pluggable scan strategies:
```python
class ScanStrategy(ABC):
    @abstractmethod
    def scan(self, path: Path) -> ScanResult: ...

class ClamAVStrategy(ScanStrategy): ...
class WindowsDefenderStrategy(ScanStrategy): ...
```

### 5. Observer Pattern (Phase 2)

File system monitoring:
```python
class FileEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Notify scanner
        self.scanner.scan_file(event.src_path)
```

## Technology Stack

### Core Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.10+ | Application logic |
| AV Engine | ClamAV | Malware detection |
| Config | TOML + Pydantic | Type-safe configuration |
| CLI | Click + Rich | User interface |
| Logging | python-json-logger | Structured logs |
| Testing | pytest | Test framework |
| Code Quality | black, ruff, mypy | Formatting, linting, typing |

### Key Libraries

```toml
[dependencies]
clamd = "^1.0.2"           # ClamAV daemon interface
click = "^8.1.0"           # CLI framework
rich = "^13.0.0"           # Terminal UI
pydantic = "^2.0.0"        # Data validation
python-json-logger = "^2.0" # JSON logs
watchdog = "^3.0.0"        # File monitoring (Phase 2)
psutil = "^5.9.0"          # System utils
```

## Performance Considerations

### Bottlenecks

1. **ClamAV Scan Speed**
   - Solution: Parallel scanning (Phase 2 with `multiscan`)
   - Current: Sequential scanning

2. **Large File Handling**
   - Solution: Streaming to ClamAV (avoid loading into memory)
   - Current: ClamAV handles file I/O

3. **Network Latency**
   - Solution: Local UNIX socket (faster than TCP)
   - Current: TCP socket on localhost

### Optimizations

1. **File Filtering**
   ```python
   # Skip large files
   if file_size > max_file_size:
       return

   # Skip excluded paths
   if path in excluded_paths:
       return
   ```

2. **Connection Pooling** (Future)
   ```python
   # Reuse ClamAV connections
   connection_pool = ConnectionPool(size=5)
   ```

3. **Caching** (Future)
   ```python
   # Cache scan results by file hash
   if file_hash in scan_cache:
       return scan_cache[file_hash]
   ```

## Security Architecture

### Defense in Depth

1. **Input Layer**: Path validation, argument sanitization
2. **Application Layer**: Quarantine isolation, log parameterization
3. **System Layer**: File permissions, process isolation
4. **Audit Layer**: Comprehensive logging, integrity checks

### Trust Boundaries

```
User Input → Validation → Application Logic → ClamAV → Results
   [Low]       [Medium]        [High]         [High]    [Medium]
```

### Security Controls

| Control | Implementation |
|---------|---------------|
| Path Traversal | `Path.resolve()` + base path checking |
| Log Injection | Parameterized logging (no string concat) |
| Quarantine Escape | Read-only permissions + no execute |
| TOCTOU | File hash verification |
| Resource Exhaustion | File size limits + timeouts |

## Extensibility

### Adding New Commands

1. Add to `cli/commands.py`:
   ```python
   @cli.command()
   @click.argument("path")
   def newcommand(path: str):
       """New command description."""
       # Implementation
   ```

2. Add tests to `tests/test_cli/`

### Adding Scan Engines (Future)

```python
class ScanEngineFactory:
    @staticmethod
    def create(engine_type: str) -> ScanEngine:
        if engine_type == "clamav":
            return ClamAVEngine()
        elif engine_type == "defender":
            return DefenderEngine()
```

### Adding Output Formats

1. Add format to `ScanReport`:
   ```python
   def to_html(self) -> str:
       """Generate HTML report."""
       # Implementation
   ```

2. Update CLI to support new format

## Testing Strategy

### Test Pyramid

```
        ┌─────────────┐
        │ Integration │  (10%)
        │   Tests     │
        ├─────────────┤
        │    Unit     │  (70%)
        │   Tests     │
        ├─────────────┤
        │   Fixtures  │  (20%)
        │  & Mocks    │
        └─────────────┘
```

### Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: ClamAV integration, end-to-end workflows
3. **Mocked Tests**: Test without ClamAV dependency
4. **Security Tests**: Path traversal, injection attacks

## Future Enhancements

### Phase 2: Real-Time Monitoring
- Watchdog file system monitoring
- Background service (Windows service)
- Desktop notifications (win10toast)
- Scheduled scans (APScheduler)

### Phase 3: Web Dashboard
- FastAPI backend
- React frontend
- WebSocket real-time updates
- REST API for programmatic access

### Phase 4: Advanced Features
- Machine learning threat detection
- Cloud-based threat intelligence
- Multi-engine scanning (ClamAV + others)
- Behavioral analysis

## Deployment

### Development
```
- Python virtual environment
- ClamAV daemon (foreground)
- Development configuration
```

### Production (Future)
```
- Windows service (clamd + HifzDefend)
- System-wide configuration
- Centralized logging (e.g., Splunk)
- Monitoring dashboards
```

## Conclusion

HifzDefend's architecture prioritizes:
- **Modularity**: Easy to understand and extend
- **Security**: Multiple layers of protection
- **Testability**: Comprehensive test coverage
- **Performance**: Efficient resource usage
- **Maintainability**: Clean code and documentation

The phased approach allows incremental development while maintaining a solid foundation for future enhancements.
