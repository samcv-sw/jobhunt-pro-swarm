import asyncio
import inspect
import ipaddress
import logging
import random
import socket
import time
import urllib.parse
from typing import Any

try:
    from curl_cffi import requests as curl_requests
    _CURL_CFFI_AVAILABLE = True
except ImportError:
    import httpx
    _CURL_CFFI_AVAILABLE = False

# Lazy import of proxy_pool to avoid circular imports at module load time
def _get_proxy() -> dict | None:
    """Return a rotating free proxy dict, or None if pool is empty/unavailable."""
    try:
        from core.proxy_pool import get_proxy
        return get_proxy()
    except Exception:
        return None

def _evict_proxy(proxy_url: str) -> None:
    """Evict a failed proxy from the pool."""
    try:
        from core.proxy_pool import evict_proxy
        evict_proxy(proxy_url)
    except Exception:
        pass

logger = logging.getLogger(__name__)

def is_safe_url(url: str) -> bool:
    """
    Validate a URL to prevent Server-Side Request Forgery (SSRF) attacks.
    Ensures that the URL resolves to a public, non-private IP address.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Try to parse hostname directly as IP address
        try:
            ip = ipaddress.ip_address(hostname)
            return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_unspecified or hostname == "0.0.0.0")
        except ValueError:
            # Not an IP string, resolve it
            pass

        # Resolve hostname to IPs
        ips = socket.getaddrinfo(hostname, None)
        for _family, _, _, _, sockaddr in ips:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_unspecified or ip_str == "0.0.0.0":
                return False
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Exponential Backoff Helpers
# ---------------------------------------------------------------------------
_MAX_RETRIES = 5
_RETRY_STATUS_CODES = {429, 503, 502, 504}


def _backoff_delay(attempt: int) -> float:
    """Return the delay (seconds) for a given retry attempt using exponential backoff with jitter."""
    return min(2 ** attempt + random.random(), 60.0)


def with_backoff_retry(fn, url: str, *args, **kwargs):
    """
    Execute a synchronous HTTP call with exponential backoff.
    Retries up to _MAX_RETRIES times on connection errors or _RETRY_STATUS_CODES responses.

    Args:
        fn: Callable that performs the HTTP request.
        url: The URL being requested (for logging only).
        *args, **kwargs: Passed through to fn.

    Returns:
        The response object from the final successful (or last-retry) call.

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exc = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = fn(url, *args, **kwargs)
            if response.status_code not in _RETRY_STATUS_CODES:
                return response
            delay = _backoff_delay(attempt)
            logger.warning(
                f"[Backoff] {url} returned {response.status_code} (attempt {attempt + 1}/{_MAX_RETRIES}). "
                f"Retrying in {delay:.1f}s..."
            )
            if attempt < _MAX_RETRIES - 1:
                time.sleep(delay)
            last_exc = None  # status-code based retry, not an exception
            if attempt == _MAX_RETRIES - 1:
                return response
        except Exception as e:
            delay = _backoff_delay(attempt)
            logger.warning(
                f"[Backoff] {url} raised {type(e).__name__} (attempt {attempt + 1}/{_MAX_RETRIES}). "
                f"Retrying in {delay:.1f}s..."
            )
            last_exc = e
            if attempt < _MAX_RETRIES - 1:
                time.sleep(delay)
    if last_exc is not None:
        raise last_exc


async def async_with_backoff_retry(fn, url: str, *args, **kwargs):
    """
    Execute an async HTTP call with exponential backoff.
    Same semantics as with_backoff_retry but for coroutines.
    """
    last_exc = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = await fn(url, *args, **kwargs)
            if response.status_code not in _RETRY_STATUS_CODES:
                return response
            delay = _backoff_delay(attempt)
            logger.warning(
                f"[AsyncBackoff] {url} returned {response.status_code} (attempt {attempt + 1}/{_MAX_RETRIES}). "
                f"Retrying in {delay:.1f}s..."
            )
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(delay)
            last_exc = None
            if attempt == _MAX_RETRIES - 1:
                return response
        except Exception as e:
            delay = _backoff_delay(attempt)
            logger.warning(
                f"[AsyncBackoff] {url} raised {type(e).__name__} (attempt {attempt + 1}/{_MAX_RETRIES}). "
                f"Retrying in {delay:.1f}s..."
            )
            last_exc = e
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(delay)
    if last_exc is not None:
        raise last_exc


