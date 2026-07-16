# ──────────────────────────────────────────────────────────────────────────────
# request_context.py - Request Context & Distributed Tracing
# Tracks request lifecycle and correlates logs across services
# ──────────────────────────────────────────────────────────────────────────────

import contextvars
import logging
import uuid
import time
from typing import Optional, Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

logger = logging.getLogger(__name__)

# Context variables for request tracking
request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default=None)
user_id: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar("user_id", default=None)
session_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("session_id", default=None)
request_start_time: contextvars.ContextVar[float] = contextvars.ContextVar("request_start_time", default=0)


class RequestContext:
    """Stores request-scoped context information."""
    
    def __init__(
        self,
        request_id: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        method: str = "GET",
        path: str = "/",
        ip_address: str = "0.0.0.0",
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.session_id = session_id
        self.method = method
        self.path = path
        self.ip_address = ip_address
        self.start_time = time.time()
        self.metadata: Dict[str, Any] = {}
    
    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return (time.time() - self.start_time) * 1000
    
    def set_user(self, user_id: int, session_id: Optional[str] = None) -> None:
        """Set user information."""
        self.user_id = user_id
        if session_id:
            self.session_id = session_id
        user_id.set(user_id)
        if session_id:
            session_id.set(session_id)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Add custom metadata."""
        self.metadata[key] = value
    
    def to_dict(self) -> dict:
        """Convert context to dictionary."""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "method": self.method,
            "path": self.path,
            "ip_address": self.ip_address,
            "elapsed_ms": self.elapsed_ms,
            "timestamp": datetime.utcnow().isoformat(),
            **self.metadata,
        }


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to create and manage request context."""
    
    async def dispatch(self, req: Request, call_next):
        """Inject request context."""
        
        # Generate or extract request ID
        req_id = req.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Extract user info if available
        user_id_val = None
        session_id_val = req.headers.get("X-Session-ID")
        
        try:
            # Try to extract from JWT or session
            from web.shared import get_verified_user_id
            user_id_val = get_verified_user_id(req)
        except Exception:
            pass
        
        # Get IP address
        ip = req.client.host if req.client else "0.0.0.0"
        
        # Create context
        context = RequestContext(
            request_id=req_id,
            user_id=user_id_val,
            session_id=session_id_val,
            method=req.method,
            path=req.url.path,
            ip_address=ip,
        )
        
        # Set context variables
        request_id.set(req_id)
        user_id.set(user_id_val)
        session_id.set(session_id_val)
        request_start_time.set(time.time())
        
        # Store in request state
        req.state.context = context
        req.state.request_id = req_id
        req.state.user_id = user_id_val
        
        # Log request start
        logger.info(
            f"{req.method} {req.url.path}",
            extra={
                "request_id": req_id,
                "user_id": user_id_val,
                "ip": ip,
            }
        )
        
        # Process request
        response = await call_next(req)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = req_id
        
        # Log request completion
        elapsed_ms = context.elapsed_ms
        logger.info(
            f"{req.method} {req.url.path} {response.status_code} ({elapsed_ms:.1f}ms)",
            extra={
                "request_id": req_id,
                "user_id": user_id_val,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
            }
        )
        
        return response


class CorrelationIdFilter(logging.Filter):
    """Add request ID to all log records."""
    
    def filter(self, record):
        """Add context variables to log record."""
        try:
            record.request_id = request_id.get()
            record.user_id = user_id.get()
            record.session_id = session_id.get()
        except LookupError:
            record.request_id = None
            record.user_id = None
            record.session_id = None
        
        return True


def get_current_context() -> Optional[RequestContext]:
    """Get the current request context."""
    try:
        from starlette.requests import _request_scope_stack
        request = _request_scope_stack.top[0] if _request_scope_stack.top else None
        if request and hasattr(request, "state") and hasattr(request.state, "context"):
            return request.state.context
    except Exception:
        pass
    return None


def get_request_id() -> Optional[str]:
    """Get current request ID."""
    try:
        return request_id.get()
    except LookupError:
        return None


def get_user_id() -> Optional[int]:
    """Get current user ID."""
    try:
        return user_id.get()
    except LookupError:
        return None


def get_session_id() -> Optional[str]:
    """Get current session ID."""
    try:
        return session_id.get()
    except LookupError:
        return None
