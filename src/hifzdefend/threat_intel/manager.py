"""Threat Intelligence Manager.

Unified interface for all threat intelligence APIs with caching,
rate limiting, and graceful degradation.
"""

import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from hifzdefend.monitoring.base import MonitorConfig
from hifzdefend.threat_intel.api_clients import (
    AbuseIPDBClient,
    SnykClient,
    ThreatIntelResponse,
    ThreatLevel,
    VirusTotalClient,
)
from hifzdefend.threat_intel.cache import ThreatIntelCache
from hifzdefend.threat_intel.rate_limiter import RateLimiter, RateLimitConfig

logger = logging.getLogger(__name__)


class ThreatIntelAPIKeys(BaseModel):
    """API keys for threat intelligence services."""

    abuseipdb: str = Field(default="", description="AbuseIPDB API key")
    virustotal: str = Field(default="", description="VirusTotal API key")
    snyk: str = Field(default="", description="Snyk API token")
    socket_dev: str = Field(default="", description="Socket.dev API key")


class ThreatIntelCacheConfig(BaseModel):
    """Cache configuration."""

    enabled: bool = Field(default=True, description="Enable caching")
    max_entries: int = Field(default=10000, description="Maximum cache entries")
    ttl: int = Field(default=3600, description="Cache TTL in seconds (1 hour default)")
    eviction_policy: str = Field(
        default="lru", description="Cache eviction policy (lru or lfu)"
    )


class ThreatIntelConfig(MonitorConfig):
    """Configuration for Threat Intelligence Manager."""

    enabled: bool = Field(default=True, description="Enable threat intelligence")

    # Rate limiting
    rate_limit_per_minute: int = Field(
        default=60, description="API calls per minute limit"
    )

    # API keys
    api_keys: ThreatIntelAPIKeys = Field(
        default_factory=ThreatIntelAPIKeys, description="API keys for services"
    )

    # Cache configuration
    cache: ThreatIntelCacheConfig = Field(
        default_factory=ThreatIntelCacheConfig, description="Cache configuration"
    )

    # Graceful degradation
    allow_degraded: bool = Field(
        default=True,
        description="Continue operation if some APIs are unavailable",
    )

    # Timeout
    api_timeout: int = Field(
        default=10, description="API request timeout in seconds"
    )


