"""Threat Intelligence Integration for HifzDefend.

This module provides:
- Unified threat intelligence API interface
- IP reputation checking (AbuseIPDB)
- File reputation checking (VirusTotal)
- Package vulnerability checking (Snyk, Socket.dev)
- DNS reputation checking (Talos)
- Local caching to reduce API calls
- Rate limiting and quota management
- Graceful degradation when APIs unavailable
"""

from hifzdefend.threat_intel.manager import (
    ThreatIntelligenceManager,
    ThreatIntelConfig,
)
from hifzdefend.threat_intel.cache import ThreatIntelCache
from hifzdefend.threat_intel.rate_limiter import RateLimiter

__all__ = [
    "ThreatIntelligenceManager",
    "ThreatIntelConfig",
    "ThreatIntelCache",
    "RateLimiter",
]
