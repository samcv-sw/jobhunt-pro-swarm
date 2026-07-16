# ──────────────────────────────────────────────────────────────────────────────
# cache_middleware.py - Response Caching & ETags for API Endpoints
# Implements HTTP caching headers and conditional request handling
# ──────────────────────────────────────────────────────────────────────────────

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.datastructures import MutableHeaders

logger = logging.getLogger(__name__)


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """Add HTTP caching headers to responses based on endpoint."""
    
    # Cache duration (seconds) by endpoint pattern
    CACHE_RULES = {
        # Never cache
        "/api/auth": 0,
        "/api/admin": 0,
        "/api/webhook": 0,
        
        # Cache public endpoints longer
        "/api/jobs": 3600,  # 1 hour
        "/api/companies": 3600,
        "/api/skills": 86400,  # 1 day
        "/api/categories": 86400,
        
        # Cache less frequently accessed data
        "/api/profile": 1800,  # 30 minutes
        "/api/applications": 300,  # 5 minutes
    }
    
    async def dispatch(self, request, call_next):
        """Inject caching headers based on route."""
        
        # Only cache GET requests
        if request.method != "GET":
            response = await call_next(request)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response
        
        # Determine cache duration
        path = request.url.path
        cache_duration = self._get_cache_duration(path)
        
        # Call the endpoint
        response = await call_next(request)
        
        # Apply caching headers
        if cache_duration > 0:
            response.headers["Cache-Control"] = f"public, max-age={cache_duration}"
            response.headers["Expires"] = self._get_expiry_header(cache_duration)
            
            # Add ETag for conditional requests
            if response.status_code == 200:
                await self._add_etag(response)
        else:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response
    
    def _get_cache_duration(self, path: str) -> int:
        """Determine cache duration for a given path."""
        for pattern, duration in self.CACHE_RULES.items():
            if path.startswith(pattern):
                return duration
        
        # Default: cache static assets for 30 days
        if path.startswith("/static/"):
            return 2592000  # 30 days
        
        # Default: no cache for unknown endpoints
        return 0
    
    @staticmethod
    def _get_expiry_header(duration_seconds: int) -> str:
        """Generate HTTP Expires header."""
        expiry = datetime.utcnow() + timedelta(seconds=duration_seconds)
        return expiry.strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    @staticmethod
    async def _add_etag(response: Response) -> None:
        """Add ETag header for cache validation."""
        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Generate ETag
        etag = f'"{hashlib.md5(body).hexdigest()}"'
        
        # Add to response
        headers = MutableHeaders(response.headers)
        headers["ETag"] = etag
        
        # Re-wrap body iterator
        async def body_iterator():
            yield body
        
        response.body_iterator = body_iterator()


class ConditionalRequestMiddleware(BaseHTTPMiddleware):
    """Handle HTTP conditional requests (If-None-Match, If-Modified-Since)."""
    
    async def dispatch(self, request, call_next):
        """Process conditional request headers."""
        
        # Get client-supplied ETag
        if_none_match = request.headers.get("If-None-Match")
        
        # Call endpoint
        response = await call_next(request)
        
        # Handle If-None-Match (ETag comparison)
        if if_none_match and response.status_code == 200:
            server_etag = response.headers.get("ETag")
            
            if server_etag and if_none_match == server_etag:
                # Return 304 Not Modified
                return Response(status_code=304, headers={"ETag": server_etag})
        
        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Enhanced cache control for specific response types."""
    
    async def dispatch(self, request, call_next):
        """Apply content-type specific caching rules."""
        
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")
        
        # JSON API responses
        if "application/json" in content_type:
            if response.status_code == 200:
                # Cache JSON responses by default (but short TTL)
                existing_cache = response.headers.get("Cache-Control", "")
                if "no-cache" not in existing_cache and "no-store" not in existing_cache:
                    response.headers["Cache-Control"] = "public, max-age=300"
        
        # Static assets
        elif any(ext in content_type for ext in ["image/", "text/css", "application/javascript"]):
            response.headers["Cache-Control"] = "public, max-age=31536000"  # 1 year
        
        # HTML documents
        elif "text/html" in content_type:
            if "admin" in request.url.path or "dashboard" in request.url.path:
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            else:
                response.headers["Cache-Control"] = "public, max-age=3600"
        
        return response


# Middleware configuration for app_v2.py
# Add to app initialization:
# app.add_middleware(ResponseCacheMiddleware)
# app.add_middleware(ConditionalRequestMiddleware)
# app.add_middleware(CacheControlMiddleware)
