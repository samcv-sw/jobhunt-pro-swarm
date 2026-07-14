import logging
import os
import threading
import time

import httpx

logger = logging.getLogger(__name__)


class EdgeCache:
    """
    Serverless Edge Cache using Upstash Redis REST API with L1 memory cache shield.
    Bypasses standard Redis sockets to avoid connection limits and scaling bottlenecks.
    """

    def __init__(self) -> None:
        """Initialise and detect Upstash Redis credentials from the environment."""
        self.url = os.environ.get("UPSTASH_REDIS_REST_URL")
        self.token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
        self.enabled = bool(self.url and self.token)
        self._client = None

        if self.enabled:
            # Ensure URL doesn't have trailing slash for clean path building
            self.url = self.url.rstrip("/")

        # Thread-safe L1 cache
        self._l1_cache = {}  # key -> (value, expiry_time)
        self._l1_lock = threading.Lock()
        self._max_l1_size = 2000

    def _get_l1_ttl(self, key: str) -> float:
        if key.startswith("llm:cl:"):
            return 600.0
        elif "ats" in key:
            return 1800.0
        elif "campaigns" in key:
            return 60.0
        elif "groq" in key or "rate_limit" in key:
            return 5.0
        return 300.0  # Default 5 min

    def _cleanup_l1(self, now: float) -> None:
        # Must be called within self._l1_lock
        expired = [k for k, (_, exp) in self._l1_cache.items() if now >= exp]
        for k in expired:
            del self._l1_cache[k]

    def _set_l1(self, key: str, value: object, ttl: float) -> None:
        # Must be called within self._l1_lock
        now = time.time()
        if len(self._l1_cache) >= self._max_l1_size and key not in self._l1_cache:
            self._cleanup_l1(now)
            if len(self._l1_cache) >= self._max_l1_size:
                # FIFO eviction
                first_key = next(iter(self._l1_cache))
                del self._l1_cache[first_key]
        self._l1_cache[key] = (value, now + ttl)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=5.0)
        return self._client

    async def _execute(self, command: str, *args) -> object:
        """Execute a Redis command via the Upstash REST API."""
        if not self.enabled:
            return None

        try:
            client = await self._get_client()
            payload = [command] + list(args)
            response = await client.post(
                self.url,
                headers={"Authorization": f"Bearer {self.token}"},
                json=payload,
            )
            response.raise_for_status()
            return response.json().get("result")
        except Exception as e:
            logger.error(f"Edge Cache Error: {e}")
            return None

    async def get(self, key: str) -> object:
        """Retrieve a value from the edge cache by key, checking L1 first."""
        now = time.time()
        with self._l1_lock:
            if key in self._l1_cache:
                val, exp = self._l1_cache[key]
                if now < exp:
                    return val
                else:
                    del self._l1_cache[key]

        val = await self._execute("GET", key)
        if val is not None:
            ttl = self._get_l1_ttl(key)
            with self._l1_lock:
                self._set_l1(key, val, ttl)
        return val

    async def set(self, key: str, value: str, ex: int = None) -> object:
        """Store a value in the edge cache, writing through L1 memory cache."""
        ttl = self._get_l1_ttl(key)
        if ex is not None:
            ttl = min(float(ex), ttl)

        with self._l1_lock:
            self._set_l1(key, value, ttl)

        if ex:
            return await self._execute("SET", key, value, "EX", ex)
        return await self._execute("SET", key, value)

    async def incr(self, key: str) -> object:
        """Atomically increment an integer counter key, invalidating L1."""
        with self._l1_lock:
            self._l1_cache.pop(key, None)
        return await self._execute("INCR", key)

    async def expire(self, key: str, seconds: int) -> object:
        """Set an expiry on a key in seconds, updating L1 if present."""
        now = time.time()
        with self._l1_lock:
            if key in self._l1_cache:
                val, _ = self._l1_cache[key]
                self._l1_cache[key] = (val, now + seconds)
        return await self._execute("EXPIRE", key, seconds)

    async def delete(self, *keys: str) -> object:
        """Delete one or more keys, invalidating L1 cache."""
        with self._l1_lock:
            for key in keys:
                self._l1_cache.pop(key, None)
        return await self._execute("DEL", *keys)

    async def keys(self, pattern: str) -> list:
        """Find all keys matching the given pattern."""
        res = await self._execute("KEYS", pattern)
        return res or []

    async def close(self):
        """Gracefully release cached network connections."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global singleton
edge_cache = EdgeCache()


# ─────────────────────────────────────────────────────────────────────────────
# LLM Result Caching helpers
# ─────────────────────────────────────────────────────────────────────────────

import hashlib as _hashlib
import json as _json
import logging as _log_module

_edge_logger = _log_module.getLogger(__name__)


def _make_llm_cache_key(job_description: str, user_cv: str) -> str:
    """Create a deterministic cache key for LLM cover letter results.

    Args:
        job_description: Job description text (first 500 chars used).
        user_cv: User CV text (first 200 chars used).

    Returns:
        Hex string cache key prefixed with 'llm:cl:'.
    """
    raw = (job_description[:500] + "|||" + user_cv[:200]).encode("utf-8")
    return "llm:cl:" + _hashlib.sha256(raw).hexdigest()[:32]


async def cache_llm_result(job_description: str, user_cv: str, result: dict, ttl: int = 3600) -> None:
    """Cache a cover letter generation result to avoid redundant LLM calls.

    Args:
        job_description: The job description text.
        user_cv: The user CV text.
        result: JSON-serializable LLM result dict.
        ttl: Cache TTL in seconds (default 1 hour).
    """
    key = _make_llm_cache_key(job_description, user_cv)
    try:
        await edge_cache.set(key, _json.dumps(result), ex=ttl)
        _edge_logger.debug('{"msg": "LLM result cached", "key": "%s", "ttl": %d}', key, ttl)
    except Exception as exc:
        _edge_logger.warning('{"msg": "LLM cache write failed", "error": "%s"}', exc)


async def get_cached_llm_result(job_description: str, user_cv: str) -> dict | None:
    """Retrieve a cached cover letter result if available.

    Args:
        job_description: The job description text.
        user_cv: The user CV text.

    Returns:
        Cached result dict, or None on cache miss.
    """
    key = _make_llm_cache_key(job_description, user_cv)
    try:
        raw = await edge_cache.get(key)
        if raw:
            _edge_logger.info('{"msg": "LLM cache HIT", "key": "%s"}', key)
            return _json.loads(raw)
        _edge_logger.debug('{"msg": "LLM cache MISS", "key": "%s"}', key)
    except Exception as exc:
        _edge_logger.warning('{"msg": "LLM cache read failed", "error": "%s"}', exc)
    return None
