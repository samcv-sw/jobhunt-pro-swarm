import os
import httpx
import logging

logger = logging.getLogger(__name__)

class EdgeCache:
    """
    Serverless Edge Cache using Upstash Redis REST API.
    Bypasses standard Redis sockets to avoid connection limits and scaling bottlenecks.
    """
    def __init__(self):
        self.url = os.environ.get("UPSTASH_REDIS_REST_URL")
        self.token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
        self.enabled = bool(self.url and self.token)
        
        if self.enabled:
            # Ensure URL doesn't have trailing slash for clean path building
            self.url = self.url.rstrip("/")

    async def _execute(self, command: str, *args):
        if not self.enabled:
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                payload = [command] + list(args)
                response = await client.post(
                    self.url,
                    headers={"Authorization": f"Bearer {self.token}"},
                    json=payload,
                    timeout=5.0
                )
                response.raise_for_status()
                return response.json().get("result")
        except Exception as e:
            logger.error(f"Edge Cache Error: {e}")
            return None

    async def get(self, key: str):
        return await self._execute("GET", key)

    async def set(self, key: str, value: str, ex: int = None):
        if ex:
            return await self._execute("SET", key, value, "EX", ex)
        return await self._execute("SET", key, value)
        
    async def incr(self, key: str):
        return await self._execute("INCR", key)

    async def expire(self, key: str, seconds: int):
        return await self._execute("EXPIRE", key, seconds)

# Global singleton
edge_cache = EdgeCache()
