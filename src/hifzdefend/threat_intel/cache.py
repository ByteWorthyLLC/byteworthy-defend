"""Threat Intelligence Cache.

LRU cache for threat intelligence API responses to reduce API calls
and improve performance.
"""

import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with value and expiration."""

    value: Any
    expires_at: float  # Unix timestamp
    created_at: float
    hit_count: int = 0


class ThreatIntelCache:
    """LRU cache for threat intelligence data."""

    def __init__(
        self,
        max_entries: int = 10000,
        ttl: int = 3600,  # 1 hour default
        eviction_policy: str = "lru",
    ):
        """Initialize threat intelligence cache.

        Args:
            max_entries: Maximum number of cache entries
            ttl: Time to live in seconds
            eviction_policy: Eviction policy ("lru" or "lfu")
        """
        self.max_entries = max_entries
        self.ttl = ttl
        self.eviction_policy = eviction_policy
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
        }

        logger.info(
            f"Threat intel cache initialized: max={max_entries}, "
            f"ttl={ttl}s, policy={eviction_policy}"
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._stats["misses"] += 1
            return None

        entry = self._cache[key]

        # Check expiration
        if time.time() > entry.expires_at:
            self._stats["misses"] += 1
            self._stats["expirations"] += 1
            del self._cache[key]
            logger.debug(f"Cache entry expired: {key}")
            return None

        # Move to end (LRU)
        self._cache.move_to_end(key)

        # Update hit count
        entry.hit_count += 1
        self._stats["hits"] += 1

        logger.debug(f"Cache hit: {key} (hits: {entry.hit_count})")
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom TTL in seconds
        """
        now = time.time()
        cache_ttl = ttl if ttl is not None else self.ttl

        # Check if cache is full
        if key not in self._cache and len(self._cache) >= self.max_entries:
            self._evict()

        # Create cache entry
        entry = CacheEntry(
            value=value,
            expires_at=now + cache_ttl,
            created_at=now,
        )

        # Add to cache (moves to end)
        self._cache[key] = entry
        self._cache.move_to_end(key)

        logger.debug(f"Cache set: {key} (ttl: {cache_ttl}s)")

    def delete(self, key: str):
        """Delete entry from cache.

        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache delete: {key}")

    def clear(self):
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared: {count} entries removed")

    def _evict(self):
        """Evict entry based on eviction policy."""
        if self.eviction_policy == "lru":
            # Remove least recently used (first item)
            key, _ = self._cache.popitem(last=False)
        elif self.eviction_policy == "lfu":
            # Remove least frequently used
            key = min(self._cache.keys(), key=lambda k: self._cache[k].hit_count)
            del self._cache[key]
        else:
            # Default to LRU
            key, _ = self._cache.popitem(last=False)

        self._stats["evictions"] += 1
        logger.debug(f"Cache eviction: {key} (policy: {self.eviction_policy})")

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items() if now > entry.expires_at
        ]

        for key in expired_keys:
            del self._cache[key]
            self._stats["expirations"] += 1

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_statistics(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with statistics
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            (self._stats["hits"] / total_requests) if total_requests > 0 else 0.0
        )

        return {
            "size": len(self._cache),
            "max_entries": self.max_entries,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self._stats["evictions"],
            "expirations": self._stats["expirations"],
            "ttl": self.ttl,
        }

    def get_entry_info(self, key: str) -> Optional[dict]:
        """Get information about cache entry.

        Args:
            key: Cache key

        Returns:
            Dictionary with entry info or None
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        now = time.time()

        return {
            "key": key,
            "created_at": entry.created_at,
            "expires_at": entry.expires_at,
            "time_to_expiry": entry.expires_at - now,
            "hit_count": entry.hit_count,
            "is_expired": now > entry.expires_at,
        }
