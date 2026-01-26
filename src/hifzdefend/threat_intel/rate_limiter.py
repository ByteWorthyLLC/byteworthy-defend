"""Rate Limiter for API calls.

Implements token bucket algorithm for rate limiting API requests
to respect quotas and avoid excessive calls.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiter configuration."""

    max_tokens: int  # Maximum tokens in bucket
    refill_rate: float  # Tokens per second
    refill_period: float = 1.0  # Seconds between refills


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, config: RateLimitConfig):
        """Initialize rate limiter.

        Args:
            config: Rate limiter configuration
        """
        self.config = config
        self.tokens = float(config.max_tokens)
        self.max_tokens = float(config.max_tokens)
        self.refill_rate = config.refill_rate
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

        logger.info(
            f"Rate limiter initialized: {config.max_tokens} tokens, "
            f"{config.refill_rate} tokens/sec"
        )

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from bucket.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False if rate limited
        """
        async with self._lock:
            # Refill tokens based on elapsed time
            self._refill_tokens()

            # Check if enough tokens available
            if self.tokens >= tokens:
                self.tokens -= tokens
                logger.debug(f"Acquired {tokens} tokens, {self.tokens:.2f} remaining")
                return True
            else:
                logger.warning(
                    f"Rate limit hit: requested {tokens}, only {self.tokens:.2f} available"
                )
                return False

    async def wait_for_token(self, tokens: int = 1, timeout: Optional[float] = None):
        """Wait until tokens become available.

        Args:
            tokens: Number of tokens needed
            timeout: Maximum wait time in seconds (None = infinite)

        Raises:
            asyncio.TimeoutError: If timeout expires
        """
        start_time = time.monotonic()

        while True:
            if await self.acquire(tokens):
                return

            # Check timeout
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed >= timeout:
                    raise asyncio.TimeoutError(
                        f"Rate limiter timeout after {timeout}s"
                    )

            # Wait a bit before retrying
            wait_time = min(1.0, self._calculate_wait_time(tokens))
            await asyncio.sleep(wait_time)

    def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill

        # Calculate tokens to add
        tokens_to_add = elapsed * self.refill_rate

        if tokens_to_add > 0:
            self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
            self.last_refill = now

    def _calculate_wait_time(self, tokens: int) -> float:
        """Calculate wait time until tokens available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Wait time in seconds
        """
        tokens_needed = tokens - self.tokens
        if tokens_needed <= 0:
            return 0.0

        return tokens_needed / self.refill_rate

    def get_available_tokens(self) -> float:
        """Get current number of available tokens.

        Returns:
            Number of tokens available
        """
        self._refill_tokens()
        return self.tokens

    def reset(self):
        """Reset rate limiter to full capacity."""
        self.tokens = self.max_tokens
        self.last_refill = time.monotonic()
        logger.info("Rate limiter reset to full capacity")

    def get_statistics(self) -> dict:
        """Get rate limiter statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "available_tokens": self.get_available_tokens(),
            "max_tokens": self.max_tokens,
            "refill_rate": self.refill_rate,
            "utilization": 1.0 - (self.get_available_tokens() / self.max_tokens),
        }
