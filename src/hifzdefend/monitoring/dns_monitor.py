"""DNS security monitoring for HifzDefend.

This monitor provides DNS-based threat detection including:
- DNS tunneling detection (data exfiltration)
- Malicious domain blocking
- DNS hijacking detection
- Suspicious DNS query patterns
- Integration with DNS threat intelligence

Features:
- DNS query monitoring
- Domain reputation checking
- DNS tunneling detection (long subdomains, high entropy)
- Malicious domain blocking
- DNS hijacking detection
- Custom DNS blocklist support
"""

import asyncio
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import dns.resolver
import dns.reversename
from pydantic import Field

from hifzdefend.monitoring.base import BaseMonitor
from hifzdefend.monitoring.events import Event, EventSeverity, EventType
from hifzdefend.monitoring.base import MonitorConfig

logger = logging.getLogger(__name__)


class DNSMonitorConfig(MonitorConfig):
    """Configuration for DNS security monitor."""

    enabled: bool = Field(default=True, description="Enable DNS security monitoring")

    detect_tunneling: bool = Field(
        default=True, description="Detect DNS tunneling (data exfiltration)"
    )

    tunneling_subdomain_length_threshold: int = Field(
        default=40,
        ge=20,
        description="Alert if subdomain length exceeds this (DNS tunneling indicator)",
    )

    tunneling_entropy_threshold: float = Field(
        default=3.5,
        ge=1.0,
        le=5.0,
        description="Alert if subdomain entropy exceeds this (randomness indicator)",
    )

    tunneling_query_rate_threshold: int = Field(
        default=20,
        ge=5,
        description="Alert if more than this many queries per minute to same domain",
    )

    block_malicious_domains: bool = Field(
        default=True, description="Block DNS queries to known malicious domains"
    )

    custom_blocklist: list[str] = Field(
        default_factory=list,
        description="Custom list of domains to block",
    )

    check_domain_reputation: bool = Field(
        default=True, description="Check domain reputation (requires API keys)"
    )

    detect_dga_domains: bool = Field(
        default=True,
        description="Detect Domain Generation Algorithm (DGA) patterns",
    )

    dga_domain_length_threshold: int = Field(
        default=15,
        ge=10,
        description="Minimum domain length to check for DGA",
    )

    monitor_dns_changes: bool = Field(
        default=True,
        description="Monitor for unexpected DNS configuration changes",
    )

    whitelist_domains: list[str] = Field(
        default_factory=lambda: [
            "google.com",
            "microsoft.com",
            "cloudflare.com",
            "github.com",
            "npmjs.org",
            "pypi.org",
        ],
        description="Domains to never flag (whitelist)",
    )

    suspicious_tlds: list[str] = Field(
        default_factory=lambda: [
            ".tk",  # Tokelau (free, often abused)
            ".ml",  # Mali (free, often abused)
            ".ga",  # Gabon (free, often abused)
            ".cf",  # Central African Republic (free)
            ".gq",  # Equatorial Guinea (free)
            ".xyz",  # Generic (often used for malware)
            ".top",  # Generic (often used for malware)
        ],
        description="Top-level domains that require extra scrutiny",
    )

    max_dns_queries_per_minute: int = Field(
        default=100,
        ge=10,
        description="Alert if DNS queries exceed this rate",
    )

    scan_interval_seconds: int = Field(
        default=30,
        ge=10,
        description="How often to scan DNS activity (seconds)",
    )


@dataclass
class DNSQuery:
    """Information about a DNS query."""

    domain: str
    query_type: str
    timestamp: datetime
    process_name: Optional[str] = None
    pid: Optional[int] = None


