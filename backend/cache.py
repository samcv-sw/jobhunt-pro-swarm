"""
Cache initialization — uses Redis backend when REDIS_URL is available,
falls back to in-memory backend for local/free-tier SQLite environments.

Upstash free-tier note: max 10 concurrent connections. The pool is capped
at 10 to respect this limit across all cache operations.
"""
import logging
import os

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

logger = logging.getLogger(__name__)


def setup_cache(app: FastAPI) -> None:  # noqa: ARG001
    """Initialise the FastAPI cache backend.

    Uses Redis (via ``fastapi_cache.backends.redis.RedisBackend``) when
    ``REDIS_URL`` is set in the environment, honouring the Upstash free-tier
    limit of 10 concurrent connections.  Falls back to an in-process
    ``InMemoryBackend`` for local development and environments without Redis.

    Args:
        app: The FastAPI application instance (unused directly; kept for
             consistency with lifespan hooks that pass it).
    """
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            from fastapi_cache.backends.redis import RedisBackend
            from redis import asyncio as aioredis  # type: ignore[import]

            pool = aioredis.ConnectionPool.from_url(
                redis_url,
                max_connections=10,   # Respect Upstash free-tier limit
                decode_responses=True,
            )
            redis_client = aioredis.Redis(connection_pool=pool)
            FastAPICache.init(RedisBackend(redis_client), prefix="jhp-cache")
            logger.info(
                '{"msg": "Redis-backed API cache initialized", '
                '"max_connections": 10, "prefix": "jhp-cache"}'
            )
            return
        except Exception as exc:  # pragma: no cover
            logger.warning(
                '{"msg": "Redis cache init failed, falling back to in-memory", '
                '"error": "%s"}',
                exc,
            )

    FastAPICache.init(InMemoryBackend(), prefix="jhp-cache")
    logger.info('{"msg": "In-memory API cache initialized (no REDIS_URL set)"}')
