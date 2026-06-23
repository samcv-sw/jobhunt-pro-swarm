"""
Upstash Redis Rate Limiter — Free tier (10k commands/day)
Uses REST API (HTTP), no Redis client library needed.

Setup:
1. Create free account at https://upstash.com
2. Create a Redis database (free tier: 10k commands/day, 256MB)
3. Set env vars:
   UPSTASH_REDIS_URL=https://xxx-xxx.upstash.io
   UPSTASH_REDIS_TOKEN=AXxxxx...

Usage:
    from core.upstash_rate_limiter import RateLimiter

    limiter = RateLimiter()

    # Check if allowed
    if limiter.allow("login:192.168.1.1", max_count=5, window_seconds=300):
        # proceed
    else:
        # rate limited

    # Get current count
    count = limiter.count("login:192.168.1.1")
"""

import os
import time
import json
import logging
import urllib.request
import urllib.error
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token-bucket rate limiter using Upstash Redis REST API.
    Falls back to in-memory dict if Upstash not configured.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.url = os.getenv("UPSTASH_REDIS_URL", "")
        self.token = os.getenv("UPSTASH_REDIS_TOKEN", "")
        self._fallback = {}  # in-memory fallback
        self._enabled = bool(self.url and self.token)
        if self._enabled:
            logger.info("Upstash rate limiter enabled")
        else:
            logger.info("Upstash not configured, using in-memory rate limiter")

    def _exec(self, command: list) -> Optional[any]:
        """Execute a Redis command via REST API."""
        if not self._enabled:
            return None
        try:
            payload = json.dumps(command).encode()
            req = urllib.request.Request(
                f"{self.url}",
                data=payload,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                return data.get("result")
        except Exception as e:
            logger.warning(f"Upstash error: {e}")
            return None

    def allow(self, key: str, max_count: int = 5, window_seconds: int = 300) -> bool:
        """
        Check if action is allowed under rate limit.
        Returns True if allowed, False if rate limited.
        """
        if self._enabled:
            # Use Redis sorted set for sliding window
            now = time.time()
            window_start = now - window_seconds

            # Remove old entries
            self._exec(["ZREMRANGEBYSCORE", key, "-inf", str(window_start)])

            # Count current
            count = self._exec(["ZCARD", key])
            count = int(count) if count else 0

            if count >= max_count:
                return False

            # Add current request
            self._exec(["ZADD", key, str(now), f"{now}"])
            self._exec(["EXPIRE", key, str(window_seconds)])
            return True
        else:
            # In-memory fallback
            now = time.time()
            if key not in self._fallback:
                self._fallback[key] = []

            # Remove old entries
            self._fallback[key] = [t for t in self._fallback[key] if t > now - window_seconds]

            if len(self._fallback[key]) >= max_count:
                return False

            self._fallback[key].append(now)
            return True

    def count(self, key: str) -> int:
        """Get current request count for key."""
        if self._enabled:
            now = time.time()
            self._exec(["ZREMRANGEBYSCORE", key, "-inf", str(now - 3600)])
            count = self._exec(["ZCARD", key])
            return int(count) if count else 0
        else:
            now = time.time()
            if key not in self._fallback:
                return 0
            self._fallback[key] = [t for t in self._fallback[key] if t > now - 3600]
            return len(self._fallback[key])

    def reset(self, key: str):
        """Reset counter for a key."""
        if self._enabled:
            self._exec(["DEL", key])
        else:
            self._fallback.pop(key, None)


# Global instance
rate_limiter = RateLimiter()


def check_login_rate(ip: str) -> bool:
    """Rate limit login attempts: 5 per 5 minutes per IP."""
    return rate_limiter.allow(f"login:{ip}", max_count=5, window_seconds=300)


def check_api_rate(api_key: str) -> bool:
    """Rate limit API calls: 100 per minute per key."""
    return rate_limiter.allow(f"api:{api_key}", max_count=100, window_seconds=60)


def check_email_rate(provider: str) -> bool:
    """Rate limit email sends: per provider caps."""
    caps = {
        "gmail": (100, 86400),      # 100/day
        "hotmail": (500, 3600),     # 500/hour
        "brevo": (250, 86400),      # 250/day
        "smtp": (50, 3600),         # 50/hour generic
    }
    max_count, window = caps.get(provider, (50, 3600))
    return rate_limiter.allow(f"email:{provider}", max_count=max_count, window_seconds=window)
