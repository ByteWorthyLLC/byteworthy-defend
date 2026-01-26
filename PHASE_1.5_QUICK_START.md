# Phase 1.5 Quick Start Guide

## What's Been Implemented

Phase 1.5 implementation has begun with the foundational architecture and 2 key security monitors:

✅ **Event Bus Architecture** - Complete event-driven monitoring system
✅ **Package Manager Security Monitor** - Detects malicious npm/pip packages
✅ **Docker Security Scanner** - Monitors Docker containers and images for threats
✅ **Configuration System** - Extended with all Phase 1.5 settings
✅ **Dependencies** - All required packages added to pyproject.toml

## Quick Setup

### 1. Create Virtual Environment (Recommended)

```bash
cd C:\Users\richa\Documents\HifzDefend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Verify
python --version
```

### 2. Install Dependencies

```bash
# Install HifzDefend with dev dependencies
pip install -e ".[dev]"

# Verify key dependencies
python -c "import psutil; import docker; print('Core dependencies OK')"
```

**Note**: Some dependencies may require system packages:
- `pyaudio` may require PortAudio
- `opencv-python` may require Visual C++ redistributables
- `scapy` may require Npcap on Windows

If any installation fails, you can install them individually later as needed.

### 3. Run Tests

```bash
# Run all monitoring tests
pytest tests/test_monitoring/ -v

# Run specific tests
pytest tests/test_monitoring/test_event_bus.py -v
pytest tests/test_monitoring/test_package_monitor.py -v
pytest tests/test_monitoring/test_docker_monitor.py -v

# Run with coverage report
pytest tests/test_monitoring/ --cov=hifzdefend.monitoring --cov-report=html
```

Expected output:
```
tests/test_monitoring/test_event_bus.py ............ PASSED
tests/test_monitoring/test_base_monitor.py .......... PASSED
tests/test_monitoring/test_manager.py ............. PASSED
tests/test_monitoring/test_package_monitor.py ............ PASSED
tests/test_monitoring/test_docker_monitor.py .......... PASSED
```

## Testing the Implementation

### Test 1: Event Bus Functionality

Create a test script `test_eventbus.py`:

```python
import asyncio
from hifzdefend.monitoring import EventBus, Event, EventType, EventSeverity

async def main():
    # Create event bus
    bus = EventBus()

    # Subscribe to events
    def on_threat(event):
        print(f"🚨 THREAT: {event.description} (score: {event.threat_score})")

    bus.subscribe(EventType.THREAT_DETECTED, on_threat)

    # Start event processing
    await bus.start()

    # Publish test event
    event = Event(
        event_type=EventType.THREAT_DETECTED,
        severity=EventSeverity.WARNING,
        source_monitor="TestMonitor",
        threat_score=75,
        description="Test threat detected"
    )
    bus.publish(event)

    # Wait for processing
    await asyncio.sleep(0.5)

    # Show stats
    stats = bus.get_stats()
    print(f"\n📊 Event Bus Stats:")
    print(f"  - Total events: {stats['total_events_processed']}")
    print(f"  - Queue size: {stats['queue_size']}")
    print(f"  - Running: {stats['running']}")

    # Stop
    await bus.stop()

asyncio.run(main())
```

Run it:
```bash
python test_eventbus.py
```

Expected output:
```
🚨 THREAT: Test threat detected (score: 75)

📊 Event Bus Stats:
  - Total events: 1
  - Queue size: 0
  - Running: True
```

### Test 2: Package Manager Monitor

Create a test script `test_package_monitor.py`:

```python
import asyncio
from hifzdefend.monitoring import EventBus, get_event_bus
from hifzdefend.monitoring.package_monitor import PackageMonitor, PackageManagerConfig

async def main():
    # Setup
    bus = get_event_bus()
    config = PackageManagerConfig(
        enabled=True,
        npm=True,
        pip=True,
        typosquat_threshold=3
    )

    # Create monitor
    monitor = PackageMonitor(config, bus)

    # Test typosquatting detection
    print("🔍 Testing typosquatting detection:")
    print(f"  'react' vs 'reakt': {monitor._levenshtein_distance('react', 'reakt')} distance")
    print(f"  'lodash' vs 'loadash': {monitor._levenshtein_distance('lodash', 'loadash')} distance")

    # Test package extraction
    print("\n📦 Testing package extraction:")
    npm_packages = monitor._extract_npm_packages("npm install lodash express")
    print(f"  npm command: {npm_packages}")

    pip_packages = monitor._extract_pip_packages("pip install requests numpy")
    print(f"  pip command: {pip_packages}")

    # Check for typosquatting
    print("\n⚠️  Testing typosquatting check:")
    distance = monitor._check_typosquatting("reakt", monitor.POPULAR_NPM_PACKAGES)
    print(f"  'reakt' similarity to popular packages: {distance}")
    if distance < config.typosquat_threshold and distance > 0:
        print("  ⚠️  TYPOSQUATTING DETECTED!")

asyncio.run(main())
```

Run it:
```bash
python test_package_monitor.py
```

### Test 3: Docker Monitor (if Docker installed)

Create a test script `test_docker_monitor.py`:

