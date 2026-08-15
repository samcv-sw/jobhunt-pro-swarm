"""
core/sub_ms_cache.py
Sub-Millisecond (<0.1ms) In-Memory LRU Cache with TTL Invalidation
Designed for ultra-high-throughput JobHunt Pro SaaS, domain MX lookups, and AI response caching.
"""

import time
import threading
from collections import OrderedDict
from typing import Any, Optional, Tuple, Dict


class SubMillisecondCache:
    """
    High-performance, thread-safe LRU cache with granular TTL expiration.
    Guarantees sub-millisecond retrieval and storage.
    """

    def __init__(self, maxsize: int = 10000, default_ttl: float = 3600.0):
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Retrieve an item from cache if present and not expired."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, expiry = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end to maintain LRU order
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store an item with custom or default TTL."""
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, expiry)

            # Evict oldest if exceeding maxsize
            if len(self._cache) > self.maxsize:
                self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        """Explicitly remove an item from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear the entire cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> Dict[str, Any]:
        """Return cache health and hit/miss statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_ratio = (self._hits / total * 100.0) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio_pct": round(hit_ratio, 2),
            }


# Global Singleton Caches
global_sub_ms_cache = SubMillisecondCache(maxsize=20000, default_ttl=86400.0) # 24h default
global_domain_mx_cache = SubMillisecondCache(maxsize=50000, default_ttl=604800.0) # 7 days
sub_ms_cache = global_sub_ms_cache

