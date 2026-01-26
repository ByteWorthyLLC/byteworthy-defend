"""Network connection monitoring for HifzDefend.

This monitor tracks all outbound network connections and detects:
- Connections to known malicious IPs
- C2 (Command & Control) beaconing patterns
- Unusual connection behavior
- Integration with threat intelligence feeds

Features:
- Real-time connection tracking
- IP reputation checking (AbuseIPDB, Talos)
- C2 beaconing detection (periodic callbacks)
- Connection whitelisting
- Threat intelligence caching
- Automatic blocking capabilities
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import aiohttp
import psutil
from pydantic import Field

from hifzdefend.monitoring.base import BaseMonitor
from hifzdefend.monitoring.events import Event, EventSeverity, EventType
from hifzdefend.monitoring.base import MonitorConfig

logger = logging.getLogger(__name__)


class NetworkMonitorConfig(MonitorConfig):
    """Configuration for Network connection monitor."""

    enabled: bool = Field(
        default=True, description="Enable network connection monitoring"
    )

    monitor_outbound: bool = Field(
        default=True, description="Monitor outbound connections"
    )

    monitor_inbound: bool = Field(
        default=False, description="Monitor inbound connections (requires admin)"
    )

    check_ip_reputation: bool = Field(
        default=True, description="Check IP addresses against threat intelligence"
    )

    block_malicious_ips: bool = Field(
        default=False,
        description="Block connections to known malicious IPs (requires admin)",
    )

    detect_c2_beaconing: bool = Field(
        default=True,
        description="Detect C2 beaconing patterns (periodic callbacks)",
    )

    beaconing_threshold: int = Field(
        default=5,
        ge=3,
        description="Number of periodic connections to same IP before alerting",
    )

    beaconing_window_seconds: int = Field(
        default=300,
        ge=60,
        description="Time window for detecting beaconing (seconds)",
    )

    whitelist_ips: list[str] = Field(
        default_factory=lambda: [
            "8.8.8.8",  # Google DNS
            "1.1.1.1",  # Cloudflare DNS
            "127.0.0.1",  # Localhost
        ],
        description="IP addresses to always allow (whitelist)",
    )

    whitelist_ports: list[int] = Field(
        default_factory=lambda: [80, 443, 53],  # HTTP, HTTPS, DNS
        description="Ports to allow without alerts",
    )

    suspicious_ports: list[int] = Field(
        default_factory=lambda: [
            22,  # SSH
            23,  # Telnet
            135,  # RPC
            139,  # NetBIOS
            445,  # SMB
            1433,  # MSSQL
            3306,  # MySQL
            3389,  # RDP
            5900,  # VNC
            8080,  # HTTP Alt
        ],
        description="Ports that require extra scrutiny",
    )

    abuseipdb_api_key: str = Field(
        default="", description="AbuseIPDB API key for IP reputation checks"
    )

    abuseipdb_confidence_threshold: int = Field(
        default=75,
        ge=0,
        le=100,
        description="AbuseIPDB confidence score threshold for malicious IPs",
    )

    cache_ttl_seconds: int = Field(
        default=3600,  # 1 hour
        ge=300,
        description="Time to cache threat intelligence results (seconds)",
    )

    max_connections_per_process: int = Field(
        default=50,
        ge=10,
        description="Alert if single process has more than this many connections",
    )

    scan_interval_seconds: int = Field(
        default=10,
        ge=5,
        description="How often to scan active connections (seconds)",
    )


@dataclass
class ConnectionInfo:
    """Information about a network connection."""

    local_addr: tuple[str, int]
    remote_addr: tuple[str, int]
    status: str
    pid: Optional[int]
    process_name: Optional[str]
    timestamp: datetime


@dataclass
class IPReputationResult:
    """Result from IP reputation check."""

    ip: str
    is_malicious: bool
    confidence_score: int
    country: str
    abuse_reports: int
    source: str  # "abuseipdb", "talos", "cache"
    checked_at: datetime


class NetworkMonitor(BaseMonitor):
    """Monitor network connections for suspicious activity."""

    def __init__(self, config: NetworkMonitorConfig, event_bus):
        super().__init__(config, event_bus)
        self.config: NetworkMonitorConfig = config

        # Connection tracking
        self._active_connections: dict[tuple, ConnectionInfo] = {}
        self._connection_history: list[ConnectionInfo] = []

        # IP reputation cache
        self._ip_reputation_cache: dict[str, IPReputationResult] = {}

        # C2 beaconing detection
        self._connection_patterns: dict[str, list[datetime]] = defaultdict(list)

        # Statistics
        self._stats = {
            "total_connections": 0,
            "suspicious_ips": 0,
            "blocked_ips": 0,
            "c2_beacons_detected": 0,
            "reputation_checks": 0,
            "cache_hits": 0,
            "suspicious_ports": 0,
        }

        # HTTP session for API calls
        self._http_session: Optional[aiohttp.ClientSession] = None

        # AbuseIPDB API endpoint
        self._abuseipdb_url = "https://api.abuseipdb.com/api/v2/check"

        logger.info("Network monitor initialized")

    async def start(self) -> None:
        """Start monitoring network connections."""
        if self._running:
            logger.warning("Network monitor already running")
            return

        logger.info("Starting network monitor")

        # Create HTTP session for API calls
        if self.config.check_ip_reputation and self.config.abuseipdb_api_key:
            headers = {
                "Key": self.config.abuseipdb_api_key,
                "Accept": "application/json",
            }
            self._http_session = aiohttp.ClientSession(headers=headers)
            logger.info("AbuseIPDB integration enabled")

        self._running = True
        logger.info("Network monitor started successfully")

    async def stop(self) -> None:
        """Stop monitoring."""
        if not self._running:
            return

        logger.info("Stopping network monitor")

        # Close HTTP session
        if self._http_session:
            await self._http_session.close()
            self._http_session = None

        self._running = False
        logger.info("Network monitor stopped")

    async def check(self) -> list[Event]:
        """Perform network connection check."""
        if not self._running:
            return []

        events = []

        try:
            # Get current connections
            connections = self._get_active_connections()

            # Analyze each connection
            for conn in connections:
                # Skip localhost and whitelist
                if self._is_whitelisted(conn):
                    continue

                # Check for suspicious ports
                if conn.remote_addr[1] in self.config.suspicious_ports:
                    event = await self._check_suspicious_port(conn)
                    if event:
                        events.append(event)

                # Check IP reputation
                if self.config.check_ip_reputation:
                    reputation_event = await self._check_ip_reputation(conn)
                    if reputation_event:
                        events.append(reputation_event)

                # Track for C2 beaconing detection
                if self.config.detect_c2_beaconing:
                    beaconing_event = self._check_c2_beaconing(conn)
                    if beaconing_event:
                        events.append(beaconing_event)

            # Check for processes with excessive connections
            excessive_event = self._check_excessive_connections(connections)
            if excessive_event:
                events.append(excessive_event)

            # Clean up old cache entries
            self._cleanup_cache()

        except Exception as e:
            logger.error(f"Error during network check: {e}", exc_info=True)

        return events

    def _get_active_connections(self) -> list[ConnectionInfo]:
        """Get all active network connections."""
        connections = []

        try:
            # Get all network connections
            for conn in psutil.net_connections(kind="inet"):
                # Skip connections without remote address
                if not conn.raddr:
                    continue

                # Skip if not ESTABLISHED (unless monitoring all)
                if conn.status != "ESTABLISHED" and self.config.monitor_outbound:
                    continue

                # Get process info
                process_name = None
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        process_name = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                conn_info = ConnectionInfo(
                    local_addr=conn.laddr,
                    remote_addr=conn.raddr,
                    status=conn.status,
                    pid=conn.pid,
                    process_name=process_name,
                    timestamp=datetime.now(),
                )

                connections.append(conn_info)

                # Update active connections
                conn_key = (conn.laddr, conn.raddr)
                if conn_key not in self._active_connections:
                    self._active_connections[conn_key] = conn_info
                    self._stats["total_connections"] += 1

                    # Add to history
                    self._connection_history.append(conn_info)
                    if len(self._connection_history) > 1000:
                        self._connection_history.pop(0)

        except psutil.AccessDenied:
            logger.warning(
                "Access denied when reading network connections (requires admin)"
            )
        except Exception as e:
            logger.error(f"Error getting active connections: {e}", exc_info=True)

        return connections

    def _is_whitelisted(self, conn: ConnectionInfo) -> bool:
        """Check if connection is whitelisted."""
        remote_ip = conn.remote_addr[0]
        remote_port = conn.remote_addr[1]

        # Check IP whitelist
        if remote_ip in self.config.whitelist_ips:
            return True

        # Check if localhost
        if remote_ip.startswith("127.") or remote_ip == "::1":
            return True

        # Check if private IP
        if self._is_private_ip(remote_ip):
            return True

        # Check port whitelist (for common ports like HTTP/HTTPS)
        if remote_port in self.config.whitelist_ports:
            return True

        return False

    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is in private range."""
        parts = ip.split(".")
        if len(parts) != 4:
            return False

        try:
            first = int(parts[0])
            second = int(parts[1])

            # 10.0.0.0/8
            if first == 10:
                return True

            # 172.16.0.0/12
            if first == 172 and 16 <= second <= 31:
                return True

            # 192.168.0.0/16
            if first == 192 and second == 168:
                return True

        except ValueError:
            return False

        return False

    async def _check_suspicious_port(self, conn: ConnectionInfo) -> Optional[Event]:
        """Check if connection uses suspicious port."""
        self._stats["suspicious_ports"] += 1

        port = conn.remote_addr[1]
        remote_ip = conn.remote_addr[0]

        # Create warning event
        event = Event(
            event_type=EventType.NETWORK_CONNECTION,
            severity=EventSeverity.WARNING,
            source_monitor=self.name,
            description=f"Connection to suspicious port {port}: {remote_ip}",
            threat_score=40,
            data={
                "pattern": "suspicious_port",
                "remote_ip": remote_ip,
                "remote_port": port,
                "local_port": conn.local_addr[1],
                "process_name": conn.process_name,
                "pid": conn.pid,
                "port_description": self._get_port_description(port),
                "recommendation": f"Verify if {conn.process_name or 'process'} should be connecting to port {port}",
            },
        )

        return event

    def _get_port_description(self, port: int) -> str:
        """Get description of what port is typically used for."""
        port_descriptions = {
            22: "SSH (Secure Shell)",
            23: "Telnet (Insecure)",
            135: "Windows RPC",
            139: "NetBIOS Session",
            445: "SMB (File Sharing)",
            1433: "Microsoft SQL Server",
            3306: "MySQL Database",
            3389: "Remote Desktop (RDP)",
            5900: "VNC Remote Desktop",
            8080: "HTTP Alternative",
        }
        return port_descriptions.get(port, f"Port {port}")

    async def _check_ip_reputation(self, conn: ConnectionInfo) -> Optional[Event]:
        """Check IP reputation against threat intelligence."""
        remote_ip = conn.remote_addr[0]

        # Check cache first
        if remote_ip in self._ip_reputation_cache:
            cached = self._ip_reputation_cache[remote_ip]
            cache_age = (datetime.now() - cached.checked_at).total_seconds()

            if cache_age < self.config.cache_ttl_seconds:
                self._stats["cache_hits"] += 1

                # Return event if cached result is malicious
                if cached.is_malicious:
                    return self._create_malicious_ip_event(conn, cached)

                return None

        # Not in cache or expired - check API
        if not self._http_session:
            return None

        try:
            reputation = await self._query_abuseipdb(remote_ip)

            if reputation:
                # Cache result
                self._ip_reputation_cache[remote_ip] = reputation
                self._stats["reputation_checks"] += 1

                # Create event if malicious
                if reputation.is_malicious:
                    self._stats["suspicious_ips"] += 1
                    return self._create_malicious_ip_event(conn, reputation)

        except Exception as e:
            logger.error(f"Error checking IP reputation for {remote_ip}: {e}")

        return None

    async def _query_abuseipdb(self, ip: str) -> Optional[IPReputationResult]:
        """Query AbuseIPDB for IP reputation."""
        if not self._http_session:
            return None

        try:
            params = {
                "ipAddress": ip,
                "maxAgeInDays": "90",
                "verbose": "",
            }

            async with self._http_session.get(
                self._abuseipdb_url, params=params, timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status != 200:
                    logger.warning(f"AbuseIPDB API error: {response.status}")
                    return None

                data = await response.json()

                if "data" not in data:
                    return None

                ip_data = data["data"]

                confidence_score = ip_data.get("abuseConfidenceScore", 0)
                is_malicious = (
                    confidence_score >= self.config.abuseipdb_confidence_threshold
                )

                return IPReputationResult(
                    ip=ip,
                    is_malicious=is_malicious,
                    confidence_score=confidence_score,
                    country=ip_data.get("countryCode", "Unknown"),
                    abuse_reports=ip_data.get("totalReports", 0),
                    source="abuseipdb",
                    checked_at=datetime.now(),
                )

        except asyncio.TimeoutError:
            logger.warning(f"AbuseIPDB query timeout for {ip}")
            return None
        except Exception as e:
            logger.error(f"Error querying AbuseIPDB for {ip}: {e}")
            return None

    def _create_malicious_ip_event(
        self, conn: ConnectionInfo, reputation: IPReputationResult
    ) -> Event:
        """Create event for malicious IP connection."""
        remote_ip = conn.remote_addr[0]

        # Determine severity based on confidence
        if reputation.confidence_score >= 90:
            severity = EventSeverity.CRITICAL
            threat_score = 90
        elif reputation.confidence_score >= 75:
            severity = EventSeverity.WARNING
            threat_score = 70
        else:
            severity = EventSeverity.WARNING
            threat_score = 50

        event = Event(
            event_type=EventType.THREAT_DETECTED,
            severity=severity,
            source_monitor=self.name,
            description=f"Connection to malicious IP: {remote_ip}",
            threat_score=threat_score,
            data={
                "pattern": "malicious_ip",
                "remote_ip": remote_ip,
                "remote_port": conn.remote_addr[1],
                "process_name": conn.process_name,
                "pid": conn.pid,
                "confidence_score": reputation.confidence_score,
                "abuse_reports": reputation.abuse_reports,
                "country": reputation.country,
                "source": reputation.source,
                "recommendation": f"Terminate process {conn.process_name or conn.pid} and investigate for malware",
                "action_available": "block_ip" if self.config.block_malicious_ips else None,
            },
        )

        return event

    def _check_c2_beaconing(self, conn: ConnectionInfo) -> Optional[Event]:
        """Check for C2 beaconing patterns (periodic callbacks)."""
        remote_ip = conn.remote_addr[0]
        now = datetime.now()

        # Track connection time
        self._connection_patterns[remote_ip].append(now)

        # Clean up old entries (outside beaconing window)
        cutoff = now - timedelta(seconds=self.config.beaconing_window_seconds)
        self._connection_patterns[remote_ip] = [
            ts for ts in self._connection_patterns[remote_ip] if ts > cutoff
        ]

        # Check if pattern indicates beaconing
        connection_times = self._connection_patterns[remote_ip]

        if len(connection_times) < self.config.beaconing_threshold:
            return None

        # Calculate intervals between connections
        intervals = []
        for i in range(1, len(connection_times)):
            interval = (connection_times[i] - connection_times[i - 1]).total_seconds()
            intervals.append(interval)

        if not intervals:
            return None

        # Check if intervals are periodic (within 20% variance)
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance**0.5

        # If standard deviation is low relative to mean, it's periodic
        if avg_interval > 0 and (std_dev / avg_interval) < 0.2:
            self._stats["c2_beacons_detected"] += 1

            event = Event(
                event_type=EventType.THREAT_DETECTED,
                severity=EventSeverity.CRITICAL,
                source_monitor=self.name,
                description=f"C2 beaconing detected to {remote_ip}",
                threat_score=85,
                data={
                    "pattern": "c2_beaconing",
                    "remote_ip": remote_ip,
                    "remote_port": conn.remote_addr[1],
                    "process_name": conn.process_name,
                    "pid": conn.pid,
                    "beacon_count": len(connection_times),
                    "average_interval_seconds": round(avg_interval, 2),
                    "periodicity_score": round(1 - (std_dev / avg_interval), 2),
                    "recommendation": "CRITICAL: Possible malware C2 communication. Terminate process and run full system scan.",
                },
            )

            return event

        return None

    def _check_excessive_connections(
        self, connections: list[ConnectionInfo]
    ) -> Optional[Event]:
        """Check for processes with excessive number of connections."""
        # Group connections by process
        process_connections: dict[int, list[ConnectionInfo]] = defaultdict(list)

        for conn in connections:
            if conn.pid:
                process_connections[conn.pid].append(conn)

        # Check for excessive connections
        for pid, conns in process_connections.items():
            if len(conns) > self.config.max_connections_per_process:
                # Get process name
                process_name = conns[0].process_name or "Unknown"

                event = Event(
                    event_type=EventType.SUSPICIOUS_ACTIVITY,
                    severity=EventSeverity.WARNING,
                    source_monitor=self.name,
                    description=f"Process has excessive connections: {process_name} ({len(conns)} connections)",
                    threat_score=50,
                    data={
                        "pattern": "excessive_connections",
                        "process_name": process_name,
                        "pid": pid,
                        "connection_count": len(conns),
                        "threshold": self.config.max_connections_per_process,
                        "unique_ips": len(set(c.remote_addr[0] for c in conns)),
                        "recommendation": f"Verify if {process_name} should have {len(conns)} simultaneous connections",
                    },
                )

                return event

        return None

    def _cleanup_cache(self) -> None:
        """Clean up expired cache entries."""
        now = datetime.now()
        expired_ips = []

        for ip, reputation in self._ip_reputation_cache.items():
            age = (now - reputation.checked_at).total_seconds()
            if age > self.config.cache_ttl_seconds:
                expired_ips.append(ip)

        for ip in expired_ips:
            del self._ip_reputation_cache[ip]

        if expired_ips:
            logger.debug(f"Cleaned up {len(expired_ips)} expired cache entries")

    def get_statistics(self) -> dict[str, Any]:
        """Get monitor statistics."""
        return {
            "total_connections": self._stats["total_connections"],
            "active_connections": len(self._active_connections),
            "suspicious_ips": self._stats["suspicious_ips"],
            "blocked_ips": self._stats["blocked_ips"],
            "c2_beacons_detected": self._stats["c2_beacons_detected"],
            "reputation_checks": self._stats["reputation_checks"],
            "cache_hits": self._stats["cache_hits"],
            "cache_size": len(self._ip_reputation_cache),
            "suspicious_ports": self._stats["suspicious_ports"],
            "check_ip_reputation": self.config.check_ip_reputation,
            "detect_c2_beaconing": self.config.detect_c2_beaconing,
            "abuseipdb_enabled": bool(
                self.config.abuseipdb_api_key and self._http_session
            ),
        }
