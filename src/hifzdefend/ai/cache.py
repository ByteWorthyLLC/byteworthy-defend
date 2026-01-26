"""
Response caching for Claude API to reduce costs and improve performance.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

from hifzdefend.utils.exceptions import HifzDefendError


class CacheError(HifzDefendError):
    """Cache operation error."""

    pass


class ResponseCache:
    """
    TTL-based cache for Claude API responses.

    Features:
    - Hash-based cache keys (prompt + model + temperature)
    - Automatic expiration based on TTL
    - File-based persistence
    - Atomic writes
    """

    def __init__(self, cache_dir: Path, ttl: int = 3600):
        """
        Initialize response cache.

        Args:
            cache_dir: Directory to store cache files
            ttl: Time-to-live in seconds (default: 3600 = 1 hour)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions on cache directory (owner-only access)
        # This prevents other users from reading cached AI responses
        try:
            import os
            import stat

            # Set permissions to 0o700 (rwx------)
            os.chmod(self.cache_dir, stat.S_IRWXU)
        except Exception as e:
            logger.warning(f"Could not set restrictive permissions on cache directory: {e}")

    def _get_cache_key(self, prompt: str, model: str, temperature: float) -> str:
        """
        Generate cache key from prompt parameters.

        Args:
            prompt: The prompt text
            model: Model identifier
            temperature: Temperature setting

        Returns:
            SHA256 hash of combined parameters
        """
        content = f"{prompt}|{model}|{temperature}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(
        self, prompt: str, model: str, temperature: float
    ) -> Optional[dict[str, Any]]:
        """
        Retrieve cached response if not expired.

        Args:
            prompt: The prompt text
            model: Model identifier
            temperature: Temperature setting

        Returns:
            Cached response dict or None if not found/expired
        """
        cache_key = self._get_cache_key(prompt, model, temperature)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        # Check TTL
        age = time.time() - cache_file.stat().st_mtime
        if age > self.ttl:
            # Delete expired cache
            try:
                cache_file.unlink()
            except OSError:
                pass  # Ignore errors during cleanup
            return None

        # Load cached response
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise CacheError(f"Failed to load cache: {e}")

    def set(
        self, prompt: str, model: str, temperature: float, response: dict[str, Any]
    ) -> None:
        """
        Store response in cache.

        Args:
            prompt: The prompt text
            model: Model identifier
            temperature: Temperature setting
            response: Response dict to cache
        """
        cache_key = self._get_cache_key(prompt, model, temperature)
        cache_file = self.cache_dir / f"{cache_key}.json"

        # Add metadata
        cache_data = {
            "cached_at": time.time(),
            "ttl": self.ttl,
            "response": response,
        }

        # Atomic write
        try:
            import os
            import stat

            temp_file = cache_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)

            # Set restrictive permissions on temp file before moving (owner read/write only)
            os.chmod(temp_file, stat.S_IRUSR | stat.S_IWUSR)

            temp_file.replace(cache_file)
        except OSError as e:
            raise CacheError(f"Failed to write cache: {e}")

    def clear(self) -> int:
        """
        Clear all cached responses.

        Returns:
            Number of files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                pass  # Ignore errors during cleanup
        return count

    def clear_expired(self) -> int:
        """
        Clear only expired cached responses.

        Returns:
            Number of files deleted
        """
        count = 0
        current_time = time.time()
        for cache_file in self.cache_dir.glob("*.json"):
            age = current_time - cache_file.stat().st_mtime
            if age > self.ttl:
                try:
                    cache_file.unlink()
                    count += 1
                except OSError:
                    pass  # Ignore errors during cleanup
        return count

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats (total files, total size, oldest/newest)
        """
        files = list(self.cache_dir.glob("*.json"))
        if not files:
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "oldest_age_seconds": None,
                "newest_age_seconds": None,
            }

        current_time = time.time()
        total_size = sum(f.stat().st_size for f in files)
        ages = [current_time - f.stat().st_mtime for f in files]

        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "oldest_age_seconds": max(ages),
            "newest_age_seconds": min(ages),
        }
