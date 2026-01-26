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

## Phase 1.5: Event-Driven Architecture

### Overview

Phase 1.5 introduces a **publish-subscribe event bus** for coordinating 13 security monitors. This architecture enables:
- **Decoupled Monitors**: Monitors operate independently
- **Asynchronous Processing**: Non-blocking event handling
- **Scalability**: Easy to add new monitors
- **Resilience**: One monitor failure doesn't affect others

### Event Bus Design

```
┌─────────────────────────────────────────────────────────────┐
│                      User Activity                          │
│  (npm install, docker pull, file modified, etc.)           │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │   Monitor Manager     │
         │   (Orchestrator)      │
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐      ┌────▼────┐      ┌───▼───┐
│Monitor│      │Monitor  │      │Monitor│
│  #1   │      │   #2    │      │  #13  │
│(Package)     │(Docker) │      │(Hardware)
└───┬───┘      └────┬────┘      └───┬───┘
    │               │               │
    │   publish()   │   publish()   │
    └───────────────┼───────────────┘
                    │
         ┌──────────▼──────────┐
         │     Event Bus       │
         │  (Central Hub)      │
         │                     │
         │  • Event Queue      │
         │  • Subscribers      │
         │  • Priority Mgmt    │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  Event Processor    │
         │  (Async Worker)     │
         └──────────┬──────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
┌───▼────┐    ┌────▼────┐    ┌────▼────┐
│Handler │    │Handler  │    │Handler  │
│  #1    │    │   #2    │    │   #3    │
└───┬────┘    └────┬────┘    └────┬────┘
    │              │              │
    └──────────────┼──────────────┘
                   │
         ┌─────────▼─────────┐
         │  Response Actions │
         │  • Alert User     │
         │  • Quarantine     │
         │  • Block          │
         │  • Log            │
         └───────────────────┘
```

### Event Model

```python
class Event(BaseModel):
    """Immutable event object."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType  # THREAT_DETECTED, SUSPICIOUS_ACTIVITY, etc.
    timestamp: datetime
    severity: Literal["info", "warning", "critical"]
    source_monitor: str  # Monitor that generated event
    data: dict[str, Any]  # Event-specific data
    threat_score: int = Field(ge=0, le=100)  # 0-100 threat level
```

**Event Types**:
- `THREAT_DETECTED`: Malware or threat identified
- `SUSPICIOUS_ACTIVITY`: Unusual behavior detected
- `PROCESS_STARTED`: New process launched
- `FILE_MODIFIED`: File created/modified/deleted
- `NETWORK_CONNECTION`: Outbound network connection
- `REGISTRY_CHANGED`: Windows Registry modified
- `HARDWARE_ACCESS`: Webcam/microphone accessed
- `PACKAGE_INSTALLED`: npm/pip package installed
- `DOCKER_IMAGE_PULLED`: Docker image downloaded
- `DNS_QUERY`: DNS lookup performed

### Monitor Lifecycle

```
1. Initialization
   │
   ├─→ Create monitor instance
   ├─→ Inject config & event bus
   └─→ Register with MonitorManager

2. Startup
   │
   ├─→ MonitorManager.start_all()
   ├─→ Monitor.start() called
   └─→ Background check loop begins

3. Monitoring (Async Loop)
   │
   ├─→ await check()  # Perform detection logic
   ├─→ Generate events
   ├─→ Publish to event bus
   └─→ Sleep (check_interval)

4. Event Processing
   │
   ├─→ Event published to bus
   ├─→ Queued for processing
   ├─→ Subscribers notified
   └─→ Response actions executed

5. Shutdown
   │
   ├─→ MonitorManager.stop_all()
   ├─→ Monitor.stop() called
   └─→ Cleanup resources
```

### Monitor Design Pattern

Each monitor follows this pattern:

```python
class ExampleMonitor(BaseMonitor):
    """Example security monitor."""

    def __init__(self, config, event_bus):
        super().__init__(config, event_bus)
        self.name = "ExampleMonitor"
        self._running = False

    async def start(self):
        """Start monitoring loop."""
        self._running = True
        while self._running:
            events = await self.check()
            for event in events:
                self.publish_event(event)
            await asyncio.sleep(self.config.check_interval)

    async def stop(self):
        """Stop monitoring."""
        self._running = False

    async def check(self) -> list[Event]:
        """Perform detection logic."""
        events = []

        # Detection logic here
        suspicious_activity = self._detect_suspicious_activity()

        if suspicious_activity:
            event = Event(
                event_type=EventType.SUSPICIOUS_ACTIVITY,
                severity="warning",
                source_monitor=self.name,
                data=suspicious_activity,
                threat_score=self._calculate_threat_score(suspicious_activity)
            )
            events.append(event)

        return events
```

