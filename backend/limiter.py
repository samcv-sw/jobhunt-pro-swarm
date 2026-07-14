import asyncio
import logging
import os
import random
import sys
import time
from collections import defaultdict

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# Try to import redis for distributed rate limiting
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis package not found. Rate limiter will fall back to local in-memory mode.")

class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int, redis_url: str = None):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self.redis = None
        self.history = defaultdict(list)
        self.cleanup_task = None
        self._is_redis_connected = False

        if REDIS_AVAILABLE and self.redis_url:
            try:
                # Initialize Redis client pool
                self.redis = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_keepalive=True,
                    retry_on_timeout=True
                )
                self._is_redis_connected = True
                logger.info(f"Rate Limiter connected to Redis at {self.redis_url}")
            except Exception as e:
                logger.error(f"Failed to initialize Redis for rate limiting: {e}. Falling back to in-memory mode.")
                self._is_redis_connected = False

        # Cleanup task will be initialized lazily on the first request to avoid "no running event loop" error.
    async def _periodic_cleanup(self):
        """Background loop to clean up expired in-memory rate limiting keys to prevent memory leaks."""
        while True:
            try:
                await asyncio.sleep(60)
                now = time.time()
                keys = list(self.history.keys())
                for i, ip in enumerate(keys):
                    # Yield to event loop periodically if there are many keys
                    if i % 100 == 0:
                        await asyncio.sleep(0)

                    self.history[ip] = [t for t in self.history[ip] if now - t < self.window_seconds]
                    # GIL-safe atomic check and deletion
                    if ip in self.history and not self.history[ip]:
                        self.history.pop(ip, None)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rate limiter in-memory cleanup loop: {e}")

    async def _call_redis(self, client_ip: str) -> bool:
        """Evaluates rate limit using Redis sliding window log with pipeline."""
        now = time.time()
        key = f"rate_limit:{client_ip}"
        clear_before = now - self.window_seconds
        # Add a unique suffix to prevent overwrites under extreme concurrency
        member = f"{now}-{random.random()}"
        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.zadd(key, {member: now})
                pipe.zremrangebyscore(key, "-inf", clear_before)
                pipe.zcard(key)
                pipe.expire(key, self.window_seconds)
                _, _, count, _ = await pipe.execute()

            return count <= self.requests_limit
        except Exception as e:
            logger.warning(f"Redis rate limiter failed ({e}). Falling back to in-memory rate limiter.")
            self._is_redis_connected = False
            if not self.cleanup_task:
                self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
            return False

    async def __call__(self, request: Request):
        from backend.auth import _get_client_ip
        client_ip = _get_client_ip(request)

        # Check via Redis if connected
        if self._is_redis_connected and self.redis:
            allowed = await self._call_redis(client_ip)
            if not allowed and self._is_redis_connected:
                raise HTTPException(status_code=429, detail="Too many requests. Rate limit exceeded.")
            elif self._is_redis_connected:
                return

        # Fallback / In-Memory rate limiting (high performance, O(1) request path, no global lock)
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        now = time.time()
        ip_history = [t for t in self.history[client_ip] if now - t < self.window_seconds]
        if len(ip_history) >= self.requests_limit:
            raise HTTPException(status_code=429, detail="Too many requests. Rate limit exceeded.")

        ip_history.append(now)
        self.history[client_ip] = ip_history

    def reset(self):
        self.history.clear()

# Adjust rate limits dynamically if testing is detected
if "pytest" in sys.modules or os.getenv("TESTING") == "true":
    RATE_LIMIT_REQUESTS = 3
    RATE_LIMIT_WINDOW = 10
else:
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60

rate_limiter = RateLimiter(requests_limit=RATE_LIMIT_REQUESTS, window_seconds=RATE_LIMIT_WINDOW)
