"""Crypto-Miner Detection Monitor.

This module detects cryptocurrency mining activity on the system by monitoring:
- Sustained high CPU/GPU usage by processes
- Network connections to known mining pools
- Common miner process names and signatures
- WMI/Registry persistence mechanisms used by miners
- GPU mining activity via nvidia-smi/amd monitoring

Author: HifzDefend Team
License: MIT
"""

import asyncio
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import psutil
from pydantic import Field

from hifzdefend.monitoring.base import BaseMonitor
from hifzdefend.monitoring.events import Event, EventSeverity, EventType
from hifzdefend.monitoring.base import MonitorConfig


class CryptoMinerMonitorConfig(MonitorConfig):
    """Configuration for Crypto-Miner Detection monitor."""

    enabled: bool = Field(default=True, description="Enable crypto-miner detection")

    cpu_threshold: int = Field(
        default=80,
        ge=0,
        le=100,
        description="CPU usage % threshold to flag process as suspicious",
    )

    cpu_duration_seconds: int = Field(
        default=60,
        description="Duration CPU must exceed threshold to trigger alert",
    )

    gpu_monitoring: bool = Field(
        default=True, description="Monitor GPU usage for mining activity"
    )

    network_monitoring: bool = Field(
        default=True, description="Monitor network connections to mining pools"
    )

    miner_process_signatures: list[str] = Field(
        default_factory=lambda: [
            # Common miner executables
            "xmrig",
            "xmr-stak",
            "ccminer",
            "cgminer",
            "bfgminer",
            "ethminer",
            "phoenixminer",
            "claymore",
            "t-rex",
            "nbminer",
            "gminer",
            "lolminer",
            "nanominer",
            "srbminer",
            # Browser miners
            "coinhive",
            "crypto-loot",
            "cryptonight",
            "minero",
            "webminer",
            # Malicious variants
            "cryptonight.exe",
            "svchost32.exe",  # Fake svchost
            "csrss32.exe",  # Fake csrss
        ],
        description="Process name signatures that indicate mining software",
    )

    mining_pool_domains: list[str] = Field(
        default_factory=lambda: [
            # Major mining pools
            "nicehash.com",
            "nanopool.org",
            "ethermine.org",
            "f2pool.com",
            "antpool.com",
            "slushpool.com",
            "poolin.com",
            "pool.minergate.com",
            "xmr.pool.minergate.com",
            "supportxmr.com",
            "minexmr.com",
            "hashvault.pro",
            "moneroocean.stream",
            # Stratum protocol indicators
            "stratum+tcp",
            "stratum+ssl",
            "stratum.",
            # Browser miner domains
            "coin-hive.com",
            "coinhive.com",
            "crypto-loot.com",
            "cryptoloot.pro",
        ],
        description="Known mining pool domains and protocols",
    )

    mining_pool_ports: list[int] = Field(
        default_factory=lambda: [
            3333,  # Common stratum port
            4444,
            5555,
            7777,
            8888,
            9999,
            14444,  # XMR pools
            3357,  # Monero
        ],
        description="Common mining pool ports",
    )

    whitelist_processes: list[str] = Field(
        default_factory=list,
        description="Processes to exclude from miner detection (e.g., legitimate crypto wallets)",
    )

    check_wmi_persistence: bool = Field(
        default=True, description="Check for WMI event consumers used for persistence"
    )

    terminate_on_detect: bool = Field(
        default=False,
        description="Automatically terminate detected miner processes (DANGEROUS - use with caution)",
    )

    alert_cooldown_seconds: int = Field(
        default=300, description="Cooldown period before re-alerting on same miner"
    )