class StealthClient:
    """
    A unified HTTP client that uses curl_cffi to impersonate real browser TLS fingerprints.
    Bypasses Cloudflare 1020 errors and DataDome blocks.
    Falls back to httpx if curl_cffi is missing.
    Supports session reuse across multiple requests.
    """
    def __init__(self, impersonate: str = "chrome120", timeout: float = 15.0) -> None:
        self.impersonate = impersonate
        self.timeout = timeout
        self._session = None

    def get_session(self) -> Any:
        if self._session is None:
            if _CURL_CFFI_AVAILABLE:
                logger.info(f"[StealthClient] Initializing curl_cffi session with {self.impersonate}")
                self._session = curl_requests.Session(impersonate=self.impersonate, timeout=self.timeout)
            else:
                logger.info("[StealthClient] Initializing httpx session fallback (HTTP/2 enabled)")
                self._session = httpx.Client(timeout=self.timeout, http2=True)
        return self._session

    def get(self, url: str, **kwargs: Any) -> Any:
        if not is_safe_url(url):
            raise ValueError("Unsafe URL: SSRF request blocked.")
        kwargs.setdefault("timeout", self.timeout)
        session = self.get_session()
        if _CURL_CFFI_AVAILABLE:
            kwargs.setdefault("impersonate", self.impersonate)
            # Try via rotating proxy first; fall back to direct on failure
            proxy = _get_proxy()
            if proxy and "proxies" not in kwargs:
                try:
                    return session.get(url, proxies=proxy, **kwargs)
                except Exception as proxy_exc:
                    logger.warning(
                        "[StealthClient] Proxy %s failed for GET %s (%s). Evicting and retrying direct.",
                        proxy.get('https'), url, proxy_exc,
                    )
                    _evict_proxy(proxy.get('https', ''))
            try:
                return session.get(url, **kwargs)
            except Exception as e:
                logger.error(f"[StealthClient] GET {url} failed with curl_cffi: {e}")
                raise
        else:
            logger.warning("[StealthClient] curl_cffi not available, falling back to httpx (High risk of bot detection)")
            kwargs.pop("impersonate", None)
            proxy = _get_proxy()
            if proxy and "proxies" not in kwargs:
                try:
                    return session.get(url, proxies=proxy, **kwargs)
                except Exception as proxy_exc:
                    logger.warning("[StealthClient] httpx proxy failed, retrying direct: %s", proxy_exc)
                    _evict_proxy(proxy.get('https', ''))
            return session.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Any:
        if not is_safe_url(url):
            raise ValueError("Unsafe URL: SSRF request blocked.")
        kwargs.setdefault("timeout", self.timeout)
        session = self.get_session()
        if _CURL_CFFI_AVAILABLE:
            kwargs.setdefault("impersonate", self.impersonate)
            proxy = _get_proxy()
            if proxy and "proxies" not in kwargs:
                try:
                    return session.post(url, proxies=proxy, **kwargs)
                except Exception as proxy_exc:
                    logger.warning(
                        "[StealthClient] Proxy %s failed for POST %s (%s). Evicting and retrying direct.",
                        proxy.get('https'), url, proxy_exc,
                    )
                    _evict_proxy(proxy.get('https', ''))
            try:
                return session.post(url, **kwargs)
            except Exception as e:
                logger.error(f"[StealthClient] POST {url} failed with curl_cffi: {e}")
                raise
        else:
            logger.warning("[StealthClient] curl_cffi not available, falling back to httpx (High risk of bot detection)")
            kwargs.pop("impersonate", None)
            proxy = _get_proxy()
            if proxy and "proxies" not in kwargs:
                try:
                    return session.post(url, proxies=proxy, **kwargs)
                except Exception as proxy_exc:
                    logger.warning("[StealthClient] httpx proxy failed, retrying direct: %s", proxy_exc)
                    _evict_proxy(proxy.get('https', ''))
            return session.post(url, **kwargs)

    def close(self) -> None:
        if self._session:
            try:
                self._session.close()
            except Exception as e:
                logger.warning(f"[StealthClient] Error closing session: {e}")
            self._session = None


