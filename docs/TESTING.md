# HifzDefend Testing Guide

Comprehensive guide to testing infrastructure, running tests, and writing new tests for HifzDefend.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Performance Goals](#performance-goals)
- [Continuous Integration](#continuous-integration)

---

## Testing Philosophy

HifzDefend follows a comprehensive testing approach:

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test components working together
3. **Performance Benchmarks** - Verify system meets performance goals
4. **False Positive Tests** - Ensure legitimate activity isn't flagged

### Testing Goals

- **Coverage**: 85%+ code coverage
- **Performance**: <5% CPU idle, <15% CPU active, <100ms event processing
- **Reliability**: <1% false positive rate
- **Safety**: All tests use mocking or safe test data (EICAR, not real malware)

---

## Test Structure

```
tests/
├── __init__.py
├── test_scanning/              # Unit tests for scanning components
│   ├── test_scanner.py
│   └── test_engine.py
├── test_monitoring/            # Unit tests for monitors
│   ├── test_event_bus.py
│   ├── test_base_monitor.py
│   ├── test_package_monitor.py
│   ├── test_docker_monitor.py
│   ├── test_registry_monitor.py
│   └── ... (one file per monitor)
├── test_rules/                 # Unit tests for rules engine
│   ├── test_rules_engine.py
│   ├── test_yara_manager.py
│   └── test_file_blocker.py
├── test_threat_intel/          # Unit tests for threat intelligence
│   ├── test_api_clients.py
│   ├── test_cache.py
│   └── test_manager.py
├── test_cli/                   # CLI command tests
│   └── test_commands.py
├── test_integration/           # Integration tests
│   ├── test_monitor_integration.py
│   └── test_end_to_end.py
└── benchmarks/                 # Performance & quality tests
    ├── test_performance.py     # CPU, memory, latency benchmarks
    └── test_false_positives.py # False positive rate tests
```

---

## Running Tests

### Prerequisites

```bash
# Install dev dependencies
pip install -e ".[dev]"
```

### Quick Test Commands

```bash
# Run all unit tests (fast, excludes slow tests)
python scripts/run_tests.py unit

# Run integration tests
python scripts/run_tests.py integration

# Run performance benchmarks
python scripts/run_tests.py benchmarks

# Run false positive tests
python scripts/run_tests.py false-pos

# Run all tests
python scripts/run_tests.py all

# Run with coverage report
python scripts/run_tests.py coverage
```

### Direct Pytest Commands

```bash
# Run specific test file
pytest tests/test_monitoring/test_event_bus.py -v

# Run specific test class
pytest tests/test_monitoring/test_event_bus.py::TestEventBus -v

# Run specific test method
pytest tests/test_monitoring/test_event_bus.py::TestEventBus::test_publish_event -v

# Run tests matching pattern
pytest -k "package_monitor" -v

# Run with markers
pytest -m "integration" -v          # Integration tests only
pytest -m "not slow" -v             # Exclude slow tests
pytest -m "benchmark" -v -s         # Benchmarks with output

# Run with coverage
pytest --cov=src/hifzdefend --cov-report=html
# View report: htmlcov/index.html
```

### Test Markers

Tests are categorized with markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower)
- `@pytest.mark.benchmark` - Performance benchmarks
- `@pytest.mark.slow` - Slow-running tests (excluded by default)
- `@pytest.mark.asyncio` - Tests using asyncio
- `@pytest.mark.requires_admin` - Requires administrator privileges
- `@pytest.mark.requires_docker` - Requires Docker running
- `@pytest.mark.requires_api_keys` - Requires external API keys

---

## Writing Tests

### Unit Test Example

```python
"""Test package monitor functionality."""

from unittest.mock import MagicMock, patch

import pytest

from hifzdefend.monitoring.package_monitor import PackageMonitor
from hifzdefend.monitoring.event_bus import EventBus, EventType


class TestPackageMonitor:
    """Test PackageMonitor class."""

    def test_initialization(self):
        """Test monitor initializes correctly."""
        config = MagicMock()
        event_bus = EventBus()

        monitor = PackageMonitor(config, event_bus)

        assert monitor.name == "PackageMonitor"
        assert monitor._running is False

    @pytest.mark.asyncio
    async def test_detect_npm_install(self):
        """Test detecting npm install command."""
        config = MagicMock()
        event_bus = EventBus()
        monitor = PackageMonitor(config, event_bus)

        # Mock process detection
        with patch("psutil.process_iter") as mock_processes:
            mock_process = MagicMock()
            mock_process.cmdline.return_value = ["npm", "install", "lodash"]
            mock_processes.return_value = [mock_process]

            events = await monitor.check()

        # Verify event generated
        assert len(events) == 1
        assert events[0].event_type == EventType.PACKAGE_INSTALLED
        assert events[0].data["package"] == "lodash"
```

### Integration Test Example

```python
"""Test monitor integration."""

import asyncio

import pytest

from hifzdefend.config.loader import HifzDefendConfig
from hifzdefend.monitoring.manager import MonitorManager


class TestMonitorIntegration:
    """Test monitors working together."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_monitors_communicate(self):
        """Test monitors communicate via event bus."""
        config = HifzDefendConfig.model_validate({
            "clamav": {"database_path": "/tmp/test"},
            "scanning": {"max_file_size_mb": 100},
            "logging": {"level": "INFO"},
            "monitoring": {
                "enabled": True,
                "package_manager": {"enabled": True},
                "docker": {"enabled": True},
            },
        })

        manager = MonitorManager(config)

        # Track events
        events_received = []

        def event_handler(event):
            events_received.append(event)

        manager.event_bus.subscribe(EventType.THREAT_DETECTED, event_handler)

        # Start monitors
        await manager.start_all()
        await asyncio.sleep(2)
        await manager.stop_all()

        # Verify system operational
        assert manager.event_bus is not None
```

### Performance Benchmark Example

```python
"""Performance benchmark test."""

import psutil
import pytest

from hifzdefend.monitoring.manager import MonitorManager


class TestPerformance:
    """Performance benchmark tests."""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    @pytest.mark.slow
    async def test_idle_cpu_usage(self):
        """Verify CPU usage <5% when idle."""
        config = # ... create config

        manager = MonitorManager(config)
        process = psutil.Process()

        await manager.start_all()
        await asyncio.sleep(2)

        # Measure CPU
        cpu_samples = []
        for _ in range(10):
            cpu_percent = process.cpu_percent(interval=1.0)
            cpu_samples.append(cpu_percent)

        await manager.stop_all()

        avg_cpu = sum(cpu_samples) / len(cpu_samples)

        # Assert performance goal
        assert avg_cpu < 5.0, f"CPU {avg_cpu:.2f}% exceeds 5% limit"
```

### Mocking Best Practices

**DO:**
- Mock external services (APIs, file system, registry)
- Mock slow operations (network calls, database queries)
- Use `AsyncMock` for async functions
- Clean up mocks after tests

```python
from unittest.mock import AsyncMock, MagicMock, patch

# Mock async function
mock_api = AsyncMock(return_value={"status": "success"})

# Mock with context manager
with patch("module.function") as mock_func:
    mock_func.return_value = "test_value"
    # ... test code ...
```

**DON'T:**
- Mock core logic being tested
- Create overly complex mock setups
- Forget to verify mock calls

---

## Performance Goals

### CPU Usage Benchmarks

| State | Target | Acceptable | Alert |
|-------|--------|------------|-------|
| Idle (no activity) | <3% | <5% | >5% |
| Active monitoring | <10% | <15% | >15% |
| Scanning file | <40% | <60% | >60% |

### Memory Usage Benchmarks

| State | Target | Acceptable | Alert |
|-------|--------|------------|-------|
| Baseline | <50MB | <100MB | >100MB |
| Active monitoring | <100MB | <200MB | >200MB |
| During scan | <300MB | <500MB | >500MB |

### Event Processing Benchmarks

| Metric | Target | Acceptable | Alert |
|--------|--------|------------|-------|
| Average latency | <50ms | <100ms | >100ms |
| P95 latency | <100ms | <200ms | >200ms |
| Throughput | >1000/s | >500/s | <500/s |

### Quality Benchmarks

| Metric | Target | Acceptable | Alert |
|--------|--------|------------|-------|
| False positive rate | <0.5% | <1% | >1% |
| False negative rate | <1% | <2% | >2% |
| Test coverage | >90% | >85% | <85% |

---

## Test Data

### Safe Malware Testing

**NEVER use real malware in tests.** Always use:

1. **EICAR Test File** - Standard antivirus test file
   ```python
   EICAR_STRING = (
       "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
   )
   ```

2. **Mock Data** - Simulated threat indicators
   ```python
   mock_threat = {
       "file_hash": "a" * 64,
       "threat_type": "test_malware",
       "severity": "critical",
   }
   ```

3. **Isolated Test Environment** - Use temporary directories
   ```python
   import tempfile
   from pathlib import Path

   with tempfile.TemporaryDirectory() as tmpdir:
       test_file = Path(tmpdir) / "test.exe"
       test_file.write_text("safe test content")
       # ... run test ...
   ```

### Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
@pytest.fixture
def test_config():
    """Minimal test configuration."""
    return HifzDefendConfig.model_validate({
        "clamav": {"database_path": "/tmp/test"},
        "scanning": {"max_file_size_mb": 100},
        "logging": {"level": "INFO"},
    })

@pytest.fixture
def event_bus():
    """Event bus for testing."""
    bus = EventBus()
    yield bus
    # Cleanup
    asyncio.run(bus.stop())
```

---

## Continuous Integration

### GitHub Actions Workflow

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Nightly builds

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e ".[dev]"

    - name: Run unit tests
      run: |
        python scripts/run_tests.py unit

    - name: Run integration tests
      run: |
        python scripts/run_tests.py integration

    - name: Run coverage
      run: |
        pytest --cov=src/hifzdefend --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

Tests run automatically before commits:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        args: ['-m', 'not slow', '--tb=short']
        language: system
        pass_filenames: false
        always_run: true
```

---

## Troubleshooting Tests

### Common Issues

**Issue: Tests fail with "ModuleNotFoundError"**
```bash
# Solution: Install in editable mode
pip install -e ".[dev]"
```

**Issue: Async tests hang**
```bash
# Solution: Ensure pytest-asyncio is installed
pip install pytest-asyncio

# And add to pytest.ini:
# asyncio_mode = auto
```

**Issue: Performance tests fail on slow machines**
```bash
# Solution: Skip performance tests
pytest -m "not benchmark"
```

**Issue: Registry tests fail without admin rights**
```bash
# Solution: Skip tests requiring admin
pytest -m "not requires_admin"
```

**Issue: Docker tests fail**
```bash
# Solution: Ensure Docker Desktop is running
# Or skip Docker tests:
pytest -m "not requires_docker"
```

### Debugging Tests

```bash
# Run with verbose output
pytest -vv -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Show local variables in errors
pytest -l

# Enable debug logging
pytest --log-cli-level=DEBUG
```

---

## Contributing Tests

When adding new features:

1. **Write tests first** (TDD approach preferred)
2. **Aim for 90%+ coverage** of new code
3. **Include integration tests** for component interactions
4. **Add performance tests** if performance-critical
5. **Document test purpose** with clear docstrings

### Test Review Checklist

- [ ] Tests are isolated (no dependencies on other tests)
- [ ] Tests clean up resources (files, processes, connections)
- [ ] Mocks are used for external dependencies
- [ ] Tests have clear, descriptive names
- [ ] Performance-critical code has benchmarks
- [ ] Tests pass consistently (not flaky)
- [ ] Coverage increased or maintained

---

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)

---

**Last Updated**: 2026-01-25
**Version**: Phase 1.5