### Threat Scoring System

Composite score (0-100) from multiple factors:

```python
def calculate_threat_score(event_data: dict) -> int:
    score = 0

    # Signature match weight
    if event_data.get("signature_match"):
        score += 50

    # Behavior indicators
    if event_data.get("suspicious_behavior"):
        score += 30

    # Reputation (external APIs)
    reputation = event_data.get("reputation_score", 0)
    score += min(reputation, 20)

    # Context (location, time, user)
    if event_data.get("unusual_context"):
        score += 10

    return min(score, 100)
```

**Score Ranges**:
- **0-30**: Info - Log only
- **31-60**: Warning - Alert user
- **61-85**: High - Alert + Recommend action
- **86-100**: Critical - Alert + Auto-quarantine

### Performance Characteristics

**Resource Usage** (with all 13 monitors enabled):
- **CPU (Idle)**: <5% (average 2-3%)
- **CPU (Active)**: <15% (average 8-12%)
- **Memory**: ~150-200MB (includes cache)
- **Event Latency**: <100ms average, <200ms P95
- **Event Throughput**: >1,000 events/second

**Optimization Techniques**:
1. **Async I/O**: All monitors use asyncio (non-blocking)
2. **Event Queuing**: Batched event processing
3. **Caching**: Threat intelligence results cached
4. **Rate Limiting**: API calls throttled
5. **Selective Monitoring**: Disable unused monitors

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

### 5. Monitoring Layer (`monitoring/`) - Phase 1.5 (Implemented ✅)

**Responsibility**: Event-driven threat detection and behavior monitoring

**Architecture**: Event Bus Pattern (Publish-Subscribe)

#### 5.1 Event Bus (`monitoring/event_bus.py`)

Central hub for all monitor communication:

```python
class EventBus:
    """Central event bus for monitor coordination."""

    def __init__(self):
        self._subscribers: dict[EventType, list[Callable]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()

    def subscribe(self, event_type: EventType, callback: Callable)
    def publish(self, event: Event)
    async def process_events()
```

