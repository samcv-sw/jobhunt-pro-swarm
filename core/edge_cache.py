import logging
import os
import httpx

logger = logging.getLogger(__name__)


class EdgeCache:
    """
    Serverless Edge Cache using Upstash Redis REST API.
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
        """Retrieve a value from the edge cache by key."""
        return await self._execute("GET", key)

    async def set(self, key: str, value: str, ex: int = None) -> object:
        """Store a value in the edge cache, with optional TTL in seconds."""
        if ex:
            return await self._execute("SET", key, value, "EX", ex)
        return await self._execute("SET", key, value)

    async def incr(self, key: str) -> object:
        """Atomically increment an integer counter key."""
        return await self._execute("INCR", key)

    async def expire(self, key: str, seconds: int) -> object:
        """Set an expiry on a key in seconds."""
        return await self._execute("EXPIRE", key, seconds)

    async def close(self):
        """Gracefully release cached network connections."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global singleton
edge_cache = EdgeCache()