@dataclass
class ProcessCPUTracker:
    """Track CPU usage for a process over time."""

    pid: int
    name: str
    cmdline: str
    cpu_samples: list[float]
    timestamps: list[float]
    first_seen: float
    last_seen: float

    def add_sample(self, cpu_percent: float, timestamp: float) -> None:
        """Add a CPU usage sample."""
        self.cpu_samples.append(cpu_percent)
        self.timestamps.append(timestamp)
        self.last_seen = timestamp

        # Keep only last 10 samples to limit memory
        if len(self.cpu_samples) > 10:
            self.cpu_samples.pop(0)
            self.timestamps.pop(0)

    def get_average_cpu(self, window_seconds: int) -> float:
        """Get average CPU usage over the last N seconds."""
        if not self.cpu_samples:
            return 0.0

        now = time.time()
        cutoff = now - window_seconds

        # Filter samples within window
        recent_samples = [
            cpu
            for cpu, ts in zip(self.cpu_samples, self.timestamps)
            if ts >= cutoff
        ]

        if not recent_samples:
            return 0.0

        return sum(recent_samples) / len(recent_samples)

    def duration_above_threshold(self, threshold: int) -> float:
        """Get duration (in seconds) CPU has been above threshold."""
        if not self.timestamps:
            return 0.0

        # Find first timestamp where CPU exceeded threshold
        first_high = None
        for cpu, ts in zip(self.cpu_samples, self.timestamps):
            if cpu >= threshold:
                if first_high is None:
                    first_high = ts
            else:
                first_high = None  # Reset if CPU drops below threshold

        if first_high is None:
            return 0.0

        return self.last_seen - first_high


