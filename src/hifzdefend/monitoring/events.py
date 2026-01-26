"""Event types and models for HifzDefend monitoring system.

This module defines the event-driven architecture foundation for all security monitors.
Events are published to the EventBus and consumed by subscribers for threat detection
and response actions.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(Enum):
    """Types of security events that can be detected."""

    # Threat Detection Events
    THREAT_DETECTED = "threat_detected"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MALWARE_DETECTED = "malware_detected"
    RANSOMWARE_DETECTED = "ransomware_detected"
    CRYPTOMINER_DETECTED = "cryptominer_detected"
    SPYWARE_DETECTED = "spyware_detected"

    # Process Events
    PROCESS_STARTED = "process_started"
    PROCESS_TERMINATED = "process_terminated"
    SUSPICIOUS_PROCESS = "suspicious_process"
    PROCESS_INJECTION = "process_injection"

    # File Events
    FILE_MODIFIED = "file_modified"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    FILE_ENCRYPTED = "file_encrypted"
    MASS_FILE_MODIFICATION = "mass_file_modification"

    # Network Events
    NETWORK_CONNECTION = "network_connection"
    SUSPICIOUS_CONNECTION = "suspicious_connection"
    C2_BEACON_DETECTED = "c2_beacon_detected"
    DNS_QUERY = "dns_query"
    DNS_TUNNELING_DETECTED = "dns_tunneling_detected"
    MALICIOUS_IP_CONNECTION = "malicious_ip_connection"

    # Registry Events (Windows)
    REGISTRY_CHANGED = "registry_changed"
    REGISTRY_STARTUP_ENTRY = "registry_startup_entry"
    REGISTRY_SERVICE_INSTALLED = "registry_service_installed"

    # Hardware Events
    HARDWARE_ACCESS = "hardware_access"
    WEBCAM_ACTIVATED = "webcam_activated"
    MICROPHONE_ACTIVATED = "microphone_activated"

    # Developer Security Events
    PACKAGE_INSTALLED = "package_installed"
    MALICIOUS_PACKAGE_DETECTED = "malicious_package_detected"
    TYPOSQUAT_DETECTED = "typosquat_detected"
    DOCKER_IMAGE_SCANNED = "docker_image_scanned"
    DOCKER_CONTAINER_STARTED = "docker_container_started"
    PRIVILEGED_CONTAINER_DETECTED = "privileged_container_detected"
    SECRETS_IN_CONTAINER = "secrets_in_container"
    IDE_EXTENSION_INSTALLED = "ide_extension_installed"
    MALICIOUS_EXTENSION_DETECTED = "malicious_extension_detected"

    # PowerShell Events
    POWERSHELL_EXECUTED = "powershell_executed"
    POWERSHELL_OBFUSCATED = "powershell_obfuscated"
    POWERSHELL_SUSPICIOUS_CMDLET = "powershell_suspicious_cmdlet"

    # Privacy Events
    CLIPBOARD_HIJACKING = "clipboard_hijacking"
    KEYLOGGER_DETECTED = "keylogger_detected"
    SCREEN_CAPTURE_DETECTED = "screen_capture_detected"

    # Download Events
    FILE_DOWNLOADED = "file_downloaded"
    SUSPICIOUS_DOWNLOAD = "suspicious_download"

    # System Events
    SHADOW_COPY_DELETED = "shadow_copy_deleted"
    FIREWALL_RULE_MODIFIED = "firewall_rule_modified"
    SECURITY_SOFTWARE_DISABLED = "security_software_disabled"

    # Monitoring Events
    MONITOR_STARTED = "monitor_started"
    MONITOR_STOPPED = "monitor_stopped"
    MONITOR_ERROR = "monitor_error"


class EventSeverity(str, Enum):
    """Severity levels for security events."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Event(BaseModel):
    """Base event class for all security events.

    All events published to the EventBus must inherit from this class.
    Events are immutable once created and include timestamp, severity,
    and threat score for prioritization.
    """

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this event",
    )
    event_type: EventType = Field(
        description="Type of event (from EventType enum)",
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the event occurred",
    )
    severity: EventSeverity = Field(
        description="Severity level (info, warning, critical)",
    )
    source_monitor: str = Field(
        description="Name of the monitor that generated this event",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data payload",
    )
    threat_score: int = Field(
        ge=0,
        le=100,
        description="Threat level score (0-100, higher = more threatening)",
    )
    description: str = Field(
        default="",
        description="Human-readable description of the event",
    )

    model_config = {
        "frozen": False,  # Allow modifications for testing
        "json_schema_extra": {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_type": "threat_detected",
                "timestamp": "2024-01-25T10:30:00",
                "severity": "warning",
                "source_monitor": "PackageMonitor",
                "data": {"package": "suspicious-package", "version": "1.0.0"},
                "threat_score": 75,
                "description": "Potentially malicious package detected",
            }
        },
    }


class ThreatDetectedEvent(Event):
    """Event for general threat detection."""

    event_type: EventType = Field(default=EventType.THREAT_DETECTED)


class ProcessEvent(Event):
    """Event for process-related activities."""

    event_type: EventType = Field(default=EventType.PROCESS_STARTED)


class FileEvent(Event):
    """Event for file system activities."""

    event_type: EventType = Field(default=EventType.FILE_MODIFIED)


class NetworkEvent(Event):
    """Event for network activities."""

    event_type: EventType = Field(default=EventType.NETWORK_CONNECTION)


class RegistryEvent(Event):
    """Event for Windows Registry changes."""

    event_type: EventType = Field(default=EventType.REGISTRY_CHANGED)


class HardwareEvent(Event):
    """Event for hardware access."""

    event_type: EventType = Field(default=EventType.HARDWARE_ACCESS)


class PackageSecurityEvent(Event):
    """Event for package manager security."""

    event_type: EventType = Field(default=EventType.PACKAGE_INSTALLED)


class DockerSecurityEvent(Event):
    """Event for Docker security."""

    event_type: EventType = Field(default=EventType.DOCKER_IMAGE_SCANNED)


class PowerShellEvent(Event):
    """Event for PowerShell activity."""

    event_type: EventType = Field(default=EventType.POWERSHELL_EXECUTED)


class PrivacyEvent(Event):
    """Event for privacy violations."""

    event_type: EventType = Field(default=EventType.CLIPBOARD_HIJACKING)


class MonitoringEvent(Event):
    """Event for monitoring system status."""

    event_type: EventType = Field(default=EventType.MONITOR_STARTED)
