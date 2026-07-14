"""
local_cache.py — Thread-safe in-memory TTL cache
=================================================
Acts as a local shield in front of Redis to prevent exceeding the 10 000
commands/day cap on Upstash free tier (or similar).

Usage:
    from core.local_cache import local_cache          # singleton
    local_cache.set("user:42:plan", "pro", ttl_seconds=300)
    value = local_cache.get("user:42:plan")           # None on miss
    local_cache.delete("user:42:plan")
    local_cache.clear_expired()                        # prune stale entries
"""

import logging
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)


class LocalTTLCache:
    """
    Thread-safe dictionary cache with per-entry TTL expiry.

    Stores entries as ``{key: (value, expiry_epoch_float)}``.
    An ``expiry`` of ``None`` means the entry never expires.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Any:
        """
        Return the cached value for *key*, or ``None`` if absent/expired.

        Logs a WARNING on every miss so operators know when traffic is
        falling through to the upstream Redis layer.
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                logger.warning(
                    "[LocalTTLCache] Cache MISS for key=%r — "
                    "falling through to Redis (counts toward daily quota).",
                    key,
                )
                return None

            value, expiry = entry
            if expiry is not None and time.monotonic() > expiry:
                # Expired — evict lazily and report as a miss
                del self._store[key]
                logger.warning(
                    "[LocalTTLCache] Cache MISS (expired) for key=%r — "
                    "falling through to Redis.",
                    key,
                )
                return None

            return value

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        """
        Store *value* under *key*.

        Args:
            key:         Cache key (string).
            value:       Any picklable Python object.
            ttl_seconds: Seconds until expiry.  ``None`` = never expires.
        """
        expiry: float | None = (
            time.monotonic() + ttl_seconds if ttl_seconds is not None else None
        )
        with self._lock:
            self._store[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """
        Remove *key* from the cache.

        Returns:
            ``True`` if the key existed and was removed, ``False`` otherwise.
        """
        with self._lock:
            existed = key in self._store
            self._store.pop(key, None)
            return existed

    def clear_expired(self) -> int:
        """
        Remove all entries that have passed their TTL.

        Returns:
            Number of entries pruned.
        """
        now = time.monotonic()
        with self._lock:
            expired_keys = [
                k for k, (_, exp) in self._store.items()
                if exp is not None and now > exp
            ]
            for k in expired_keys:
                del self._store[k]
        if expired_keys:
            logger.debug(
                "[LocalTTLCache] Pruned %d expired entry/entries: %s",
                len(expired_keys),
                expired_keys,
            )
        return len(expired_keys)

    def clear(self) -> None:
        """Wipe the entire cache (all keys, regardless of TTL)."""
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        """Return the current number of entries (including not-yet-pruned expired ones)."""
        with self._lock:
            return len(self._store)

    def __repr__(self) -> str:
        with self._lock:
            return f"<LocalTTLCache entries={len(self._store)}>"


# ---------------------------------------------------------------------------
# Module-level singleton — import and use directly
# ---------------------------------------------------------------------------
local_cache: LocalTTLCache = LocalTTLCache()