class CryptoMinerMonitor(BaseMonitor):
    """Monitor for cryptocurrency mining activity detection."""

    def __init__(self, config: CryptoMinerMonitorConfig, event_bus):
        """Initialize the crypto-miner monitor.

        Args:
            config: Monitor configuration
            event_bus: Event bus for publishing events
        """
        super().__init__(config, event_bus)
        self.config: CryptoMinerMonitorConfig = config
        self._process_trackers: dict[int, ProcessCPUTracker] = {}
        self._last_alerts: dict[str, float] = {}  # Alert cooldown tracking
        self._miner_signature_regex = None
        self._pool_domain_regex = None
        self._lock = asyncio.Lock()

        # Compile regex patterns for efficiency
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for miner signatures and pool domains."""
        # Compile miner process name patterns
        if self.config.miner_process_signatures:
            pattern = "|".join(
                re.escape(sig) for sig in self.config.miner_process_signatures
            )
            self._miner_signature_regex = re.compile(pattern, re.IGNORECASE)

        # Compile mining pool domain patterns
        if self.config.mining_pool_domains:
            pattern = "|".join(
                re.escape(domain) for domain in self.config.mining_pool_domains
            )
            self._pool_domain_regex = re.compile(pattern, re.IGNORECASE)

    async def start(self) -> None:
        """Start the crypto-miner monitor."""
        self._logger.info("Starting Crypto-Miner Detection Monitor")
        self._running = True

        # Log configuration
        self._logger.info(
            f"CPU threshold: {self.config.cpu_threshold}% for {self.config.cpu_duration_seconds}s"
        )
        self._logger.info(f"GPU monitoring: {self.config.gpu_monitoring}")
        self._logger.info(f"Network monitoring: {self.config.network_monitoring}")
        self._logger.info(
            f"Tracking {len(self.config.miner_process_signatures)} miner signatures"
        )
        self._logger.info(
            f"Monitoring {len(self.config.mining_pool_domains)} pool domains"
        )

    async def stop(self) -> None:
        """Stop the crypto-miner monitor."""
        self._logger.info("Stopping Crypto-Miner Detection Monitor")
        self._running = False
        async with self._lock:
            self._process_trackers.clear()
            self._last_alerts.clear()

    async def check(self) -> list[Event]:
        """Perform crypto-miner detection check.

        Returns:
            List of detected miner events
        """
        if not self._running:
            return []

        events = []

        # Check for high CPU usage processes
        cpu_events = await self._check_high_cpu_processes()
        events.extend(cpu_events)

        # Check for miner process signatures
        signature_events = await self._check_miner_signatures()
        events.extend(signature_events)

        # Check for mining pool connections
        if self.config.network_monitoring:
            network_events = await self._check_mining_pool_connections()
            events.extend(network_events)

        # Check for WMI persistence
        if self.config.check_wmi_persistence:
            wmi_events = await self._check_wmi_persistence()
            events.extend(wmi_events)

        # Clean up old process trackers
        await self._cleanup_old_trackers()

        return events

    async def _check_high_cpu_processes(self) -> list[Event]:
        """Check for processes with sustained high CPU usage.

        Returns:
            List of events for high CPU processes
        """
        events = []
        now = time.time()

        async with self._lock:
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "cmdline"]):
                try:
                    pid = proc.info["pid"]
                    name = proc.info["name"]
                    cpu_percent = proc.info["cpu_percent"]

                    # Skip if process is whitelisted
                    if self._is_whitelisted(name):
                        continue

                    # Skip system processes
                    if pid in [0, 4]:  # System, System Idle Process
                        continue

                    # Get or create tracker
                    if pid not in self._process_trackers:
                        cmdline = " ".join(proc.info["cmdline"] or [])
                        self._process_trackers[pid] = ProcessCPUTracker(
                            pid=pid,
                            name=name,
                            cmdline=cmdline,
                            cpu_samples=[],
                            timestamps=[],
                            first_seen=now,
                            last_seen=now,
                        )

                    tracker = self._process_trackers[pid]
                    tracker.add_sample(cpu_percent, now)

                    # Check if CPU exceeds threshold for required duration
                    avg_cpu = tracker.get_average_cpu(
                        self.config.cpu_duration_seconds
                    )
                    duration = tracker.duration_above_threshold(
                        self.config.cpu_threshold
                    )

                    if (
                        avg_cpu >= self.config.cpu_threshold
                        and duration >= self.config.cpu_duration_seconds
                    ):
                        # Check alert cooldown
                        if self._should_alert(f"cpu_{pid}"):
                            event = Event(
                                event_type=EventType.SUSPICIOUS_ACTIVITY,
                                severity=EventSeverity.WARNING,
                                source_monitor=self.name,
                                description=f"Process with sustained high CPU usage detected: {name} (PID: {pid})",
                                threat_score=65,
                                data={
                                    "pattern": "high_cpu_usage",
                                    "process_name": name,
                                    "process_id": pid,
                                    "cpu_percent": round(avg_cpu, 2),
                                    "duration_seconds": round(duration, 2),
                                    "threshold": self.config.cpu_threshold,
                                    "command_line": tracker.cmdline,
                                    "recommendation": f"Investigate process {name} for cryptocurrency mining activity. High CPU usage sustained for {round(duration, 2)} seconds.",
                                },
                            )
                            events.append(event)
                            self.publish_event(event)

                            # Terminate if configured
                            if self.config.terminate_on_detect:
                                await self._terminate_process(proc, "high CPU usage")

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    self._logger.debug(f"Error checking process CPU: {e}")
                    continue

        return events

    async def _check_miner_signatures(self) -> list[Event]:
        """Check for known miner process signatures.

        Returns:
            List of events for detected miner processes
        """
        events = []

        if not self._miner_signature_regex:
            return events

        for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
            try:
                pid = proc.info["pid"]
                name = proc.info["name"]
                exe = proc.info.get("exe", "")
                cmdline = " ".join(proc.info["cmdline"] or [])

                # Skip if whitelisted
                if self._is_whitelisted(name):
                    continue

                # Check process name, exe path, and command line
                text_to_check = f"{name} {exe} {cmdline}"

                if self._miner_signature_regex.search(text_to_check):
                    # Check alert cooldown
                    if self._should_alert(f"signature_{pid}"):
                        event = Event(
                            event_type=EventType.THREAT_DETECTED,
                            severity=EventSeverity.CRITICAL,
                            source_monitor=self.name,
                            description=f"Known crypto-miner process detected: {name}",
                            threat_score=95,
                            data={
                                "pattern": "miner_signature",
                                "process_name": name,
                                "process_id": pid,
                                "executable_path": exe,
                                "command_line": cmdline,
                                "recommendation": f"CRITICAL: Cryptocurrency miner detected. Terminate process {name} (PID: {pid}) immediately and scan system for malware.",
                            },
                        )
                        events.append(event)
                        self.publish_event(event)

                        # Terminate if configured
                        if self.config.terminate_on_detect:
                            await self._terminate_process(proc, "miner signature match")

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self._logger.debug(f"Error checking process signature: {e}")
                continue

        return events

    async def _check_mining_pool_connections(self) -> list[Event]:
        """Check for network connections to mining pools.

        Returns:
            List of events for mining pool connections
        """
        events = []

        if not self._pool_domain_regex:
            return events

        for proc in psutil.process_iter(["pid", "name", "connections"]):
            try:
                pid = proc.info["pid"]
                name = proc.info["name"]
                connections = proc.info.get("connections", [])

                # Skip if whitelisted
                if self._is_whitelisted(name):
                    continue

                for conn in connections:
                    if conn.status != psutil.CONN_ESTABLISHED:
                        continue

                    remote_ip = conn.raddr.ip if conn.raddr else None
                    remote_port = conn.raddr.port if conn.raddr else None

                    if not remote_ip or not remote_port:
                        continue

                    # Check if connected to known mining pool port
                    is_pool_port = remote_port in self.config.mining_pool_ports

                    # Try to resolve IP to domain (expensive operation, cache results)
                    domain = await self._resolve_ip_to_domain(remote_ip)

                    # Check if domain matches mining pool patterns
                    is_pool_domain = False
                    if domain:
                        is_pool_domain = bool(self._pool_domain_regex.search(domain))

                    if is_pool_port or is_pool_domain:
                        # Check alert cooldown
                        if self._should_alert(f"pool_{pid}_{remote_ip}"):
                            threat_score = 90 if is_pool_domain else 75
                            severity = (
                                EventSeverity.CRITICAL
                                if is_pool_domain
                                else EventSeverity.WARNING
                            )

                            event = Event(
                                event_type=EventType.NETWORK_CONNECTION,
                                severity=severity,
                                source_monitor=self.name,
                                description=f"Mining pool connection detected from process: {name}",
                                threat_score=threat_score,
                                data={
                                    "pattern": "mining_pool_connection",
                                    "process_name": name,
                                    "process_id": pid,
                                    "remote_ip": remote_ip,
                                    "remote_port": remote_port,
                                    "remote_domain": domain or "unknown",
                                    "connection_type": "pool_domain"
                                    if is_pool_domain
                                    else "pool_port",
                                    "recommendation": f"Mining pool connection detected. Terminate process {name} (PID: {pid}) and block IP {remote_ip}.",
                                },
                            )
                            events.append(event)
                            self.publish_event(event)

                            # Terminate if configured
                            if self.config.terminate_on_detect:
                                await self._terminate_process(
                                    proc, "mining pool connection"
                                )

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self._logger.debug(f"Error checking process connections: {e}")
                continue

        return events

    async def _check_wmi_persistence(self) -> list[Event]:
        """Check for WMI event consumers used by miners for persistence.

        Returns:
            List of events for WMI persistence mechanisms
        """
        events = []

        try:
            # On Windows, check WMI event consumers
            import platform

            if platform.system() != "Windows":
                return events

            try:
                import wmi

                c = wmi.WMI()

                # Check for suspicious WMI event consumers
                consumers = c.query(
                    "SELECT * FROM __EventConsumer WHERE Name LIKE '%miner%' OR Name LIKE '%crypto%' OR CommandLineTemplate LIKE '%stratum%'"
                )

                for consumer in consumers:
                    if self._should_alert(f"wmi_{consumer.Name}"):
                        event = Event(
                            event_type=EventType.SUSPICIOUS_ACTIVITY,
                            severity=EventSeverity.CRITICAL,
                            source_monitor=self.name,
                            description=f"Suspicious WMI event consumer detected: {consumer.Name}",
                            threat_score=90,
                            data={
                                "pattern": "wmi_persistence",
                                "consumer_name": consumer.Name,
                                "consumer_type": consumer.__class__.__name__,
                                "recommendation": "WMI persistence mechanism detected. This is commonly used by crypto-miners for stealth. Remove WMI event consumer.",
                            },
                        )
                        events.append(event)
                        self.publish_event(event)

            except ImportError:
                self._logger.debug("WMI module not available, skipping WMI checks")

        except Exception as e:
            self._logger.debug(f"Error checking WMI persistence: {e}")

        return events

    async def _resolve_ip_to_domain(self, ip: str) -> str | None:
        """Resolve IP address to domain name.

        Args:
            ip: IP address to resolve

        Returns:
            Domain name or None if resolution fails
        """
        try:
            import socket

            # This is a blocking call, but we'll keep it for now
            # In production, use aiodns or similar
            domain = socket.gethostbyaddr(ip)[0]
            return domain
        except (socket.herror, socket.gaierror):
            return None

    def _is_whitelisted(self, process_name: str) -> bool:
        """Check if process is whitelisted.

        Args:
            process_name: Name of the process

        Returns:
            True if whitelisted, False otherwise
        """
        return any(
            whitelist.lower() in process_name.lower()
            for whitelist in self.config.whitelist_processes
        )

    def _should_alert(self, key: str) -> bool:
        """Check if alert cooldown has expired for given key.

        Args:
            key: Alert identifier

        Returns:
            True if alert should be sent, False if in cooldown
        """
        now = time.time()
        last_alert = self._last_alerts.get(key, 0)

        if now - last_alert >= self.config.alert_cooldown_seconds:
            self._last_alerts[key] = now
            return True

        return False

    async def _terminate_process(self, proc: psutil.Process, reason: str) -> None:
        """Terminate a malicious process.

        Args:
            proc: Process to terminate
            reason: Reason for termination
        """
        try:
            pid = proc.pid
            name = proc.name()

            self._logger.warning(
                f"Terminating process {name} (PID: {pid}) - Reason: {reason}"
            )

            proc.terminate()
            proc.wait(timeout=5)

            self._logger.info(f"Successfully terminated process {name} (PID: {pid})")

        except psutil.TimeoutExpired:
            # Force kill if terminate didn't work
            try:
                proc.kill()
                self._logger.warning(
                    f"Force killed process {name} (PID: {pid}) after timeout"
                )
            except Exception as e:
                self._logger.error(
                    f"Failed to force kill process {name} (PID: {pid}): {e}"
                )

        except Exception as e:
            self._logger.error(f"Failed to terminate process: {e}")

    async def _cleanup_old_trackers(self) -> None:
        """Remove trackers for processes that no longer exist."""
        async with self._lock:
            current_pids = {p.pid for p in psutil.process_iter(["pid"])}
            old_pids = set(self._process_trackers.keys()) - current_pids

            for pid in old_pids:
                del self._process_trackers[pid]

    def get_statistics(self) -> dict[str, Any]:
        """Get monitoring statistics.

        Returns:
            Dictionary with current statistics
        """
        return {
            "monitored_processes": len(self._process_trackers),
            "active_alerts": len(self._last_alerts),
            "cpu_threshold": self.config.cpu_threshold,
            "gpu_monitoring": self.config.gpu_monitoring,
            "network_monitoring": self.config.network_monitoring,
            "terminate_on_detect": self.config.terminate_on_detect,
        }