class AsyncStealthClient:
    """Async version of StealthClient supporting asynchronous session reuse."""
    def __init__(self, impersonate: str = "chrome120", timeout: float = 15.0) -> None:
        self.impersonate = impersonate
        self.timeout = timeout
        self._session = None

    async def get_session(self) -> Any:
        if self._session is None:
            if _CURL_CFFI_AVAILABLE:
                logger.info(f"[AsyncStealthClient] Initializing curl_cffi async session with {self.impersonate}")
                self._session = curl_requests.AsyncSession(impersonate=self.impersonate, timeout=self.timeout)
            else:
                logger.info("[AsyncStealthClient] Initializing httpx async session fallback")
                self._session = httpx.AsyncClient(timeout=self.timeout)
        return self._session

    async def get(self, url: str, **kwargs: Any) -> Any:
        if not is_safe_url(url):
            raise ValueError("Unsafe URL: SSRF request blocked.")
        kwargs.setdefault("timeout", self.timeout)
        session = await self.get_session()
        if _CURL_CFFI_AVAILABLE:
            kwargs.setdefault("impersonate", self.impersonate)
            try:
                return await session.get(url, **kwargs)
            except Exception as e:
                logger.error(f"[AsyncStealthClient] GET {url} failed: {e}")
                raise
        else:
            kwargs.pop("impersonate", None)
            return await session.get(url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Any:
        if not is_safe_url(url):
            raise ValueError("Unsafe URL: SSRF request blocked.")
        kwargs.setdefault("timeout", self.timeout)
        session = await self.get_session()
        if _CURL_CFFI_AVAILABLE:
            kwargs.setdefault("impersonate", self.impersonate)
            try:
                return await session.post(url, **kwargs)
            except Exception as e:
                logger.error(f"[AsyncStealthClient] POST {url} failed: {e}")
                raise
        else:
            kwargs.pop("impersonate", None)
            return await session.post(url, **kwargs)

    async def close(self) -> None:
        if self._session:
            try:
                if hasattr(self._session, "aclose"):
                    await self._session.aclose()
                elif hasattr(self._session, "close"):
                    res = self._session.close()
                    if inspect.iscoroutine(res):
                        await res
            except Exception as e:
                logger.warning(f"[AsyncStealthClient] Error closing session: {e}")
            self._session = None


# Singleton instances for easy import
stealth_http = StealthClient()
async_stealth_http = AsyncStealthClient()


async def fetch_with_backoff(
    url: str,
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> str:
    """Fetch a URL with exponential backoff on transient failures.

    Retries up to ``max_retries`` times with exponentially increasing delays
    plus random jitter to avoid thundering herd effects.

    Args:
        url: Target URL to fetch.
        max_retries: Maximum number of retry attempts after the initial try.
        base_delay: Base delay in seconds before the first retry.
        max_delay: Maximum delay cap between retries.

    Returns:
        Response text on success.

    Raises:
        Exception: Re-raises the last exception after all retries are exhausted.
    """
    import asyncio
    import logging
    import random

    import httpx

    _log = logging.getLogger(__name__)
    last_exc: Exception | None = None

    if not is_safe_url(url):
        raise ValueError("Unsafe URL: SSRF request blocked.")
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries:
                delay = min(base_delay * (2 ** attempt) + random.uniform(0.0, 1.0), max_delay)
                _log.warning(
                    '{"msg": "fetch_with_backoff retry", "url": "%s", "attempt": %d, "delay_s": %.2f, "error": "%s"}',
                    url, attempt + 1, delay, exc,
                )
                await asyncio.sleep(delay)

    raise last_exc  # type: ignore[misc]
