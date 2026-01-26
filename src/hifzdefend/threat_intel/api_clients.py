"""Threat Intelligence API Clients.

Individual API client implementations for various threat intelligence services:
- AbuseIPDB: IP reputation checking
- VirusTotal: File/URL reputation checking
- Snyk: Package vulnerability checking
- Socket.dev: Supply chain security
- Talos Intelligence: DNS/domain reputation
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat level classification."""

    UNKNOWN = "unknown"
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    CRITICAL = "critical"


@dataclass
class ThreatIntelResponse:
    """Unified threat intelligence response."""

    source: str  # API source (abuseipdb, virustotal, etc.)
    query: str  # What was queried (IP, hash, package, etc.)
    threat_level: ThreatLevel
    threat_score: int  # 0-100
    details: dict[str, Any]
    error: Optional[str] = None
    cached: bool = False


class BaseThreatIntelClient(ABC):
    """Base class for threat intelligence API clients."""

    def __init__(self, api_key: str, base_url: str, timeout: int = 10):
        """Initialize API client.

        Args:
            api_key: API key for authentication
            base_url: Base URL for API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    @abstractmethod
    async def query(self, target: str) -> ThreatIntelResponse:
        """Query API for threat intelligence.

        Args:
            target: Target to query (IP, hash, package, etc.)

        Returns:
            Threat intelligence response
        """
        pass


class AbuseIPDBClient(BaseThreatIntelClient):
    """AbuseIPDB API client for IP reputation checking."""

    def __init__(self, api_key: str):
        """Initialize AbuseIPDB client.

        Args:
            api_key: AbuseIPDB API key
        """
        super().__init__(
            api_key=api_key,
            base_url="https://api.abuseipdb.com/api/v2",
            timeout=10,
        )

    async def query(self, ip_address: str) -> ThreatIntelResponse:
        """Check IP reputation.

        Args:
            ip_address: IP address to check

        Returns:
            Threat intelligence response
        """
        if not self.api_key:
            return ThreatIntelResponse(
                source="abuseipdb",
                query=ip_address,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error="API key not configured",
            )

        try:
            session = await self._get_session()

            headers = {"Key": self.api_key, "Accept": "application/json"}

            params = {"ipAddress": ip_address, "maxAgeInDays": 90}

            async with session.get(
                f"{self.base_url}/check", headers=headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    ip_data = data.get("data", {})

                    # Calculate threat level
                    abuse_score = ip_data.get("abuseConfidenceScore", 0)
                    threat_level = self._calculate_threat_level(abuse_score)

                    return ThreatIntelResponse(
                        source="abuseipdb",
                        query=ip_address,
                        threat_level=threat_level,
                        threat_score=abuse_score,
                        details={
                            "is_whitelisted": ip_data.get("isWhitelisted", False),
                            "is_tor": ip_data.get("isTor", False),
                            "total_reports": ip_data.get("totalReports", 0),
                            "num_distinct_users": ip_data.get("numDistinctUsers", 0),
                            "country_code": ip_data.get("countryCode", ""),
                            "usage_type": ip_data.get("usageType", ""),
                            "isp": ip_data.get("isp", ""),
                            "domain": ip_data.get("domain", ""),
                        },
                    )
                elif response.status == 429:
                    # Rate limited
                    return ThreatIntelResponse(
                        source="abuseipdb",
                        query=ip_address,
                        threat_level=ThreatLevel.UNKNOWN,
                        threat_score=0,
                        details={},
                        error="Rate limit exceeded",
                    )
                else:
                    error_text = await response.text()
                    return ThreatIntelResponse(
                        source="abuseipdb",
                        query=ip_address,
                        threat_level=ThreatLevel.UNKNOWN,
                        threat_score=0,
                        details={},
                        error=f"API error: {response.status} - {error_text}",
                    )

        except aiohttp.ClientError as e:
            logger.error(f"AbuseIPDB API error: {e}", exc_info=True)
            return ThreatIntelResponse(
                source="abuseipdb",
                query=ip_address,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error=str(e),
            )

    def _calculate_threat_level(self, abuse_score: int) -> ThreatLevel:
        """Calculate threat level from abuse score.

        Args:
            abuse_score: Abuse confidence score (0-100)

        Returns:
            Threat level
        """
        if abuse_score >= 75:
            return ThreatLevel.CRITICAL
        elif abuse_score >= 50:
            return ThreatLevel.MALICIOUS
        elif abuse_score >= 25:
            return ThreatLevel.SUSPICIOUS
        elif abuse_score > 0:
            return ThreatLevel.SUSPICIOUS
        else:
            return ThreatLevel.CLEAN


class VirusTotalClient(BaseThreatIntelClient):
    """VirusTotal API client for file/URL reputation checking."""

    def __init__(self, api_key: str):
        """Initialize VirusTotal client.

        Args:
            api_key: VirusTotal API key
        """
        super().__init__(
            api_key=api_key, base_url="https://www.virustotal.com/api/v3", timeout=15
        )

    async def query_file_hash(self, file_hash: str) -> ThreatIntelResponse:
        """Check file hash reputation.

        Args:
            file_hash: SHA256 file hash

        Returns:
            Threat intelligence response
        """
        if not self.api_key:
            return ThreatIntelResponse(
                source="virustotal",
                query=file_hash,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error="API key not configured",
            )

        try:
            session = await self._get_session()

            headers = {"x-apikey": self.api_key, "Accept": "application/json"}

            async with session.get(
                f"{self.base_url}/files/{file_hash}", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    attributes = data.get("data", {}).get("attributes", {})

                    # Extract detection statistics
                    stats = attributes.get("last_analysis_stats", {})
                    malicious = stats.get("malicious", 0)
                    suspicious = stats.get("suspicious", 0)
                    undetected = stats.get("undetected", 0)
                    total = malicious + suspicious + undetected

                    # Calculate threat score and level
                    threat_score = self._calculate_threat_score(
                        malicious, suspicious, total
                    )
                    threat_level = self._calculate_threat_level(threat_score)

                    return ThreatIntelResponse(
                        source="virustotal",
                        query=file_hash,
                        threat_level=threat_level,
                        threat_score=threat_score,
                        details={
                            "malicious": malicious,
                            "suspicious": suspicious,
                            "undetected": undetected,
                            "total_engines": total,
                            "names": attributes.get("names", []),
                            "size": attributes.get("size", 0),
                            "type_description": attributes.get("type_description", ""),
                            "creation_date": attributes.get("creation_date", 0),
                            "last_analysis_date": attributes.get(
                                "last_analysis_date", 0
                            ),
                        },
                    )
                elif response.status == 404:
                    # Hash not found (could be new file)
                    return ThreatIntelResponse(
                        source="virustotal",
                        query=file_hash,
                        threat_level=ThreatLevel.UNKNOWN,
                        threat_score=0,
                        details={},
                        error="File hash not found in database",
                    )
                elif response.status == 429:
                    return ThreatIntelResponse(
                        source="virustotal",
                        query=file_hash,
                        threat_level=ThreatLevel.UNKNOWN,
                        threat_score=0,
                        details={},
                        error="Rate limit exceeded",
                    )
                else:
                    error_text = await response.text()
                    return ThreatIntelResponse(
                        source="virustotal",
                        query=file_hash,
                        threat_level=ThreatLevel.UNKNOWN,
                        threat_score=0,
                        details={},
                        error=f"API error: {response.status} - {error_text}",
                    )

        except aiohttp.ClientError as e:
            logger.error(f"VirusTotal API error: {e}", exc_info=True)
            return ThreatIntelResponse(
                source="virustotal",
                query=file_hash,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error=str(e),
            )

    async def query(self, target: str) -> ThreatIntelResponse:
        """Query VirusTotal (delegates to query_file_hash).

        Args:
            target: File hash or URL

        Returns:
            Threat intelligence response
        """
        # Assume target is file hash if it looks like one
        if len(target) == 64 and all(c in "0123456789abcdefABCDEF" for c in target):
            return await self.query_file_hash(target)
        else:
            # Could implement URL checking here
            return ThreatIntelResponse(
                source="virustotal",
                query=target,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error="URL checking not implemented",
            )

    def _calculate_threat_score(
        self, malicious: int, suspicious: int, total: int
    ) -> int:
        """Calculate threat score from detection statistics.

        Args:
            malicious: Number of engines detecting as malicious
            suspicious: Number of engines detecting as suspicious
            total: Total number of engines

        Returns:
            Threat score (0-100)
        """
        if total == 0:
            return 0

        # Weighted score: malicious = 1.0, suspicious = 0.5
        weighted_detections = malicious + (suspicious * 0.5)
        score = int((weighted_detections / total) * 100)

        return min(100, max(0, score))

    def _calculate_threat_level(self, threat_score: int) -> ThreatLevel:
        """Calculate threat level from score.

        Args:
            threat_score: Threat score (0-100)

        Returns:
            Threat level
        """
        if threat_score >= 75:
            return ThreatLevel.CRITICAL
        elif threat_score >= 50:
            return ThreatLevel.MALICIOUS
        elif threat_score >= 25:
            return ThreatLevel.SUSPICIOUS
        elif threat_score > 0:
            return ThreatLevel.SUSPICIOUS
        else:
            return ThreatLevel.CLEAN


class SnykClient(BaseThreatIntelClient):
    """Snyk API client for package vulnerability checking."""

    def __init__(self, api_key: str):
        """Initialize Snyk client.

        Args:
            api_key: Snyk API key
        """
        super().__init__(
            api_key=api_key, base_url="https://api.snyk.io/v1", timeout=15
        )

    async def query_package(
        self, package_name: str, version: str, ecosystem: str = "npm"
    ) -> ThreatIntelResponse:
        """Check package for known vulnerabilities.

        Args:
            package_name: Package name
            version: Package version
            ecosystem: Package ecosystem (npm, pypi, etc.)

        Returns:
            Threat intelligence response
        """
        if not self.api_key:
            return ThreatIntelResponse(
                source="snyk",
                query=f"{package_name}@{version}",
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error="API key not configured",
            )

        try:
            session = await self._get_session()

            headers = {
                "Authorization": f"token {self.api_key}",
                "Content-Type": "application/json",
            }

            # Construct package identifier based on ecosystem
            if ecosystem == "npm":
                package_id = f"{package_name}@{version}"
            elif ecosystem == "pypi":
                package_id = f"{package_name}=={version}"
            else:
                package_id = f"{package_name}@{version}"

            # Test endpoint
            payload = {"package": package_id}

            async with session.post(
                f"{self.base_url}/test/{ecosystem}",
                headers=headers,
                json=payload,
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    # Extract vulnerability information
                    issues = data.get("issues", [])
                    vuln_count = len(issues)

                    # Calculate severity distribution
                    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}

                    for issue in issues:
                        severity = issue.get("severity", "").lower()
                        if severity in severity_counts:
                            severity_counts[severity] += 1

                    # Calculate threat score
                    threat_score = self._calculate_threat_score(severity_counts)
                    threat_level = self._calculate_threat_level(threat_score)

                    return ThreatIntelResponse(
                        source="snyk",
                        query=package_id,
                        threat_level=threat_level,
                        threat_score=threat_score,
                        details={
                            "vulnerability_count": vuln_count,
                            "severity_counts": severity_counts,
                            "issues": [
                                {
                                    "id": issue.get("id", ""),
                                    "title": issue.get("title", ""),
                                    "severity": issue.get("severity", ""),
                                    "cvss_score": issue.get("cvssScore", 0),
                                }
                                for issue in issues[:10]  # Limit to 10
                            ],
                        },
                    )
                elif response.status == 404:
                    # Package not found or no vulnerabilities
                    return ThreatIntelResponse(
                        source="snyk",
                        query=package_id,
                        threat_level=ThreatLevel.CLEAN,
                        threat_score=0,
                        details={"vulnerability_count": 0},
                    )
                elif response.status == 429:
                    return ThreatIntelResponse(
                        source="snyk",
                        query=package_id,
                        threat_level=ThreatLevel.UNKNOWN,
                        threat_score=0,
                        details={},
                        error="Rate limit exceeded",
                    )
                else:
                    error_text = await response.text()
                    return ThreatIntelResponse(
                        source="snyk",
                        query=package_id,
                        threat_level=ThreatLevel.UNKNOWN,
                        threat_score=0,
                        details={},
                        error=f"API error: {response.status} - {error_text}",
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Snyk API error: {e}", exc_info=True)
            return ThreatIntelResponse(
                source="snyk",
                query=f"{package_name}@{version}",
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error=str(e),
            )

    async def query(self, target: str) -> ThreatIntelResponse:
        """Query Snyk (requires package format).

        Args:
            target: Package in format "name@version" or "name==version"

        Returns:
            Threat intelligence response
        """
        # Parse package string
        if "@" in target:
            package_name, version = target.split("@", 1)
            ecosystem = "npm"
        elif "==" in target:
            package_name, version = target.split("==", 1)
            ecosystem = "pypi"
        else:
            return ThreatIntelResponse(
                source="snyk",
                query=target,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error="Invalid package format (use name@version or name==version)",
            )

        return await self.query_package(package_name, version, ecosystem)

    def _calculate_threat_score(self, severity_counts: dict) -> int:
        """Calculate threat score from severity distribution.

        Args:
            severity_counts: Dictionary with severity counts

        Returns:
            Threat score (0-100)
        """
        # Weight vulnerabilities by severity
        score = (
            severity_counts.get("critical", 0) * 25
            + severity_counts.get("high", 0) * 15
            + severity_counts.get("medium", 0) * 5
            + severity_counts.get("low", 0) * 1
        )

        return min(100, score)

    def _calculate_threat_level(self, threat_score: int) -> ThreatLevel:
        """Calculate threat level from score.

        Args:
            threat_score: Threat score (0-100)

        Returns:
            Threat level
        """
        if threat_score >= 75:
            return ThreatLevel.CRITICAL
        elif threat_score >= 50:
            return ThreatLevel.MALICIOUS
        elif threat_score >= 25:
            return ThreatLevel.SUSPICIOUS
        elif threat_score > 0:
            return ThreatLevel.SUSPICIOUS
        else:
            return ThreatLevel.CLEAN
