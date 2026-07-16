# ──────────────────────────────────────────────────────────────────────────────
# auth_utils.py - Authentication & Authorization Utilities
# JWT tokens, OAuth, permission checks, role-based access control
# ──────────────────────────────────────────────────────────────────────────────

import jwt
import os
import logging
from typing import Optional, Dict, List, Set
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    RECRUITER = "recruiter"
    CANDIDATE = "candidate"
    MODERATOR = "moderator"
    VIEWER = "viewer"


class Permission(str, Enum):
    """System permissions."""
    # User management
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Job management
    JOB_READ = "job:read"
    JOB_CREATE = "job:create"
    JOB_UPDATE = "job:update"
    JOB_DELETE = "job:delete"
    
    # Application management
    APPLICATION_READ = "application:read"
    APPLICATION_UPDATE = "application:update"
    APPLICATION_DELETE = "application:delete"
    
    # Admin operations
    ADMIN_ACCESS = "admin:access"
    SETTINGS_UPDATE = "settings:update"
    ANALYTICS_VIEW = "analytics:view"
    AUDIT_LOG_VIEW = "audit:view"


# Role-permission mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        Permission.USER_READ, Permission.USER_CREATE, Permission.USER_UPDATE, Permission.USER_DELETE,
        Permission.JOB_READ, Permission.JOB_CREATE, Permission.JOB_UPDATE, Permission.JOB_DELETE,
        Permission.APPLICATION_READ, Permission.APPLICATION_UPDATE, Permission.APPLICATION_DELETE,
        Permission.ADMIN_ACCESS, Permission.SETTINGS_UPDATE, Permission.ANALYTICS_VIEW, Permission.AUDIT_LOG_VIEW,
    },
    UserRole.RECRUITER: {
        Permission.JOB_READ, Permission.JOB_CREATE, Permission.JOB_UPDATE, Permission.JOB_DELETE,
        Permission.APPLICATION_READ, Permission.APPLICATION_UPDATE,
        Permission.ANALYTICS_VIEW,
    },
    UserRole.CANDIDATE: {
        Permission.JOB_READ,
        Permission.APPLICATION_READ, Permission.APPLICATION_UPDATE,
        Permission.USER_READ, Permission.USER_UPDATE,
    },
    UserRole.MODERATOR: {
        Permission.USER_READ, Permission.APPLICATION_READ,
        Permission.AUDIT_LOG_VIEW,
    },
    UserRole.VIEWER: {
        Permission.JOB_READ, Permission.USER_READ,
    },
}


class JWTTokenManager:
    """JWT token generation and validation."""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "jobhunt-dev-secret")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.expiration_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    def generate_token(
        self,
        user_id: int,
        email: str,
        role: UserRole,
        additional_claims: Optional[Dict] = None,
    ) -> str:
        """Generate JWT token."""
        payload = {
            "user_id": user_id,
            "email": email,
            "role": role.value,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.expiration_hours),
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Token generated for user {user_id}")
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def generate_refresh_token(self, user_id: int) -> str:
        """Generate refresh token (longer expiration)."""
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=7),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


class PermissionChecker:
    """Check user permissions."""
    
    @staticmethod
    def has_permission(role: UserRole, permission: Permission) -> bool:
        """Check if role has permission."""
        return permission in ROLE_PERMISSIONS.get(role, set())
    
    @staticmethod
    def has_any_permission(role: UserRole, permissions: List[Permission]) -> bool:
        """Check if role has any of the permissions."""
        role_perms = ROLE_PERMISSIONS.get(role, set())
        return any(p in role_perms for p in permissions)
    
    @staticmethod
    def has_all_permissions(role: UserRole, permissions: List[Permission]) -> bool:
        """Check if role has all permissions."""
        role_perms = ROLE_PERMISSIONS.get(role, set())
        return all(p in role_perms for p in permissions)
    
    @staticmethod
    def get_role_permissions(role: UserRole) -> Set[Permission]:
        """Get all permissions for a role."""
        return ROLE_PERMISSIONS.get(role, set())


class RateLimitManager:
    """Manage per-user rate limiting."""
    
    def __init__(self):
        self._user_limits: Dict[int, Dict] = {}
        self._cleanup_interval = 3600  # 1 hour
    
    def check_limit(
        self,
        user_id: int,
        endpoint: str,
        limit: int = 100,
        window_seconds: int = 3600,
    ) -> tuple:
        """Check if user exceeded rate limit."""
        key = f"{user_id}:{endpoint}"
        now = datetime.utcnow()
        
        if key not in self._user_limits:
            self._user_limits[key] = {"count": 0, "first_request": now}
        
        user_data = self._user_limits[key]
        elapsed = (now - user_data["first_request"]).total_seconds()
        
        # Reset if window expired
        if elapsed > window_seconds:
            user_data["count"] = 0
            user_data["first_request"] = now
        
        # Increment counter
        user_data["count"] += 1
        
        # Check if exceeded
        remaining = max(0, limit - user_data["count"])
        exceeded = user_data["count"] > limit
        
        return exceeded, remaining
    
    def get_reset_time(self, user_id: int, endpoint: str) -> int:
        """Get seconds until rate limit resets."""
        key = f"{user_id}:{endpoint}"
        if key in self._user_limits:
            user_data = self._user_limits[key]
            window = 3600  # TODO: make configurable
            elapsed = (datetime.utcnow() - user_data["first_request"]).total_seconds()
            reset_in = max(0, int(window - elapsed))
            return reset_in
        return 0


class SessionManager:
    """Manage user sessions."""
    
    def __init__(self):
        self._sessions: Dict[str, Dict] = {}
    
    def create_session(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str,
    ) -> str:
        """Create new session."""
        import uuid
        session_id = str(uuid.uuid4())
        
        self._sessions[session_id] = {
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        }
        
        logger.info(f"Session created for user {user_id}: {session_id}")
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Validate session."""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            
            # Check if session expired (24 hours)
            age = (datetime.utcnow() - session["created_at"]).total_seconds()
            if age > 86400:
                del self._sessions[session_id]
                return None
            
            # Update last activity
            session["last_activity"] = datetime.utcnow()
            return session
        
        return None
    
    def destroy_session(self, session_id: str) -> bool:
        """Destroy session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Session destroyed: {session_id}")
            return True
        return False


# Decorators for FastAPI endpoints

def require_auth(func):
    """Require authentication."""
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Missing token")
        
        token_manager = JWTTokenManager()
        payload = token_manager.verify_token(token)
        if not payload:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Invalid token")
        
        request.state.user_id = payload["user_id"]
        request.state.role = UserRole(payload["role"])
        
        return await func(request, *args, **kwargs)
    
    return wrapper


def require_permission(permission: Permission):
    """Require specific permission."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            if not hasattr(request.state, "role"):
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if not PermissionChecker.has_permission(request.state.role, permission):
                from fastapi import HTTPException
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_role(*roles: UserRole):
    """Require specific role."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            if not hasattr(request.state, "role"):
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if request.state.role not in roles:
                from fastapi import HTTPException
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# Global instances
jwt_manager = JWTTokenManager()
permission_checker = PermissionChecker()
rate_limiter = RateLimitManager()
session_manager = SessionManager()
