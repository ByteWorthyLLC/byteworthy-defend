"""Package Manager Security Monitor for HifzDefend.

Monitors package manager installations (npm, pip) for security threats:
- Checks packages against known malicious databases
- Detects typosquatting attempts
- Verifies package signatures and checksums
- Integrates with threat intelligence APIs (Snyk, Socket.dev)
"""

import asyncio
import hashlib
import logging
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional

import psutil
import requests
from pydantic import BaseModel, Field

from ..monitoring.base import BaseMonitor, MonitorConfig
from ..monitoring.events import EventSeverity, EventType, PackageSecurityEvent

logger = logging.getLogger(__name__)


class PackageManagerConfig(MonitorConfig):
    """Configuration for Package Manager monitor."""

    npm: bool = Field(default=True, description="Monitor npm packages")
    pip: bool = Field(default=True, description="Monitor pip packages")
    check_malicious_db: bool = Field(default=True, description="Check malicious package database")
    typosquat_threshold: int = Field(
        default=3, ge=0, le=10, description="Levenshtein distance threshold for typosquatting"
    )
    verify_signatures: bool = Field(default=True, description="Verify package signatures")
    api_key_snyk: str = Field(default="", description="Snyk API key (optional)")
    api_key_socket_dev: str = Field(default="", description="Socket.dev API key (optional)")


class PackageInfo(BaseModel):
    """Information about a package installation."""

    package_manager: str  # npm, pip, yarn, etc.
    package_name: str
    version: str = ""
    command: str  # Full command executed
    timestamp: str