```python
import asyncio
from hifzdefend.monitoring import EventBus, get_event_bus
from hifzdefend.monitoring.docker_monitor import DockerMonitor, DockerMonitorConfig

async def main():
    # Setup
    bus = get_event_bus()
    config = DockerMonitorConfig(
        enabled=True,
        scan_images=True,
        block_privileged=True
    )

    # Create monitor
    monitor = DockerMonitor(config, bus)

    # Start monitor
    await monitor.start()

    if monitor._docker_available:
        print("✅ Docker is available")
        print("\n🔍 Checking Docker security...")

        # Run check
        events = await monitor.check()

        print(f"\n📊 Found {len(events)} events:")
        for event in events:
            print(f"  - {event.event_type.value}: {event.description}")
    else:
        print("⚠️  Docker is not available")

    # Stop monitor
    await monitor.stop()

asyncio.run(main())
```

Run it:
```bash
python test_docker_monitor.py
```

## Next Steps

### Continue Implementation (Choose One)

#### Option 1: Implement IDE Monitor (8 hours)

Create `src/hifzdefend/monitoring/ide_monitor.py`:

```python
from ..monitoring.base import BaseMonitor, MonitorConfig
from ..monitoring.events import EventType, EventSeverity
# Monitor VS Code extensions, Claude CLI, GitHub Desktop
```

#### Option 2: Implement Registry Monitor (10 hours)

Create `src/hifzdefend/monitoring/registry_monitor.py`:

```python
from ..monitoring.base import BaseMonitor, MonitorConfig
import winreg
# Monitor Windows Registry changes
```

#### Option 3: Implement PowerShell Monitor (8 hours)

Create `src/hifzdefend/monitoring/powershell_monitor.py`:

```python
from ..monitoring.base import BaseMonitor, MonitorConfig
# Monitor PowerShell execution and obfuscation
```

### Full Implementation Template

Use this template for new monitors:

```python
"""[Monitor Name] for HifzDefend.

Description of what this monitor does and why it's important.
"""

import logging
from typing import Any

from pydantic import BaseModel, Field

from ..monitoring.base import BaseMonitor, MonitorConfig
from ..monitoring.events import Event, EventSeverity, EventType

logger = logging.getLogger(__name__)


class [MonitorName]Config(MonitorConfig):
    """Configuration for [Monitor Name]."""

    # Add monitor-specific config fields
    enabled: bool = Field(default=True)
    # ... more fields


class [MonitorName](BaseMonitor):
    """[Monitor description].

    Example:
        ```python
        config = [MonitorName]Config(enabled=True)
        monitor = [MonitorName](config, event_bus)
        await monitor.start_monitoring()
        ```
    """

    def __init__(self, config: [MonitorName]Config, event_bus: Any) -> None:
        """Initialize the monitor."""
        super().__init__(config, event_bus)
        self.config: [MonitorName]Config = config
        # Add monitor-specific initialization

    async def start(self) -> None:
        """Start the monitor."""
        self._running = True
        self._logger.info(f"{self.name} started")

    async def stop(self) -> None:
        """Stop the monitor."""
        self._running = False
        self._logger.info(f"{self.name} stopped")

    async def check(self) -> list[Event]:
        """Perform monitoring check.

        Returns:
            List of events detected
        """
        events: list[Event] = []

        try:
            # Implement monitoring logic here
            # Generate events for detected threats
            pass
        except Exception as e:
            self._logger.error(f"Error in check: {e}", exc_info=True)

        return events
```

## Verifying Installation

### Check Dependencies

```bash
# List installed packages
pip list | grep -E "(yara|docker|psutil|scapy|pydantic)"

# Test imports
python -c "
from hifzdefend.monitoring import EventBus, BaseMonitor, MonitorManager
from hifzdefend.monitoring.package_monitor import PackageMonitor
from hifzdefend.monitoring.docker_monitor import DockerMonitor
print('✅ All imports successful')
"
```

### Check Configuration

```bash
# View default configuration
cat config/hifzdefend.defaults.toml

# Check monitoring sections
grep -A 5 "\[monitoring\]" config/hifzdefend.defaults.toml
```

## Troubleshooting

### Issue: ModuleNotFoundError

**Problem**: `ModuleNotFoundError: No module named 'hifzdefend'`

**Solution**:
```bash
# Ensure you're in the project directory
cd C:\Users\richa\Documents\HifzDefend

# Install in editable mode
pip install -e .
```

### Issue: pyaudio Installation Fails

**Problem**: `error: Microsoft Visual C++ 14.0 or greater is required`

**Solution**:
```bash
# Skip pyaudio for now (only needed for microphone monitoring)
# Or install Visual C++ Build Tools from Microsoft
# Or use pre-built wheel:
pip install pipwin
pipwin install pyaudio
```

### Issue: Docker Not Available

**Problem**: `Docker daemon not found`

**Solution**: Docker monitor will gracefully handle Docker not being available. Install Docker Desktop if needed.

### Issue: Tests Fail with "no asyncio event loop"

**Problem**: `RuntimeError: no running event loop`

**Solution**: Tests use `pytest-asyncio`. Ensure it's installed:
```bash
pip install pytest-asyncio
```

## Getting Help

1. **Check Implementation Status**: See `docs/PHASE_1.5_IMPLEMENTATION_STATUS.md`
2. **Review Architecture**: See `docs/ARCHITECTURE.md`
3. **Read Original Plan**: See the full Phase 1.5 plan
4. **Check Tests**: Look at existing tests for examples

## Summary

You now have:
- ✅ Working Event Bus Architecture
- ✅ 2 Security Monitors (Package Manager, Docker)
- ✅ Complete configuration system
- ✅ Comprehensive test suite (for completed modules)
- ✅ Full dependency list

**Next**: Choose a monitor to implement from the pending list and follow the template above!

**Estimated Remaining Time**: 90-120 hours for full Phase 1.5 completion (15 monitors remaining)

---

Happy coding! 🚀