**Design Decisions**:
- Asynchronous event processing (asyncio)
- Priority-based event queue
- Type-safe event models (Pydantic)
- Multiple subscribers per event type
- Graceful error handling (one monitor failure doesn't crash others)

#### 5.2 Base Monitor (`monitoring/base.py`)

Abstract base class for all monitors:

```python
class BaseMonitor(ABC):
    """Abstract base class for security monitors."""

    def __init__(self, config: MonitorConfig, event_bus: EventBus)

    @abstractmethod
    async def start() -> None
    @abstractmethod
    async def stop() -> None
    @abstractmethod
    async def check() -> list[Event]

    def publish_event(self, event: Event)
```

#### 5.3 Implemented Monitors (13 Total)

**Developer Security**:
- `package_monitor.py`: npm/pip security (typosquatting, malicious packages)
- `docker_monitor.py`: Container security (Trivy integration)
- `ide_monitor.py`: VS Code extensions, Claude Code CLI

**Behavior-Based Detection**:
- `registry_monitor.py`: Windows Registry changes
- `powershell_monitor.py`: Script execution & obfuscation detection
- `ransomware_monitor.py`: File encryption patterns
- `cryptominer_monitor.py`: CPU/GPU mining activity

**Network & Privacy**:
- `network_monitor.py`: IP reputation, C2 beaconing
- `dns_monitor.py`: DNS filtering, tunneling detection
- `download_monitor.py`: Auto-scan downloads (VirusTotal)
- `spyware_monitor.py`: Keylogger & RAT detection
- `clipboard_monitor.py`: Crypto address hijacking
- `hardware_monitor.py`: Webcam/mic access alerts

#### 5.4 Monitor Manager (`monitoring/manager.py`)

Orchestrates monitor lifecycle:

```python
class MonitorManager:
    """Manages all security monitors."""

    def __init__(self, config: HifzDefendConfig)

    def register_monitor(self, monitor: BaseMonitor)
    async def start_all()
    async def stop_all()
    def get_status() -> dict
```

**Design Decisions**:
- Centralized monitor lifecycle management
- Independent monitor operation (failure isolation)
- Status reporting for all monitors
- Dynamic enable/disable of monitors

### 6. Rules Engine Layer (`rules/`) - Phase 1.5 (Implemented ✅)

**Responsibility**: Custom threat signatures and policy enforcement

#### 6.1 YARA Manager (`rules/yara_manager.py`)

```python
class YARAManager:
    """YARA rules compilation and matching."""

    def compile_rules(self, rules_dir: Path)
    def scan_with_rules(self, file_path: Path) -> list[RuleMatch]
```

#### 6.2 File Blocker (`rules/file_blocker.py`)

Context-aware file blocking:

```python
class FileBlocker:
    """Block files based on type, location, and context."""

    def should_block_file(self, file_path: Path) -> bool
    def check_context(self, file_path: Path) -> BlockContext
```

#### 6.3 Application Whitelist (`rules/app_whitelist.py`)

```python
class ApplicationWhitelist:
    """Trusted application verification."""

    def is_whitelisted_app(self, file_path: Path) -> bool
    def verify_signature(self, file_path: Path) -> bool
    def check_file_hash(self, file_path: Path) -> bool
```

### 7. Threat Intelligence Layer (`threat_intel/`) - Phase 1.5 (Implemented ✅)

**Responsibility**: External threat intelligence integration

#### 7.1 API Clients (`threat_intel/api_clients.py`)

Integrations:
- **AbuseIPDB**: IP reputation
- **VirusTotal**: File/URL reputation
- **Snyk**: Package vulnerabilities
- **Socket.dev**: Supply chain security

#### 7.2 Threat Intel Cache (`threat_intel/cache.py`)

```python
class ThreatIntelCache:
    """Cache threat intelligence results."""

    def get(self, key: str) -> Optional[dict]
    def set(self, key: str, value: dict, ttl: int)
    def clear()
```

**Design Decisions**:
- SQLite backend for persistence
- TTL-based expiration
- LRU eviction policy
- Rate limit tracking

### 8. Utilities Layer (`utils/`)

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

#### Phase 1 Dependencies
```toml
[dependencies]
clamd = "^1.0.2"           # ClamAV daemon interface
click = "^8.1.0"           # CLI framework
rich = "^13.0.0"           # Terminal UI
pydantic = "^2.0.0"        # Data validation
python-json-logger = "^2.0" # JSON logs
watchdog = "^3.0.0"        # File monitoring
psutil = "^5.9.0"          # System utils
```

#### Phase 1.5 Dependencies (Advanced Threat Detection)
```toml
# Custom Rules & Signatures
yara-python = "^4.5.0"     # YARA rules engine
scapy = "^2.5.0"           # Network packet analysis

# Container Security
docker = "^7.0.0"          # Docker API client

# Threat Intelligence
requests = "^2.31.0"       # HTTP requests
aiohttp = "^3.9.0"         # Async HTTP client

# Network Monitoring
dnspython = "^2.4.0"       # DNS monitoring

# System Monitoring
pynput = "^1.7.6"          # Input device monitoring
opencv-python = "^4.8.0"   # Webcam detection
pyaudio = "^0.2.14"        # Microphone detection

# Windows APIs
python-registry = "^1.3.1" # Registry access
wmi = "^1.5.1"             # Windows Management Instrumentation
pywin32 = "^306"           # Windows API access

# Security
cryptography = "^41.0.0"   # Signature verification
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

## Completed Phases

### ✅ Phase 1: Core Scanning (v0.1.0)
- ClamAV integration
- File/directory scanning
- Quarantine management
- Configuration system
- Structured logging

### ✅ Phase 1.5: Advanced Threat Detection (v0.1.5)
- Event-driven architecture (Event Bus)
- 13 Security monitors
- YARA custom signatures
- Threat intelligence integration
- Behavior-based detection
- Network security monitoring
- Privacy protection

## Future Enhancements

### Phase 2: Real-Time Service (v0.2.0)
- **Windows Background Service**: Run as system service
- **System Tray Integration**: Status icon and quick actions
- **Desktop Notifications**: Real-time alerts (win10toast)
- **Scheduled Scans**: APScheduler integration
- **Auto-Update Definitions**: Automatic ClamAV database updates
- **Service Management**: Start/stop/restart from CLI/tray

### Phase 3: Web Dashboard (v0.3.0)
- **FastAPI Backend**: RESTful API
- **React Frontend**: Modern web UI
- **WebSocket Updates**: Real-time statistics
- **Threat Report Viewer**: Interactive threat analysis
- **Configuration UI**: Web-based settings management
- **Remote Monitor Control**: Enable/disable monitors remotely

### Phase 4: Advanced Features (v1.0.0+)
- **Machine Learning**: Behavior-based threat detection
- **Multi-Engine Scanning**: ClamAV + Windows Defender integration
- **Cloud Threat Intelligence**: Real-time global threat feed
- **Heuristic Analysis**: Zero-day threat detection
- **Code Signing**: Signed executables and updates
- **Telemetry**: Opt-in usage statistics

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
