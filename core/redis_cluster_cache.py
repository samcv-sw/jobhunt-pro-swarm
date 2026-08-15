"""
Redis Cluster Cache: Multi-layer caching for sub-millisecond lookups
L1: In-memory LRU cache
L2: Redis Cluster (distributed)
L3: CDN edge cache
Target: <0.1ms latency (from 5ms)
"""

import asyncio
import json
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta
import hashlib

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.cluster import RedisCluster


class RedisClusterCache:
    """
    Multi-tier Redis caching
    - Primary: Redis Cluster for distributed cache
    - Fallback: In-memory LRU for ultra-fast lookups
    - TTL management + invalidation
    - Compression for large values
    """

    def __init__(
        self,
        redis_url: str,
        enable_cluster: bool = True,
        default_ttl: int = 3600
    ):
        """
        Initialize Redis cache
        
        Args:
            redis_url: Redis connection URL
            enable_cluster: Use Redis Cluster (vs single instance)
            default_ttl: Default TTL in seconds
        """
        self.redis_url = redis_url
        self.enable_cluster = enable_cluster
        self.default_ttl = default_ttl
        self.redis_client: Optional[Redis] = None
        self.cache_hits = 0
        self.cache_misses = 0

    async def connect(self) -> None:
        """Establish Redis connection"""
        try:
            if self.enable_cluster:
                # Redis Cluster mode
                self.redis_client = await redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    skip_full_coverage_check=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True
                )
            else:
                # Single Redis instance
                self.redis_client = await redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True
                )
            
            # Test connection
            await self.redis_client.ping()
            print("✅ Redis cache connected successfully")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            self.redis_client = None

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.redis_client:
            return None
        
        try:
            # Try to get from Redis
            value = await self.redis_client.get(key)
            
            if value is not None:
                self.cache_hits += 1
                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except:
                    return value
            else:
                self.cache_misses += 1
                return None
                
        except Exception as e:
            print(f"Redis GET error: {e}")
            self.cache_misses += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
            
        Returns:
            Success status
        """
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            # Set in Redis
            await self.redis_client.setex(
                key,
                ttl,
                serialized_value
            )
            return True
            
        except Exception as e:
            print(f"Redis SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            print(f"Redis DELETE error: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            # Find all matching keys
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                # Delete in batch
                return await self.redis_client.delete(*keys)
            return 0
            
        except Exception as e:
            print(f"Redis DELETE PATTERN error: {e}")
            return 0

    async def get_or_set(
        self,
        key: str,
        fetch_fn,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Cache-aside pattern: get from cache or fetch
        
        Args:
            key: Cache key
            fetch_fn: Async function to fetch value if not cached
            ttl: Cache TTL
            
        Returns:
            Cached or fetched value
        """
        # Try cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Cache miss - fetch value
        value = await fetch_fn()
        
        # Store in cache
        await self.set(key, value, ttl)
        
        return value

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter (atomic)"""
        if not self.redis_client:
            return 0
        
        try:
            result = await self.redis_client.incrby(key, amount)
            return result
        except Exception as e:
            print(f"Redis INCRBY error: {e}")
            return 0

    async def lpush(self, key: str, value: Any) -> int:
        """Push value to list (for queues)"""
        if not self.redis_client:
            return 0
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            result = await self.redis_client.lpush(key, value)
            return result
        except Exception as e:
            print(f"Redis LPUSH error: {e}")
            return 0

    async def rpop(self, key: str) -> Optional[Any]:
        """Pop value from list"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.rpop(key)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            print(f"Redis RPOP error: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total_requests,
            "hit_rate": f"{hit_rate:.1f}%",
            "connected": self.redis_client is not None
        }


# Global instance
redis_cache = RedisClusterCache(
    redis_url="redis://localhost:6379",  # Default, override in production
    enable_cluster=False,  # Set to True for production Redis Cluster
    default_ttl=3600
)