class ThreatIntelligenceManager:
    """Unified threat intelligence manager."""

    def __init__(self, config: ThreatIntelConfig):
        """Initialize threat intelligence manager.

        Args:
            config: Threat intelligence configuration
        """
        self.config = config
        self._stats = {
            "api_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "api_errors": 0,
            "rate_limit_hits": 0,
        }

        # Initialize cache
        if config.cache.enabled:
            self.cache = ThreatIntelCache(
                max_entries=config.cache.max_entries,
                ttl=config.cache.ttl,
                eviction_policy=config.cache.eviction_policy,
            )
        else:
            self.cache = None

        # Initialize rate limiter
        rate_limit_config = RateLimitConfig(
            max_tokens=config.rate_limit_per_minute,
            refill_rate=config.rate_limit_per_minute / 60.0,  # tokens per second
        )
        self.rate_limiter = RateLimiter(rate_limit_config)

        # Initialize API clients
        self.abuseipdb = None
        self.virustotal = None
        self.snyk = None

        if config.api_keys.abuseipdb:
            self.abuseipdb = AbuseIPDBClient(config.api_keys.abuseipdb)
            logger.info("AbuseIPDB client initialized")

        if config.api_keys.virustotal:
            self.virustotal = VirusTotalClient(config.api_keys.virustotal)
            logger.info("VirusTotal client initialized")

        if config.api_keys.snyk:
            self.snyk = SnykClient(config.api_keys.snyk)
            logger.info("Snyk client initialized")

        logger.info("Threat Intelligence Manager initialized")

    async def check_ip_reputation(self, ip_address: str) -> ThreatIntelResponse:
        """Check IP address reputation.

        Args:
            ip_address: IP address to check

        Returns:
            Threat intelligence response
        """
        cache_key = f"ip:{ip_address}"

        # Check cache first
        if self.cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self._stats["cache_hits"] += 1
                logger.debug(f"Cache hit for IP: {ip_address}")
                cached_result.cached = True
                return cached_result

        self._stats["cache_misses"] += 1

        # Check if AbuseIPDB is available
        if not self.abuseipdb:
            logger.warning("AbuseIPDB client not configured")
            return ThreatIntelResponse(
                source="abuseipdb",
                query=ip_address,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error="AbuseIPDB API key not configured",
            )

        # Check rate limit
        if not await self.rate_limiter.acquire():
            self._stats["rate_limit_hits"] += 1
            logger.warning("Rate limit exceeded for IP reputation check")
            return ThreatIntelResponse(
                source="abuseipdb",
                query=ip_address,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error="Rate limit exceeded",
            )

        # Query API
        try:
            self._stats["api_calls"] += 1
            result = await self.abuseipdb.query(ip_address)

            # Cache result if successful
            if self.cache and not result.error:
                self.cache.set(cache_key, result)

            return result

        except Exception as e:
            self._stats["api_errors"] += 1
            logger.error(f"Error checking IP reputation: {e}", exc_info=True)
            return ThreatIntelResponse(
                source="abuseipdb",
                query=ip_address,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error=str(e),
            )

    async def check_file_reputation(self, file_hash: str) -> ThreatIntelResponse:
        """Check file hash reputation.

        Args:
            file_hash: SHA256 file hash

        Returns:
            Threat intelligence response
        """
        cache_key = f"file:{file_hash}"

        # Check cache first
        if self.cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self._stats["cache_hits"] += 1
                logger.debug(f"Cache hit for file: {file_hash}")
                cached_result.cached = True
                return cached_result

        self._stats["cache_misses"] += 1

        # Check if VirusTotal is available
        if not self.virustotal:
            logger.warning("VirusTotal client not configured")
            return ThreatIntelResponse(
                source="virustotal",
                query=file_hash,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error="VirusTotal API key not configured",
            )

        # Check rate limit
        if not await self.rate_limiter.acquire():
            self._stats["rate_limit_hits"] += 1
            logger.warning("Rate limit exceeded for file reputation check")
            return ThreatIntelResponse(
                source="virustotal",
                query=file_hash,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error="Rate limit exceeded",
            )

        # Query API
        try:
            self._stats["api_calls"] += 1
            result = await self.virustotal.query_file_hash(file_hash)

            # Cache result if successful
            if self.cache and not result.error:
                # Longer TTL for file hashes (they don't change)
                self.cache.set(cache_key, result, ttl=86400)  # 24 hours

            return result

        except Exception as e:
            self._stats["api_errors"] += 1
            logger.error(f"Error checking file reputation: {e}", exc_info=True)
            return ThreatIntelResponse(
                source="virustotal",
                query=file_hash,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error=str(e),
            )

    async def check_package_security(
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
        package_id = f"{package_name}@{version}" if ecosystem == "npm" else f"{package_name}=={version}"
        cache_key = f"package:{ecosystem}:{package_id}"

        # Check cache first
        if self.cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self._stats["cache_hits"] += 1
                logger.debug(f"Cache hit for package: {package_id}")
                cached_result.cached = True
                return cached_result

        self._stats["cache_misses"] += 1

        # Check if Snyk is available
        if not self.snyk:
            logger.warning("Snyk client not configured")
            return ThreatIntelResponse(
                source="snyk",
                query=package_id,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error="Snyk API key not configured",
            )

        # Check rate limit
        if not await self.rate_limiter.acquire():
            self._stats["rate_limit_hits"] += 1
            logger.warning("Rate limit exceeded for package security check")
            return ThreatIntelResponse(
                source="snyk",
                query=package_id,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error="Rate limit exceeded",
            )

        # Query API
        try:
            self._stats["api_calls"] += 1
            result = await self.snyk.query_package(package_name, version, ecosystem)

            # Cache result if successful
            if self.cache and not result.error:
                # Medium TTL for packages (vulnerabilities may be discovered)
                self.cache.set(cache_key, result, ttl=3600)  # 1 hour

            return result

        except Exception as e:
            self._stats["api_errors"] += 1
            logger.error(f"Error checking package security: {e}", exc_info=True)
            return ThreatIntelResponse(
                source="snyk",
                query=package_id,
                threat_level=ThreatLevel.UNKNOWN,
                threat_score=0,
                details={},
                error=str(e),
            )

    async def close(self):
        """Close all API clients and cleanup resources."""
        if self.abuseipdb:
            await self.abuseipdb.close()

        if self.virustotal:
            await self.virustotal.close()

        if self.snyk:
            await self.snyk.close()

        logger.info("Threat Intelligence Manager closed")

    def get_statistics(self) -> dict:
        """Get threat intelligence statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "api_calls": self._stats["api_calls"],
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "api_errors": self._stats["api_errors"],
            "rate_limit_hits": self._stats["rate_limit_hits"],
        }

        # Add cache statistics if enabled
        if self.cache:
            stats["cache"] = self.cache.get_statistics()

        # Add rate limiter statistics
        stats["rate_limiter"] = self.rate_limiter.get_statistics()

        # Calculate cache hit rate
        total_requests = stats["cache_hits"] + stats["cache_misses"]
        if total_requests > 0:
            stats["cache_hit_rate"] = stats["cache_hits"] / total_requests
        else:
            stats["cache_hit_rate"] = 0.0

        # Calculate API success rate
        total_api_calls = stats["api_calls"]
        if total_api_calls > 0:
            stats["api_success_rate"] = 1.0 - (stats["api_errors"] / total_api_calls)
        else:
            stats["api_success_rate"] = 0.0

        return stats

    def get_service_status(self) -> dict:
        """Get status of configured services.

        Returns:
            Dictionary with service availability
        """
        return {
            "abuseipdb": self.abuseipdb is not None,
            "virustotal": self.virustotal is not None,
            "snyk": self.snyk is not None,
            "cache": self.cache is not None,
        }
