"""
Upstash Redis Rate Limiter — Free tier (10k commands/day)
Uses REST API (HTTP), no Redis client library needed.
"""

import json
import logging
import os
import time
import random
import urllib.error
import urllib.request
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
        self._cleanup_counter = 0
        if self._enabled:
            logger.info("Upstash rate limiter enabled")
        else:
            logger.info("Upstash not configured, using in-memory rate limiter")

    def _exec(self, command: list) -> any | None:
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
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                return data.get("result")
        except Exception as e:
            logger.warning(f"Upstash error: {e}")
            return None

    def _exec_pipeline(self, commands: list) -> Optional[list]:
        """Execute multiple Redis commands in a single HTTP request using pipeline."""
        if not self._enabled:
            return None
        try:
            payload = json.dumps(commands).encode()
            req = urllib.request.Request(
                f"{self.url}/pipeline",
                data=payload,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                results = []
                for res in data:
                    if "error" in res:
                        logger.warning(f"Pipeline command error: {res['error']}")
                        results.append(None)
                    else:
                        results.append(res.get("result"))
                return results
        except Exception as e:
            logger.warning(f"Upstash pipeline error: {e}")
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

            # Pipeline 1: Clean up expired timestamps and get active count
            pipeline_results = self._exec_pipeline([
                ["ZREMRANGEBYSCORE", key, "-inf", str(window_start)],
                ["ZCARD", key]
            ])
            if not pipeline_results:
                return True  # Fallback to allowed if connection fails

            count = pipeline_results[1]
            count = int(count) if count is not None else 0
            if count >= max_count:
                return False

            # Pipeline 2: Add member with unique suffix and reset expiration
            member = f"{now}:{random.random()}"
            self._exec_pipeline([
                ["ZADD", key, str(now), member],
                ["EXPIRE", key, str(window_seconds)]
            ])
            return True
        else:
            # In-memory fallback
            now = time.time()
            if key not in self._fallback:
                self._fallback[key] = []

            # Remove old entries and clean up to prevent memory leaks
            active_ts = [t for t in self._fallback[key] if t > now - window_seconds]
            
            self._cleanup_counter += 1
            if self._cleanup_counter >= 1000:
                self._cleanup_fallback()
                self._cleanup_counter = 0
                active_ts = [t for t in self._fallback.get(key, []) if t > now - window_seconds]

            if len(active_ts) >= max_count:
                if not active_ts:
                    self._fallback.pop(key, None)
                else:
                    self._fallback[key] = active_ts
                return False

            active_ts.append(now)
            self._fallback[key] = active_ts
            return True

    def _cleanup_fallback(self):
        """Prune expired fallback rate limit lists to prevent memory leaks."""
        now = time.time()
        expired_keys = []
        for key, ts_list in list(self._fallback.items()):
            filtered = [t for t in ts_list if t > now - 86400]  # default max window 1 day
            if not filtered:
                expired_keys.append(key)
            else:
                self._fallback[key] = filtered
        for key in expired_keys:
            self._fallback.pop(key, None)

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
        "gmail": (100, 86400),  # 100/day
        "hotmail": (500, 3600),  # 500/hour
        "brevo": (250, 86400),  # 250/day
        "smtp": (50, 3600),  # 50/hour generic
    }
    max_count, window = caps.get(provider, (50, 3600))
    return rate_limiter.allow(
        f"email:{provider}", max_count=max_count, window_seconds=window
    )
