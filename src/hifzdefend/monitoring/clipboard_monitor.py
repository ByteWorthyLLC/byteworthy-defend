"""Clipboard security monitoring for HifzDefend.

This monitor protects against clipboard hijacking including:
- Cryptocurrency address replacement
- Sensitive data detection in clipboard
- Clipboard access by suspicious processes
- Clipboard hijacking malware

Features:
- Real-time clipboard monitoring
- Crypto address pattern detection
- Clipboard hijacking detection
- Sensitive data alerts
- Process-to-clipboard access tracking
"""

import hashlib
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import psutil
from pydantic import Field

from hifzdefend.monitoring.base import BaseMonitor
from hifzdefend.monitoring.events import Event, EventSeverity, EventType
from hifzdefend.monitoring.base import MonitorConfig

logger = logging.getLogger(__name__)


class ClipboardMonitorConfig(MonitorConfig):
    """Configuration for Clipboard security monitor."""

    enabled: bool = Field(
        default=True, description="Enable clipboard security monitoring"
    )

    alert_on_crypto_address_change: bool = Field(
        default=True,
        description="Alert when cryptocurrency addresses are detected/changed in clipboard",
    )

    detect_clipboard_hijacking: bool = Field(
        default=True,
        description="Detect clipboard hijacking attempts (address replacement)",
    )

    detect_sensitive_data: bool = Field(
        default=True,
        description="Detect sensitive data in clipboard (passwords, keys, tokens)",
    )

    monitor_clipboard_access: bool = Field(
        default=True,
        description="Track which processes access clipboard",
    )

    crypto_address_patterns: dict[str, str] = Field(
        default_factory=lambda: {
            "bitcoin": r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
            "ethereum": r"\b0x[a-fA-F0-9]{40}\b",
            "litecoin": r"\b[LM][a-km-zA-HJ-NP-Z1-9]{26,33}\b",
            "monero": r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b",
            "ripple": r"\br[a-zA-Z0-9]{24,34}\b",
        },
        description="Regex patterns for cryptocurrency addresses",
    )

    sensitive_patterns: dict[str, str] = Field(
        default_factory=lambda: {
            "private_key": r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
            "api_key": r"(api[_-]?key|apikey)[\"']?\s*[:=]\s*[\"']?[a-zA-Z0-9]{16,}",
            "password": r"(password|passwd|pwd)[\"']?\s*[:=]\s*[\"']?[^\s\"']{8,}",
            "aws_key": r"AKIA[0-9A-Z]{16}",
            "github_token": r"ghp_[a-zA-Z0-9]{36}",
        },
        description="Patterns for sensitive data",
    )

    max_clipboard_changes_per_minute: int = Field(
        default=20,
        ge=5,
        description="Alert if clipboard changes more than this many times per minute",
    )

    whitelisted_processes: list[str] = Field(
        default_factory=lambda: [
            "chrome.exe",
            "firefox.exe",
            "msedge.exe",
            "code.exe",  # VS Code
            "notepad.exe",
            "notepad++.exe",
            "sublime_text.exe",
            "explorer.exe",
        ],
        description="Processes allowed to access clipboard without alerts",
    )

    scan_interval_seconds: int = Field(
        default=5,
        ge=1,
        description="How often to check clipboard (seconds)",
    )


@dataclass
class ClipboardEntry:
    """Information about a clipboard entry."""

    content_hash: str
    timestamp: datetime
    content_preview: str
    detected_patterns: list[str]