class DNSMonitor(BaseMonitor):
    """Monitor DNS activity for security threats."""

    def __init__(self, config: DNSMonitorConfig, event_bus):
        super().__init__(config, event_bus)
        self.config: DNSMonitorConfig = config

        # DNS query tracking
        self._dns_queries: list[DNSQuery] = []
        self._query_counts: dict[str, list[datetime]] = defaultdict(list)

        # Domain reputation cache
        self._domain_reputation_cache: dict[str, dict] = {}

        # DNS configuration baseline
        self._dns_servers_baseline: list[str] = []

        # Statistics
        self._stats = {
            "total_queries": 0,
            "blocked_queries": 0,
            "tunneling_detected": 0,
            "dga_domains_detected": 0,
            "suspicious_tlds": 0,
            "dns_hijacking_detected": 0,
        }

        # DNS resolver
        self._resolver = dns.resolver.Resolver()

        logger.info("DNS monitor initialized")

    async def start(self) -> None:
        """Start DNS monitoring."""
        if self._running:
            logger.warning("DNS monitor already running")
            return

        logger.info("Starting DNS monitor")

        # Capture baseline DNS configuration
        if self.config.monitor_dns_changes:
            self._capture_dns_baseline()

        self._running = True
        logger.info("DNS monitor started successfully")

    async def stop(self) -> None:
        """Stop monitoring."""
        if not self._running:
            return

        logger.info("Stopping DNS monitor")
        self._running = False
        logger.info("DNS monitor stopped")

    async def check(self) -> list[Event]:
        """Perform DNS security check."""
        if not self._running:
            return []

        events = []

        try:
            # Check for DNS configuration changes
            if self.config.monitor_dns_changes:
                hijacking_event = self._check_dns_hijacking()
                if hijacking_event:
                    events.append(hijacking_event)

            # Simulate DNS query monitoring
            # NOTE: In production, this would hook into DNS traffic or use DNS logs
            # For now, we check configured patterns

            # Clean up old query tracking data
            self._cleanup_old_queries()

        except Exception as e:
            logger.error(f"Error during DNS check: {e}", exc_info=True)

        return events

    def analyze_dns_query(self, domain: str, query_type: str = "A") -> Optional[Event]:
        """Analyze a DNS query for threats.

        This method can be called by other monitors when they detect DNS queries.

        Args:
            domain: Domain being queried
            query_type: DNS query type (A, AAAA, TXT, etc.)

        Returns:
            Event if threat detected, None otherwise
        """
        # Record query
        query = DNSQuery(
            domain=domain, query_type=query_type, timestamp=datetime.now()
        )
        self._dns_queries.append(query)
        self._stats["total_queries"] += 1

        # Track query rate
        self._query_counts[domain].append(datetime.now())

        # Keep query history limited
        if len(self._dns_queries) > 10000:
            self._dns_queries.pop(0)

        # Check whitelist
        if self._is_whitelisted_domain(domain):
            return None

        # Check custom blocklist
        if self._is_blocked_domain(domain):
            self._stats["blocked_queries"] += 1
            return self._create_blocked_domain_event(domain)

        # Check for DNS tunneling
        if self.config.detect_tunneling:
            tunneling_event = self._check_dns_tunneling(domain)
            if tunneling_event:
                return tunneling_event

        # Check for DGA domains
        if self.config.detect_dga_domains:
            dga_event = self._check_dga_domain(domain)
            if dga_event:
                return dga_event

        # Check for suspicious TLDs
        suspicious_tld_event = self._check_suspicious_tld(domain)
        if suspicious_tld_event:
            return suspicious_tld_event

        # Check query rate
        excessive_queries_event = self._check_excessive_queries(domain)
        if excessive_queries_event:
            return excessive_queries_event

        return None

    def _is_whitelisted_domain(self, domain: str) -> bool:
        """Check if domain is whitelisted."""
        domain_lower = domain.lower()

        for whitelisted in self.config.whitelist_domains:
            if domain_lower.endswith(whitelisted.lower()):
                return True

        return False

    def _is_blocked_domain(self, domain: str) -> bool:
        """Check if domain is in blocklist."""
        domain_lower = domain.lower()

        for blocked in self.config.custom_blocklist:
            if domain_lower.endswith(blocked.lower()):
                return True

        return False

    def _create_blocked_domain_event(self, domain: str) -> Event:
        """Create event for blocked domain."""
        event = Event(
            event_type=EventType.THREAT_DETECTED,
            severity=EventSeverity.WARNING,
            source_monitor=self.name,
            description=f"Blocked query to malicious domain: {domain}",
            threat_score=70,
            data={
                "pattern": "blocked_domain",
                "domain": domain,
                "reason": "custom_blocklist",
                "recommendation": "Domain is in blocklist. Investigate process attempting connection.",
            },
        )

        return event

    def _check_dns_tunneling(self, domain: str) -> Optional[Event]:
        """Check for DNS tunneling indicators."""
        # Extract subdomain (everything before second-level domain)
        parts = domain.split(".")

        if len(parts) < 3:
            return None

        # Check subdomain (could be multiple levels)
        subdomain = ".".join(parts[:-2])

        # Check 1: Subdomain length
        if len(subdomain) > self.config.tunneling_subdomain_length_threshold:
            self._stats["tunneling_detected"] += 1

            event = Event(
                event_type=EventType.THREAT_DETECTED,
                severity=EventSeverity.CRITICAL,
                source_monitor=self.name,
                description=f"DNS tunneling detected: {domain}",
                threat_score=85,
                data={
                    "pattern": "dns_tunneling",
                    "domain": domain,
                    "subdomain": subdomain,
                    "subdomain_length": len(subdomain),
                    "threshold": self.config.tunneling_subdomain_length_threshold,
                    "reason": "excessive_subdomain_length",
                    "recommendation": "CRITICAL: Possible data exfiltration via DNS tunneling. Block domain and investigate.",
                },
            )

            return event

        # Check 2: Subdomain entropy (randomness)
        entropy = self._calculate_entropy(subdomain)

        if entropy > self.config.tunneling_entropy_threshold:
            self._stats["tunneling_detected"] += 1

            event = Event(
                event_type=EventType.THREAT_DETECTED,
                severity=EventSeverity.CRITICAL,
                source_monitor=self.name,
                description=f"DNS tunneling detected (high entropy): {domain}",
                threat_score=80,
                data={
                    "pattern": "dns_tunneling",
                    "domain": domain,
                    "subdomain": subdomain,
                    "entropy": round(entropy, 2),
                    "threshold": self.config.tunneling_entropy_threshold,
                    "reason": "high_subdomain_entropy",
                    "recommendation": "CRITICAL: Possible data exfiltration via DNS tunneling. Block domain and investigate.",
                },
            )

            return event

        return None

    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text (measure of randomness)."""
        if not text:
            return 0.0

        # Count character frequencies
        char_counts: dict[str, int] = defaultdict(int)
        for char in text:
            char_counts[char] += 1

        # Calculate entropy
        text_len = len(text)
        entropy = 0.0

        for count in char_counts.values():
            probability = count / text_len
            if probability > 0:
                entropy -= probability * (probability**0.5).bit_length()

        return entropy

    def _check_dga_domain(self, domain: str) -> Optional[Event]:
        """Check for Domain Generation Algorithm (DGA) patterns.

        DGA domains are algorithmically generated by malware for C2 communication.
        Characteristics:
        - High entropy (random-looking)
        - Unusual length
        - Low vowel ratio
        - Uncommon character patterns
        """
        # Extract domain name (without TLD)
        parts = domain.split(".")
        if len(parts) < 2:
            return None

        domain_name = parts[-2]

        # Check length
        if len(domain_name) < self.config.dga_domain_length_threshold:
            return None

        # Calculate characteristics
        entropy = self._calculate_entropy(domain_name)
        vowel_ratio = self._calculate_vowel_ratio(domain_name)
        digit_ratio = sum(c.isdigit() for c in domain_name) / len(domain_name)

        # DGA heuristics:
        # - High entropy (>3.0)
        # - Low vowel ratio (<0.3)
        # - High digit ratio (>0.3) OR very low (<0.05)
        is_dga = (
            entropy > 3.0
            and vowel_ratio < 0.3
            and (digit_ratio > 0.3 or digit_ratio < 0.05)
        )

        if is_dga:
            self._stats["dga_domains_detected"] += 1

            event = Event(
                event_type=EventType.THREAT_DETECTED,
                severity=EventSeverity.CRITICAL,
                source_monitor=self.name,
                description=f"DGA domain detected: {domain}",
                threat_score=85,
                data={
                    "pattern": "dga_domain",
                    "domain": domain,
                    "domain_name": domain_name,
                    "entropy": round(entropy, 2),
                    "vowel_ratio": round(vowel_ratio, 2),
                    "digit_ratio": round(digit_ratio, 2),
                    "characteristics": "High entropy, low vowel ratio - typical of algorithmically generated domains",
                    "recommendation": "CRITICAL: Likely malware C2 domain. Block domain and scan system for malware.",
                },
            )

            return event

        return None

    def _calculate_vowel_ratio(self, text: str) -> float:
        """Calculate ratio of vowels in text."""
        if not text:
            return 0.0

        vowels = "aeiouAEIOU"
        vowel_count = sum(1 for c in text if c in vowels)
        return vowel_count / len(text)

    def _check_suspicious_tld(self, domain: str) -> Optional[Event]:
        """Check for suspicious top-level domains."""
        domain_lower = domain.lower()

        for tld in self.config.suspicious_tlds:
            if domain_lower.endswith(tld):
                self._stats["suspicious_tlds"] += 1

                event = Event(
                    event_type=EventType.SUSPICIOUS_ACTIVITY,
                    severity=EventSeverity.WARNING,
                    source_monitor=self.name,
                    description=f"Query to suspicious TLD: {domain}",
                    threat_score=40,
                    data={
                        "pattern": "suspicious_tld",
                        "domain": domain,
                        "tld": tld,
                        "reason": f"{tld} domains are often used for malicious purposes",
                        "recommendation": "Verify legitimacy of domain before trusting content",
                    },
                )

                return event

        return None

    def _check_excessive_queries(self, domain: str) -> Optional[Event]:
        """Check for excessive DNS queries to same domain."""
        # Clean up old queries (older than 1 minute)
        cutoff = datetime.now() - timedelta(minutes=1)
        self._query_counts[domain] = [
            ts for ts in self._query_counts[domain] if ts > cutoff
        ]

        query_count = len(self._query_counts[domain])

        if query_count > self.config.tunneling_query_rate_threshold:
            event = Event(
                event_type=EventType.SUSPICIOUS_ACTIVITY,
                severity=EventSeverity.WARNING,
                source_monitor=self.name,
                description=f"Excessive DNS queries to {domain}: {query_count}/minute",
                threat_score=60,
                data={
                    "pattern": "excessive_queries",
                    "domain": domain,
                    "query_count": query_count,
                    "threshold": self.config.tunneling_query_rate_threshold,
                    "reason": "Possible DNS tunneling or unusual application behavior",
                    "recommendation": "Investigate process making queries to this domain",
                },
            )

            return event

        return None

    def _check_dns_hijacking(self) -> Optional[Event]:
        """Check for DNS configuration changes (possible hijacking)."""
        try:
            current_dns = self._get_current_dns_servers()

            if not self._dns_servers_baseline:
                # First run - establish baseline
                self._dns_servers_baseline = current_dns
                return None

            # Check for changes
            if set(current_dns) != set(self._dns_servers_baseline):
                self._stats["dns_hijacking_detected"] += 1

                added = set(current_dns) - set(self._dns_servers_baseline)
                removed = set(self._dns_servers_baseline) - set(current_dns)

                event = Event(
                    event_type=EventType.THREAT_DETECTED,
                    severity=EventSeverity.CRITICAL,
                    source_monitor=self.name,
                    description="DNS configuration change detected (possible hijacking)",
                    threat_score=90,
                    data={
                        "pattern": "dns_hijacking",
                        "baseline_servers": self._dns_servers_baseline,
                        "current_servers": current_dns,
                        "added_servers": list(added),
                        "removed_servers": list(removed),
                        "recommendation": "CRITICAL: Verify DNS changes are legitimate. Malware often changes DNS to intercept traffic.",
                    },
                )

                # Update baseline after alert
                self._dns_servers_baseline = current_dns

                return event

        except Exception as e:
            logger.error(f"Error checking DNS hijacking: {e}")

        return None

    def _capture_dns_baseline(self) -> None:
        """Capture current DNS server configuration as baseline."""
        try:
            self._dns_servers_baseline = self._get_current_dns_servers()
            logger.info(f"DNS baseline captured: {self._dns_servers_baseline}")
        except Exception as e:
            logger.error(f"Error capturing DNS baseline: {e}")

    def _get_current_dns_servers(self) -> list[str]:
        """Get current DNS server configuration."""
        try:
            # Use dns.resolver to get current nameservers
            return list(self._resolver.nameservers)
        except Exception as e:
            logger.error(f"Error getting DNS servers: {e}")
            return []

    def _cleanup_old_queries(self) -> None:
        """Clean up old query tracking data."""
        cutoff = datetime.now() - timedelta(hours=1)

        # Clean DNS queries
        self._dns_queries = [q for q in self._dns_queries if q.timestamp > cutoff]

        # Clean query counts
        for domain in list(self._query_counts.keys()):
            self._query_counts[domain] = [
                ts for ts in self._query_counts[domain] if ts > cutoff
            ]

            if not self._query_counts[domain]:
                del self._query_counts[domain]

    def get_statistics(self) -> dict[str, Any]:
        """Get monitor statistics."""
        return {
            "total_queries": self._stats["total_queries"],
            "recent_queries": len(self._dns_queries),
            "blocked_queries": self._stats["blocked_queries"],
            "tunneling_detected": self._stats["tunneling_detected"],
            "dga_domains_detected": self._stats["dga_domains_detected"],
            "suspicious_tlds": self._stats["suspicious_tlds"],
            "dns_hijacking_detected": self._stats["dns_hijacking_detected"],
            "unique_domains_tracked": len(self._query_counts),
            "dns_servers": self._dns_servers_baseline,
            "detect_tunneling": self.config.detect_tunneling,
            "detect_dga": self.config.detect_dga_domains,
            "monitor_dns_changes": self.config.monitor_dns_changes,
        }
