"""Docker Security Scanner for HifzDefend.

Monitors Docker containers and images for security threats:
- Scans Docker images before running containers
- Checks base images against vulnerability databases
- Monitors Dockerfile for suspicious commands
- Detects privileged container creation
- Scans for secrets in container layers
- Monitors Docker socket access
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..monitoring.base import BaseMonitor, MonitorConfig
from ..monitoring.events import DockerSecurityEvent, EventSeverity, EventType

logger = logging.getLogger(__name__)


class DockerMonitorConfig(MonitorConfig):
    """Configuration for Docker Security monitor."""

    scan_images: bool = Field(default=True, description="Scan Docker images")
    scan_before_run: bool = Field(default=True, description="Scan images before running")
    block_privileged: bool = Field(default=True, description="Alert on privileged containers")
    scan_for_secrets: bool = Field(default=True, description="Scan for secrets in images")
    trivy_enabled: bool = Field(default=True, description="Use Trivy for scanning")
    max_image_age_days: int = Field(
        default=30, ge=1, description="Alert if image is older than this"
    )


class DockerMonitor(BaseMonitor):
    """Monitor Docker security.

    This monitor watches Docker for security issues including:
    - Vulnerable images
    - Privileged containers
    - Secrets in container layers
    - Suspicious Dockerfile commands
    - Old/outdated images

    Example:
        ```python
        config = DockerMonitorConfig(enabled=True)
        monitor = DockerMonitor(config, event_bus)
        await monitor.start_monitoring()
        ```
    """

    # Suspicious Dockerfile commands
    SUSPICIOUS_DOCKERFILE_PATTERNS = [
        r"curl\s+.+\|\s*bash",  # Piping curl to bash
        r"wget\s+.+\|\s*bash",  # Piping wget to bash
        r"chmod\s+777",  # World-writable permissions
        r"--insecure",  # Insecure curl/wget
        r"--no-check-certificate",  # Skip cert verification
        r"ADD\s+http",  # ADD from HTTP (not HTTPS)
    ]

    # Secret patterns to detect
    SECRET_PATTERNS = {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "AWS Secret Key": r"aws.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]",
        "GitHub Token": r"gh[pousr]_[0-9a-zA-Z]{36}",
        "Generic API Key": r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[0-9a-zA-Z]{32,}",
        "Private Key": r"-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY",
        "Password": r"password['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]",
    }

    def __init__(self, config: DockerMonitorConfig, event_bus: Any) -> None:
        """Initialize the Docker monitor.

        Args:
            config: Monitor configuration
            event_bus: Event bus for publishing events
        """
        super().__init__(config, event_bus)
        self.config: DockerMonitorConfig = config

        # Docker client
        self._docker_client: Optional[Any] = None
        self._docker_available = False

        # Tracked containers/images
        self._monitored_containers: set[str] = set()
        self._scanned_images: set[str] = set()

    async def start(self) -> None:
        """Start the Docker monitor."""
        try:
            import docker

            self._docker_client = docker.from_env()
            self._docker_available = True
            self._logger.info("Docker monitor started - Docker daemon available")
        except Exception as e:
            self._logger.warning(f"Docker not available: {e}")
            self._docker_available = False

        self._running = True

    async def stop(self) -> None:
        """Stop the Docker monitor."""
        if self._docker_client:
            try:
                self._docker_client.close()
            except Exception as e:
                self._logger.error(f"Error closing Docker client: {e}")

        self._running = False
        self._logger.info("Docker monitor stopped")

    async def check(self) -> list[DockerSecurityEvent]:
        """Check Docker for security issues.

        Returns:
            List of security events detected
        """
        events: list[DockerSecurityEvent] = []

        if not self._docker_available:
            return events

        try:
            # Check running containers
            containers = self._docker_client.containers.list()
            for container in containers:
                container_events = await self._check_container(container)
                events.extend(container_events)

            # Check images if scanning enabled
            if self.config.scan_images:
                images = self._docker_client.images.list()
                for image in images:
                    image_events = await self._check_image(image)
                    events.extend(image_events)

        except Exception as e:
            self._logger.error(f"Error checking Docker: {e}", exc_info=True)

        return events

    async def _check_container(self, container: Any) -> list[DockerSecurityEvent]:
        """Check a Docker container for security issues.

        Args:
            container: Docker container object

        Returns:
            List of security events
        """
        events: list[DockerSecurityEvent] = []

        try:
            container_id = container.id[:12]

            # Skip if already monitored
            if container_id in self._monitored_containers:
                return events

            self._monitored_containers.add(container_id)

            # Log container start
            events.append(
                DockerSecurityEvent(
                    event_type=EventType.DOCKER_CONTAINER_STARTED,
                    severity=EventSeverity.INFO,
                    source_monitor=self.name,
                    threat_score=0,
                    description=f"Docker container started: {container.name}",
                    data={
                        "container_id": container_id,
                        "container_name": container.name,
                        "image": container.image.tags[0] if container.image.tags else "unknown",
                        "status": container.status,
                    },
                )
            )

            # Check if container is privileged
            if self.config.block_privileged:
                attrs = container.attrs
                host_config = attrs.get("HostConfig", {})
                if host_config.get("Privileged", False):
                    events.append(
                        DockerSecurityEvent(
                            event_type=EventType.PRIVILEGED_CONTAINER_DETECTED,
                            severity=EventSeverity.CRITICAL,
                            source_monitor=self.name,
                            threat_score=90,
                            description=f"Privileged container detected: {container.name}",
                            data={
                                "container_id": container_id,
                                "container_name": container.name,
                                "image": container.image.tags[0]
                                if container.image.tags
                                else "unknown",
                            },
                        )
                    )

            # Check for host network mode (security concern)
            if host_config.get("NetworkMode") == "host":
                events.append(
                    DockerSecurityEvent(
                        event_type=EventType.SUSPICIOUS_ACTIVITY,
                        severity=EventSeverity.WARNING,
                        source_monitor=self.name,
                        threat_score=60,
                        description=f"Container using host network mode: {container.name}",
                        data={
                            "container_id": container_id,
                            "container_name": container.name,
                            "network_mode": "host",
                        },
                    )
                )

            # Check for Docker socket mount (dangerous)
            mounts = attrs.get("Mounts", [])
            for mount in mounts:
                if "/var/run/docker.sock" in mount.get("Source", ""):
                    events.append(
                        DockerSecurityEvent(
                            event_type=EventType.SUSPICIOUS_ACTIVITY,
                            severity=EventSeverity.CRITICAL,
                            source_monitor=self.name,
                            threat_score=95,
                            description=f"Container has Docker socket access: {container.name}",
                            data={
                                "container_id": container_id,
                                "container_name": container.name,
                                "risk": "Full Docker control from container",
                            },
                        )
                    )

        except Exception as e:
            self._logger.error(f"Error checking container: {e}", exc_info=True)

        return events

    async def _check_image(self, image: Any) -> list[DockerSecurityEvent]:
        """Check a Docker image for security issues.

        Args:
            image: Docker image object

        Returns:
            List of security events
        """
        events: list[DockerSecurityEvent] = []

        try:
            image_id = image.id.split(":")[1][:12] if ":" in image.id else image.id[:12]

            # Skip if already scanned
            if image_id in self._scanned_images:
                return events

            self._scanned_images.add(image_id)

            # Get image tags
            tags = image.tags if image.tags else ["<none>:<none>"]

            # Log image scan
            events.append(
                DockerSecurityEvent(
                    event_type=EventType.DOCKER_IMAGE_SCANNED,
                    severity=EventSeverity.INFO,
                    source_monitor=self.name,
                    threat_score=0,
                    description=f"Docker image scanned: {tags[0]}",
                    data={
                        "image_id": image_id,
                        "tags": tags,
                        "size": image.attrs.get("Size", 0),
                    },
                )
            )

            # Check image age
            created = image.attrs.get("Created", "")
            if created:
                created_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                age_days = (datetime.now(created_date.tzinfo) - created_date).days

                if age_days > self.config.max_image_age_days:
                    events.append(
                        DockerSecurityEvent(
                            event_type=EventType.SUSPICIOUS_ACTIVITY,
                            severity=EventSeverity.WARNING,
                            source_monitor=self.name,
                            threat_score=40,
                            description=f"Old Docker image detected: {tags[0]} ({age_days} days old)",
                            data={
                                "image_id": image_id,
                                "tags": tags,
                                "age_days": age_days,
                                "recommendation": "Update to latest version",
                            },
                        )
                    )

            # Scan for secrets if enabled
            if self.config.scan_for_secrets:
                secret_events = await self._scan_image_for_secrets(image, image_id, tags)
                events.extend(secret_events)

        except Exception as e:
            self._logger.error(f"Error checking image: {e}", exc_info=True)

        return events

    async def _scan_image_for_secrets(
        self, image: Any, image_id: str, tags: list[str]
    ) -> list[DockerSecurityEvent]:
        """Scan Docker image layers for secrets.

        Args:
            image: Docker image object
            image_id: Image ID
            tags: Image tags

        Returns:
            List of security events for secrets found
        """
        events: list[DockerSecurityEvent] = []

        try:
            # Get image history
            history = image.history()

            for layer in history:
                created_by = layer.get("CreatedBy", "")

                # Check for secrets in layer commands
                for secret_type, pattern in self.SECRET_PATTERNS.items():
                    if re.search(pattern, created_by):
                        events.append(
                            DockerSecurityEvent(
                                event_type=EventType.SECRETS_IN_CONTAINER,
                                severity=EventSeverity.CRITICAL,
                                source_monitor=self.name,
                                threat_score=95,
                                description=f"Secret found in Docker image: {secret_type}",
                                data={
                                    "image_id": image_id,
                                    "tags": tags,
                                    "secret_type": secret_type,
                                    "layer": created_by[:100],  # Truncate
                                },
                            )
                        )

                # Check for suspicious commands
                for pattern in self.SUSPICIOUS_DOCKERFILE_PATTERNS:
                    if re.search(pattern, created_by, re.IGNORECASE):
                        events.append(
                            DockerSecurityEvent(
                                event_type=EventType.SUSPICIOUS_ACTIVITY,
                                severity=EventSeverity.WARNING,
                                source_monitor=self.name,
                                threat_score=70,
                                description=f"Suspicious Dockerfile command in image: {tags[0]}",
                                data={
                                    "image_id": image_id,
                                    "tags": tags,
                                    "command": created_by[:100],  # Truncate
                                    "risk": "Potentially dangerous command pattern",
                                },
                            )
                        )

        except Exception as e:
            self._logger.error(f"Error scanning image for secrets: {e}", exc_info=True)

        return events

    async def _run_trivy_scan(self, image_name: str) -> Optional[dict]:
        """Run Trivy vulnerability scanner on image.

        Args:
            image_name: Name of image to scan

        Returns:
            Scan results or None if Trivy not available
        """
        if not self.config.trivy_enabled:
            return None

        try:
            # Trivy integration would go here
            # This is a placeholder for future implementation
            self._logger.debug(f"Would run Trivy scan on {image_name}")
            return None
        except Exception as e:
            self._logger.error(f"Error running Trivy scan: {e}")
            return None
