import logging
from typing import Any

try:
    from curl_cffi import requests as curl_requests
    _CURL_CFFI_AVAILABLE = True
except ImportError:
    import httpx
    _CURL_CFFI_AVAILABLE = False

logger = logging.getLogger(__name__)

class StealthClient:
    """
    A unified HTTP client that uses curl_cffi to impersonate real browser TLS fingerprints.
    Bypasses Cloudflare 1020 errors and DataDome blocks.
    Falls back to httpx if curl_cffi is missing.
    """
    def __init__(self, impersonate: str = "chrome110", timeout: float = 15.0) -> None:
        self.impersonate = impersonate
        self.timeout = timeout

    def get(self, url: str, **kwargs: Any) -> Any:
        kwargs.setdefault("timeout", self.timeout)
        if _CURL_CFFI_AVAILABLE:
            kwargs.setdefault("impersonate", self.impersonate)
            try:
                return curl_requests.get(url, **kwargs)
            except Exception as e:
                logger.error(f"[StealthClient] GET {url} failed with curl_cffi: {e}")
                raise
        else:
            logger.warning("[StealthClient] curl_cffi not available, falling back to httpx (High risk of bot detection)")
            # httpx doesn't accept 'impersonate' argument
            kwargs.pop("impersonate", None)
            return httpx.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Any:
        kwargs.setdefault("timeout", self.timeout)
        if _CURL_CFFI_AVAILABLE:
            kwargs.setdefault("impersonate", self.impersonate)
            try:
                return curl_requests.post(url, **kwargs)
            except Exception as e:
                logger.error(f"[StealthClient] POST {url} failed with curl_cffi: {e}")
                raise
        else:
            logger.warning("[StealthClient] curl_cffi not available, falling back to httpx (High risk of bot detection)")
            kwargs.pop("impersonate", None)
            return httpx.post(url, **kwargs)

class AsyncStealthClient:
    """Async version of StealthClient."""
    def __init__(self, impersonate: str = "chrome110", timeout: float = 15.0) -> None:
        self.impersonate = impersonate
        self.timeout = timeout

    async def get(self, url: str, **kwargs: Any) -> Any:
        kwargs.setdefault("timeout", self.timeout)
        if _CURL_CFFI_AVAILABLE:
            kwargs.setdefault("impersonate", self.impersonate)
            try:
                async with curl_requests.AsyncSession() as session:
                    return await session.get(url, **kwargs)
            except Exception as e:
                logger.error(f"[AsyncStealthClient] GET {url} failed: {e}")
                raise
        else:
            kwargs.pop("impersonate", None)
            async with httpx.AsyncClient() as client:
                return await client.get(url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Any:
        kwargs.setdefault("timeout", self.timeout)
        if _CURL_CFFI_AVAILABLE:
            kwargs.setdefault("impersonate", self.impersonate)
            try:
                async with curl_requests.AsyncSession() as session:
                    return await session.post(url, **kwargs)
            except Exception as e:
                logger.error(f"[AsyncStealthClient] POST {url} failed: {e}")
                raise
        else:
            kwargs.pop("impersonate", None)
            async with httpx.AsyncClient() as client:
                return await client.post(url, **kwargs)

# Singleton instances for easy import
stealth_http = StealthClient()
async_stealth_http = AsyncStealthClient()