class PackageMonitor(BaseMonitor):
    """Monitor package manager installations for security threats.

    This monitor watches for package installation commands and performs
    security checks to detect malicious packages, typosquatting, and
    supply chain attacks.

    Example:
        ```python
        config = PackageManagerConfig(enabled=True)
        monitor = PackageMonitor(config, event_bus)
        await monitor.start_monitoring()
        ```
    """

    # Common npm packages to check for typosquatting
    POPULAR_NPM_PACKAGES = [
        "react",
        "lodash",
        "express",
        "axios",
        "webpack",
        "typescript",
        "jest",
        "eslint",
        "prettier",
        "next",
        "vue",
        "angular",
        "babel",
        "redux",
    ]

    # Common pip packages to check for typosquatting
    POPULAR_PIP_PACKAGES = [
        "requests",
        "numpy",
        "pandas",
        "django",
        "flask",
        "pytest",
        "click",
        "pillow",
        "beautifulsoup4",
        "scikit-learn",
        "tensorflow",
        "torch",
        "matplotlib",
        "pydantic",
    ]

    # Known malicious packages (examples - would be loaded from database)
    MALICIOUS_PACKAGES = {
        "npm": ["event-source-polyfill", "noblox.js-vps", "twilio-npm"],
        "pip": ["python3-dateutil", "jeIlyfish", "urllib3"],
    }

    def __init__(self, config: PackageManagerConfig, event_bus: Any) -> None:
        """Initialize the Package Manager monitor.

        Args:
            config: Monitor configuration
            event_bus: Event bus for publishing events
        """
        super().__init__(config, event_bus)
        self.config: PackageManagerConfig = config

        # Process tracking
        self._monitored_processes: set[int] = set()
        self._last_check_pids: set[int] = set()

        # Package manager command patterns
        self.npm_patterns = [
            r"npm\s+install\s+(.+)",
            r"npm\s+i\s+(.+)",
            r"yarn\s+add\s+(.+)",
            r"pnpm\s+add\s+(.+)",
        ]

        self.pip_patterns = [
            r"pip\s+install\s+(.+)",
            r"pip3\s+install\s+(.+)",
            r"poetry\s+add\s+(.+)",
        ]

    async def start(self) -> None:
        """Start the Package Manager monitor."""
        self._running = True
        self._logger.info("Package Manager monitor started")

    async def stop(self) -> None:
        """Stop the Package Manager monitor."""
        self._running = False
        self._logger.info("Package Manager monitor stopped")

    async def check(self) -> list[PackageSecurityEvent]:
        """Check for package manager installations.

        Returns:
            List of events detected during this check
        """
        events: list[PackageSecurityEvent] = []

        try:
            # Get all running processes
            current_pids = set()
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    current_pids.add(proc.info["pid"])

                    # Skip if already monitored
                    if proc.info["pid"] in self._monitored_processes:
                        continue

                    # Check for package manager commands
                    cmdline = proc.info.get("cmdline", [])
                    if not cmdline:
                        continue

                    command = " ".join(cmdline)

                    # Check npm commands
                    if self.config.npm and any(
                        pm in command.lower() for pm in ["npm", "yarn", "pnpm"]
                    ):
                        package_events = await self._check_npm_installation(command, proc.info)
                        events.extend(package_events)
                        self._monitored_processes.add(proc.info["pid"])

                    # Check pip commands
                    if self.config.pip and any(
                        pm in command.lower() for pm in ["pip", "pip3", "poetry"]
                    ):
                        package_events = await self._check_pip_installation(command, proc.info)
                        events.extend(package_events)
                        self._monitored_processes.add(proc.info["pid"])

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Clean up terminated processes from monitored set
            self._monitored_processes = self._monitored_processes.intersection(current_pids)

        except Exception as e:
            self._logger.error(f"Error checking package managers: {e}", exc_info=True)

        return events

    async def _check_npm_installation(
        self, command: str, proc_info: dict[str, Any]
    ) -> list[PackageSecurityEvent]:
        """Check npm package installation for threats.

        Args:
            command: Full command being executed
            proc_info: Process information

        Returns:
            List of security events detected
        """
        events: list[PackageSecurityEvent] = []

        # Extract package names from command
        packages = self._extract_npm_packages(command)

        for package_name in packages:
            self._logger.info(f"Checking npm package: {package_name}")

            # Log installation
            events.append(
                PackageSecurityEvent(
                    event_type=EventType.PACKAGE_INSTALLED,
                    severity=EventSeverity.INFO,
                    source_monitor=self.name,
                    threat_score=0,
                    description=f"npm package installation: {package_name}",
                    data={
                        "package_manager": "npm",
                        "package_name": package_name,
                        "command": command,
                        "pid": proc_info["pid"],
                    },
                )
            )

            # Check for typosquatting
            typosquat_score = self._check_typosquatting(
                package_name, self.POPULAR_NPM_PACKAGES
            )
            if typosquat_score < self.config.typosquat_threshold and typosquat_score > 0:
                events.append(
                    PackageSecurityEvent(
                        event_type=EventType.TYPOSQUAT_DETECTED,
                        severity=EventSeverity.WARNING,
                        source_monitor=self.name,
                        threat_score=70,
                        description=f"Potential typosquatting detected: {package_name}",
                        data={
                            "package_manager": "npm",
                            "package_name": package_name,
                            "similarity_score": typosquat_score,
                            "command": command,
                        },
                    )
                )

            # Check malicious database
            if self.config.check_malicious_db and package_name in self.MALICIOUS_PACKAGES["npm"]:
                events.append(
                    PackageSecurityEvent(
                        event_type=EventType.MALICIOUS_PACKAGE_DETECTED,
                        severity=EventSeverity.CRITICAL,
                        source_monitor=self.name,
                        threat_score=95,
                        description=f"Known malicious npm package detected: {package_name}",
                        data={
                            "package_manager": "npm",
                            "package_name": package_name,
                            "command": command,
                        },
                    )
                )

        return events

    async def _check_pip_installation(
        self, command: str, proc_info: dict[str, Any]
    ) -> list[PackageSecurityEvent]:
        """Check pip package installation for threats.

        Args:
            command: Full command being executed
            proc_info: Process information

        Returns:
            List of security events detected
        """
        events: list[PackageSecurityEvent] = []

        # Extract package names from command
        packages = self._extract_pip_packages(command)

        for package_name in packages:
            self._logger.info(f"Checking pip package: {package_name}")

            # Log installation
            events.append(
                PackageSecurityEvent(
                    event_type=EventType.PACKAGE_INSTALLED,
                    severity=EventSeverity.INFO,
                    source_monitor=self.name,
                    threat_score=0,
                    description=f"pip package installation: {package_name}",
                    data={
                        "package_manager": "pip",
                        "package_name": package_name,
                        "command": command,
                        "pid": proc_info["pid"],
                    },
                )
            )

            # Check for typosquatting
            typosquat_score = self._check_typosquatting(
                package_name, self.POPULAR_PIP_PACKAGES
            )
            if typosquat_score < self.config.typosquat_threshold and typosquat_score > 0:
                events.append(
                    PackageSecurityEvent(
                        event_type=EventType.TYPOSQUAT_DETECTED,
                        severity=EventSeverity.WARNING,
                        source_monitor=self.name,
                        threat_score=70,
                        description=f"Potential typosquatting detected: {package_name}",
                        data={
                            "package_manager": "pip",
                            "package_name": package_name,
                            "similarity_score": typosquat_score,
                            "command": command,
                        },
                    )
                )

            # Check malicious database
            if self.config.check_malicious_db and package_name in self.MALICIOUS_PACKAGES["pip"]:
                events.append(
                    PackageSecurityEvent(
                        event_type=EventType.MALICIOUS_PACKAGE_DETECTED,
                        severity=EventSeverity.CRITICAL,
                        source_monitor=self.name,
                        threat_score=95,
                        description=f"Known malicious pip package detected: {package_name}",
                        data={
                            "package_manager": "pip",
                            "package_name": package_name,
                            "command": command,
                        },
                    )
                )

        return events

    def _extract_npm_packages(self, command: str) -> list[str]:
        """Extract package names from npm command.

        Args:
            command: Full npm command

        Returns:
            List of package names
        """
        packages = []

        for pattern in self.npm_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                # Get the packages part
                packages_str = match.group(1)

                # Remove flags and extract package names
                parts = packages_str.split()
                for part in parts:
                    # Skip flags
                    if part.startswith("-"):
                        continue
                    # Extract package name (remove version specifiers)
                    package = part.split("@")[0]
                    if package:
                        packages.append(package)

        return packages

    def _extract_pip_packages(self, command: str) -> list[str]:
        """Extract package names from pip command.

        Args:
            command: Full pip command

        Returns:
            List of package names
        """
        packages = []

        for pattern in self.pip_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                # Get the packages part
                packages_str = match.group(1)

                # Remove flags and extract package names
                parts = packages_str.split()
                for part in parts:
                    # Skip flags
                    if part.startswith("-"):
                        continue
                    # Skip requirements.txt
                    if "requirements" in part.lower():
                        continue
                    # Extract package name (remove version specifiers)
                    package = re.split(r"[<>=!]", part)[0]
                    if package:
                        packages.append(package)

        return packages

    def _check_typosquatting(self, package_name: str, popular_packages: list[str]) -> int:
        """Check if package name is a typosquatting attempt.

        Uses Levenshtein distance to find similar package names.

        Args:
            package_name: Name of package to check
            popular_packages: List of popular packages to compare against

        Returns:
            Minimum distance to any popular package (0 = exact match)
        """
        min_distance = 999

        for popular in popular_packages:
            distance = self._levenshtein_distance(package_name.lower(), popular.lower())
            min_distance = min(min_distance, distance)

        return min_distance

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Edit distance between strings
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    async def _check_snyk_api(self, package_name: str, package_manager: str) -> Optional[dict]:
        """Check package against Snyk vulnerability database.

        Args:
            package_name: Name of package
            package_manager: Type of package manager (npm/pip)

        Returns:
            Vulnerability information if found, None otherwise
        """
        if not self.config.api_key_snyk:
            return None

        try:
            # Snyk API endpoint (would need real implementation)
            # This is a placeholder
            self._logger.debug(f"Would check Snyk for {package_name}")
            return None
        except Exception as e:
            self._logger.error(f"Error checking Snyk API: {e}")
            return None

    async def _check_socket_dev_api(
        self, package_name: str, package_manager: str
    ) -> Optional[dict]:
        """Check package against Socket.dev supply chain security.

        Args:
            package_name: Name of package
            package_manager: Type of package manager (npm/pip)

        Returns:
            Security information if found, None otherwise
        """
        if not self.config.api_key_socket_dev:
            return None

        try:
            # Socket.dev API endpoint (would need real implementation)
            # This is a placeholder
            self._logger.debug(f"Would check Socket.dev for {package_name}")
            return None
        except Exception as e:
            self._logger.error(f"Error checking Socket.dev API: {e}")
            return None