class ClipboardMonitor(BaseMonitor):
    """Monitor clipboard for security threats."""

    def __init__(self, config: ClipboardMonitorConfig, event_bus):
        super().__init__(config, event_bus)
        self.config: ClipboardMonitorConfig = config

        # Clipboard tracking
        self._last_clipboard_hash: Optional[str] = None
        self._clipboard_history: list[ClipboardEntry] = []
        self._clipboard_change_times: list[datetime] = []

        # Crypto address tracking
        self._last_crypto_address: Optional[str] = None
        self._crypto_address_changes: int = 0

        # Statistics
        self._stats = {
            "clipboard_changes": 0,
            "crypto_addresses_detected": 0,
            "hijacking_detected": 0,
            "sensitive_data_detected": 0,
            "excessive_changes_detected": 0,
        }

        # Try to import clipboard library
        try:
            import pyperclip
            self._clipboard_module = pyperclip
            self._clipboard_available = True
        except ImportError:
            logger.warning("pyperclip not available - clipboard monitoring disabled")
            logger.warning("Install with: pip install pyperclip")
            self._clipboard_module = None
            self._clipboard_available = False

        logger.info("Clipboard monitor initialized")

    async def start(self) -> None:
        """Start clipboard monitoring."""
        if self._running:
            logger.warning("Clipboard monitor already running")
            return

        logger.info("Starting clipboard monitor")

        if not self._clipboard_available:
            logger.error("Clipboard monitoring unavailable (pyperclip not installed)")
            return

        self._running = True
        logger.info("Clipboard monitor started successfully")

    async def stop(self) -> None:
        """Stop monitoring."""
        if not self._running:
            return

        logger.info("Stopping clipboard monitor")
        self._running = False
        logger.info("Clipboard monitor stopped")

    async def check(self) -> list[Event]:
        """Perform clipboard security check."""
        if not self._running or not self._clipboard_available:
            return []

        events = []

        try:
            # Get current clipboard content
            clipboard_content = self._get_clipboard_content()

            if clipboard_content is None:
                return []

            # Calculate content hash
            content_hash = self._hash_content(clipboard_content)

            # Check if clipboard changed
            if content_hash != self._last_clipboard_hash:
                self._stats["clipboard_changes"] += 1
                self._clipboard_change_times.append(datetime.now())

                # Check for crypto addresses
                if self.config.alert_on_crypto_address_change:
                    crypto_event = self._check_crypto_address(clipboard_content)
                    if crypto_event:
                        events.append(crypto_event)

                # Check for sensitive data
                if self.config.detect_sensitive_data:
                    sensitive_event = self._check_sensitive_data(clipboard_content)
                    if sensitive_event:
                        events.append(sensitive_event)

                # Track clipboard entry
                self._track_clipboard_entry(clipboard_content, content_hash)

                # Update last hash
                self._last_clipboard_hash = content_hash

            # Check for excessive clipboard changes
            if self.config.detect_clipboard_hijacking:
                excessive_event = self._check_excessive_changes()
                if excessive_event:
                    events.append(excessive_event)

        except Exception as e:
            logger.error(f"Error during clipboard check: {e}", exc_info=True)

        return events

    def _get_clipboard_content(self) -> Optional[str]:
        """Get current clipboard content."""
        if not self._clipboard_module:
            return None

        try:
            content = self._clipboard_module.paste()
            return content if content else None
        except Exception as e:
            logger.debug(f"Error reading clipboard: {e}")
            return None

    def _hash_content(self, content: str) -> str:
        """Calculate hash of clipboard content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _check_crypto_address(self, content: str) -> Optional[Event]:
        """Check for cryptocurrency addresses in clipboard."""
        detected_cryptos = []

        for crypto_name, pattern in self.config.crypto_address_patterns.items():
            if re.search(pattern, content):
                detected_cryptos.append(crypto_name)

        if detected_cryptos:
            self._stats["crypto_addresses_detected"] += 1

            # Extract the address
            # Try to get the actual address for comparison
            current_address = None
            for crypto_name in detected_cryptos:
                pattern = self.config.crypto_address_patterns[crypto_name]
                match = re.search(pattern, content)
                if match:
                    current_address = match.group(0)
                    break

            # Check for address replacement (clipboard hijacking)
            if self._last_crypto_address and current_address:
                if self._last_crypto_address != current_address:
                    # Address changed - possible hijacking!
                    self._stats["hijacking_detected"] += 1
                    self._crypto_address_changes += 1

                    event = Event(
                        event_type=EventType.THREAT_DETECTED,
                        severity=EventSeverity.CRITICAL,
                        source_monitor=self.name,
                        description="Cryptocurrency address replacement detected (clipboard hijacking)",
                        threat_score=95,
                        data={
                            "pattern": "clipboard_hijacking",
                            "crypto_types": detected_cryptos,
                            "previous_address": self._last_crypto_address,
                            "new_address": current_address,
                            "recommendation": "CRITICAL: Clipboard hijacking malware detected! Crypto address was replaced. Do NOT send funds. Run full malware scan.",
                        },
                    )

                    self._last_crypto_address = current_address
                    return event

            # Track current address
            if current_address:
                self._last_crypto_address = current_address

            # Alert on crypto address detection (warning level)
            event = Event(
                event_type=EventType.SUSPICIOUS_ACTIVITY,
                severity=EventSeverity.WARNING,
                source_monitor=self.name,
                description=f"Cryptocurrency address detected in clipboard: {', '.join(detected_cryptos)}",
                threat_score=30,
                data={
                    "pattern": "crypto_address_detected",
                    "crypto_types": detected_cryptos,
                    "address_preview": current_address[:20] + "..." if current_address and len(current_address) > 20 else current_address,
                    "recommendation": "Verify destination address before sending funds. Check for clipboard hijacking malware.",
                },
            )

            return event

        return None

    def _check_sensitive_data(self, content: str) -> Optional[Event]:
        """Check for sensitive data in clipboard."""
        detected_patterns = []

        for pattern_name, pattern in self.config.sensitive_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                detected_patterns.append(pattern_name)

        if detected_patterns:
            self._stats["sensitive_data_detected"] += 1

            event = Event(
                event_type=EventType.SUSPICIOUS_ACTIVITY,
                severity=EventSeverity.WARNING,
                source_monitor=self.name,
                description=f"Sensitive data detected in clipboard: {', '.join(detected_patterns)}",
                threat_score=40,
                data={
                    "pattern": "sensitive_data_clipboard",
                    "detected_types": detected_patterns,
                    "content_length": len(content),
                    "recommendation": "Sensitive data in clipboard may be exposed. Clear clipboard after use.",
                },
            )

            return event

        return None

    def _check_excessive_changes(self) -> Optional[Event]:
        """Check for excessive clipboard changes (possible hijacking)."""
        # Clean up old change times (older than 1 minute)
        cutoff = datetime.now() - timedelta(minutes=1)
        self._clipboard_change_times = [
            ts for ts in self._clipboard_change_times if ts > cutoff
        ]

        change_count = len(self._clipboard_change_times)

        if change_count > self.config.max_clipboard_changes_per_minute:
            self._stats["excessive_changes_detected"] += 1

            event = Event(
                event_type=EventType.SUSPICIOUS_ACTIVITY,
                severity=EventSeverity.WARNING,
                source_monitor=self.name,
                description=f"Excessive clipboard changes: {change_count}/minute",
                threat_score=60,
                data={
                    "pattern": "excessive_clipboard_changes",
                    "change_count": change_count,
                    "threshold": self.config.max_clipboard_changes_per_minute,
                    "recommendation": "Unusual clipboard activity. May indicate clipboard hijacking malware or automated tool.",
                },
            )

            return event

        return None

    def _track_clipboard_entry(self, content: str, content_hash: str) -> None:
        """Track clipboard entry in history."""
        # Create content preview (first 100 chars)
        preview = content[:100] if len(content) > 100 else content

        # Detect patterns
        detected_patterns = []

        # Check crypto
        for crypto_name in self.config.crypto_address_patterns:
            if re.search(self.config.crypto_address_patterns[crypto_name], content):
                detected_patterns.append(f"crypto_{crypto_name}")

        # Check sensitive
        for pattern_name in self.config.sensitive_patterns:
            if re.search(self.config.sensitive_patterns[pattern_name], content, re.IGNORECASE):
                detected_patterns.append(f"sensitive_{pattern_name}")

        entry = ClipboardEntry(
            content_hash=content_hash,
            timestamp=datetime.now(),
            content_preview=preview,
            detected_patterns=detected_patterns,
        )

        self._clipboard_history.append(entry)

        # Keep history limited
        if len(self._clipboard_history) > 100:
            self._clipboard_history.pop(0)

    def get_statistics(self) -> dict[str, Any]:
        """Get monitor statistics."""
        return {
            "clipboard_changes": self._stats["clipboard_changes"],
            "crypto_addresses_detected": self._stats["crypto_addresses_detected"],
            "hijacking_detected": self._stats["hijacking_detected"],
            "sensitive_data_detected": self._stats["sensitive_data_detected"],
            "excessive_changes_detected": self._stats["excessive_changes_detected"],
            "crypto_address_changes": self._crypto_address_changes,
            "clipboard_history_size": len(self._clipboard_history),
            "alert_on_crypto": self.config.alert_on_crypto_address_change,
            "detect_hijacking": self.config.detect_clipboard_hijacking,
            "clipboard_available": self._clipboard_available,
        }
