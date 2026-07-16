"""
Authentication module handling JWT generation and validation.
Secures the Enterprise API endpoints.
"""
import contextlib
import ipaddress
import logging
import os
import random
import sys
import threading
import time
from collections import defaultdict

import jwt
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

raw_keys = os.environ.get("JWT_SECRET_KEYS")
JWT_SECRET_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()] if raw_keys else []
if not JWT_SECRET_KEYS:
    single_key = os.environ.get("JWT_SECRET_KEY")
    if not single_key:
        if os.getenv("TESTING") == "true" or "pytest" in sys.modules or "unittest" in sys.modules:
            single_key = "jobhunt-pro-secret-key-32bytes-ok!!"
        else:
            raise ValueError("JWT_SECRET_KEYS or JWT_SECRET_KEY environment variable is not set in production context.")
    JWT_SECRET_KEYS = [single_key]

JWT_SECRET_KEY = JWT_SECRET_KEYS[0]

JWT_ALGORITHM = "HS256"

# We use HTTPBearer security scheme
security = HTTPBearer(auto_error=False)

# Detect test environment once at import time — rate limiting is skipped during tests
# to avoid cross-test IP lockouts. The rate limiter logic is tested directly in
# tests/test_hardening_v2.py via unit tests.
_IS_TESTING: bool = (
    os.getenv("TESTING", "false").lower() == "true"
    or "pytest" in sys.modules
    or "unittest" in sys.modules
)

# ---------------------------------------------------------------------------
# Brute-Force Rate Limiter — in-memory IP-based sliding window
# ---------------------------------------------------------------------------
_FAIL_WINDOW_SECONDS: int = 60       # Sliding window length (seconds)
_MAX_FAILURES: int = 5               # Max failures before lockout
_LOCKOUT_SECONDS: int = 300          # Lockout duration (seconds)

_rate_lock = threading.Lock()

# { ip: {"failures": [timestamp, ...], "locked_until": float | None} }
_rate_state: dict = defaultdict(lambda: {"failures": [], "locked_until": None})

_last_prune_time: float = 0.0

_logger = logging.getLogger(__name__)

# Optional distributed backend (Redis). When REDIS_URL is configured the limiter
# coordinates lockouts across all worker processes; otherwise it degrades to the
# in-memory store above (single-worker only). IMP-SEC-BF
_redis_client = None
_redis_available = False
try:
    import redis  # sync client
    _REDIS_URL = os.getenv("REDIS_URL")
    if _REDIS_URL:
        try:
            _redis_client = redis.Redis.from_url(
                _REDIS_URL, socket_connect_timeout=1.0, socket_timeout=1.0,
                decode_responses=True, retry_on_timeout=False,
            )
            _redis_client.ping()
            _redis_available = True
            _logger.info("Brute-force limiter connected to Redis (distributed mode).")
        except Exception as _e:  # noqa: BLE001
            _logger.warning(f"Brute-force limiter Redis init failed ({_e}); using in-memory store.")
            _redis_available = False
            _redis_client = None
except ImportError:
    _logger.info("redis package not installed; brute-force limiter uses in-memory store (single-worker).")


# ---------------------------------------------------------------------------
# Trusted proxy allowlist — IMP-008: XFF spoofing protection
# ---------------------------------------------------------------------------

def _load_trusted_proxies() -> list:
    """Load trusted proxy CIDR ranges from TRUSTED_PROXIES env var."""
    raw = os.getenv("TRUSTED_PROXIES", "127.0.0.1")
    networks = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        with contextlib.suppress(ValueError):
            networks.append(ipaddress.ip_network(entry, strict=False))
    return networks


def _is_trusted_proxy(ip_str: str) -> bool:
    """Return True if ip_str falls within any trusted proxy network."""
    if _IS_TESTING and (ip_str in ("testclient", "testserver", "127.0.0.1")):
        return True
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in _load_trusted_proxies())
    except ValueError:
        return False


def _get_client_ip(request: Request | None) -> str:
    """Extract the real client IP, only trusting X-Forwarded-For from verified proxies.

    IMP-008: Validates the connecting IP against TRUSTED_PROXIES before
    honouring X-Forwarded-For, preventing header-spoofing rate-limit bypass.
    """
    if request is None:
        return "unknown"
    connecting_ip = request.client.host if request.client else None
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for and connecting_ip and _is_trusted_proxy(connecting_ip):
        # Only take the first (leftmost = real client) IP
        return forwarded_for.split(",")[0].strip()
    if connecting_ip:
        return connecting_ip
    return "unknown"


def _lazy_prune_ip_locked(ip: str, now: float) -> None:
    """Prune failures and update lockout state for a single IP.
    Must be called under _rate_lock.
    """
    if ip not in _rate_state:
        return
    state = _rate_state[ip]
    state["failures"] = [t for t in state["failures"] if now - t < _FAIL_WINDOW_SECONDS]

    locked_until = state.get("locked_until")
    if locked_until is not None:
        if locked_until - now <= 0:
            state["locked_until"] = None
            state["failures"] = []

    if not state["failures"] and state.get("locked_until") is None:
        _rate_state.pop(ip, None)


def _run_global_cleanup_if_needed(now: float) -> None:
    """Perform throttled global cleanup on the dictionary.
    Must be called under _rate_lock.
    """
    global _last_prune_time
    if len(_rate_state) > 1000 and (now - _last_prune_time) > 60.0:
        for key in list(_rate_state.keys()):
            _lazy_prune_ip_locked(key, now)
        _last_prune_time = now


def _record_failure(ip: str) -> None:
    """Record a JWT verification failure for an IP address (distributed-aware)."""
    if _redis_available and _redis_client is not None:
        try:
            key = f"bf_fail:{ip}"
            now = time.time()
            pipe = _redis_client.pipeline()
            pipe.zadd(key, {f"{now}:{random.random()}": now})
            pipe.zremrangebyscore(key, "-inf", now - _FAIL_WINDOW_SECONDS)
            pipe.expire(key, _LOCKOUT_SECONDS + _FAIL_WINDOW_SECONDS)
            pipe.zcard(key)
            _, _, _, count = pipe.execute()
            if count >= _MAX_FAILURES:
                _redis_client.set(f"bf_lock:{ip}", "1", ex=_LOCKOUT_SECONDS)
                _logger.warning(f"[BruteForce] IP {ip} locked out for {_LOCKOUT_SECONDS}s after {count} failures.")
            return
        except Exception as _e:  # noqa: BLE001
            _logger.warning(f"Redis failure recording failed ({_e}); falling back to in-memory.")
    # In-memory fallback (single-worker)
    now = time.monotonic()
    with _rate_lock:
        _lazy_prune_ip_locked(ip, now)

        state = _rate_state[ip]
        state["failures"].append(now)
        if len(state["failures"]) >= _MAX_FAILURES:
            state["locked_until"] = now + _LOCKOUT_SECONDS
            _logger.warning(f"[BruteForce] IP {ip} locked out for {_LOCKOUT_SECONDS}s after "
                            f"{len(state['failures'])} failures.")

        _run_global_cleanup_if_needed(now)


def _check_lockout(ip: str) -> float:
    """
    Check if an IP is currently locked out (distributed-aware).
    Returns the remaining lockout seconds (>0) if locked, else 0.
    """
    if _redis_available and _redis_client is not None:
        try:
            ttl = _redis_client.ttl(f"bf_lock:{ip}")
            if ttl is not None and ttl > 0:
                return float(ttl)
            return 0.0
        except Exception as _e:  # noqa: BLE001
            _logger.warning(f"Redis lockout check failed ({_e}); falling back to in-memory.")
    now = time.monotonic()
    with _rate_lock:
        _lazy_prune_ip_locked(ip, now)
        _run_global_cleanup_if_needed(now)
        state = _rate_state.get(ip)
        if state is not None:
            locked_until = state.get("locked_until")
            if locked_until is not None:
                remaining = locked_until - now
                return max(0.0, remaining)
        return 0.0


def _record_success(ip: str) -> None:
    """Clear failure history for an IP on successful authentication (distributed-aware)."""
    if _redis_available and _redis_client is not None:
        try:
            _redis_client.delete(f"bf_fail:{ip}", f"bf_lock:{ip}")
            return
        except Exception as _e:  # noqa: BLE001
            _logger.warning(f"Redis success recording failed ({_e}); falling back to in-memory.")
    now = time.monotonic()
    with _rate_lock:
        if ip in _rate_state:
            _rate_state[ip]["failures"] = []
            _rate_state[ip]["locked_until"] = None
        _lazy_prune_ip_locked(ip, now)
        _run_global_cleanup_if_needed(now)


# ---------------------------------------------------------------------------
# Token generation
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_in: int = 3600) -> str:
    """
    Generates a JWT access token for testing and user identification.
    """
    payload = data.copy()
    payload.update({
        "exp": time.time() + expires_in,
        "iss": "jobhunt-pro"
    })
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    """
    Decodes a JWT token by trying all available secret keys in JWT_SECRET_KEYS.
    If a signature is valid but expired, raises ExpiredSignatureError immediately.
    Raises InvalidTokenError if no key can successfully decode the token.
    """
    last_err = None
    for key in JWT_SECRET_KEYS:
        try:
            return jwt.decode(token, key, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError as e:
            raise e
        except jwt.InvalidSignatureError as e:
            last_err = e
            continue
        except jwt.InvalidTokenError as e:
            raise e
    if last_err:
        raise last_err
    raise jwt.InvalidTokenError("Invalid token")


# ---------------------------------------------------------------------------
# Token verification with brute-force protection
# ---------------------------------------------------------------------------

async def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Security(security),
    request: Request = None,
) -> dict:
    """
    FastAPI dependency to validate Bearer tokens.
    Enforces IP-based brute-force protection in production.
    In test mode (_IS_TESTING=True) rate limiting is skipped to avoid
    cross-test IP lockouts; the limiter logic is tested separately.
    Raises HTTPException(429) if the IP is locked out (production only).
    Raises HTTPException(401) on invalid token.
    """
    ip = _get_client_ip(request)

    if not _IS_TESTING:
        # Check lockout BEFORE even trying to decode the token
        remaining = _check_lockout(ip)
        if remaining > 0:
            raise HTTPException(
                status_code=429,
                detail="Too many failed authentication attempts. Please try again later.",
                headers={"Retry-After": str(int(remaining) + 1)},
            )

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing or invalid scheme"
        )

    token = credentials.credentials
    try:
        payload = decode_jwt_token(token)

        # Backwards compatibility: log warning if issuer is missing/invalid, but accept
        iss = payload.get("iss")
        if iss != "jobhunt-pro":
            _logger.warning(f"JWT issuer mismatch or missing: {iss}")

        # Successful auth — clear failure history
        if not _IS_TESTING:
            _record_success(ip)
        return payload
    except jwt.ExpiredSignatureError:
        if not _IS_TESTING:
            _record_failure(ip)
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        if not _IS_TESTING:
            _record_failure(ip)
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


# ---------------------------------------------------------------------------
# Admin authorization
# ---------------------------------------------------------------------------

def _load_admin_allowlist() -> set[str]:
    """Load the set of authorized admin identifiers from environment.

    Supports either ADMIN_EMAILS or ADMIN_USER_IDS (comma-separated).
    Matching is case-insensitive.
    """
    raw = os.environ.get("ADMIN_EMAILS", "") or os.environ.get("ADMIN_USER_IDS", "")
    return {x.strip().lower() for x in raw.split(",") if x.strip()}


async def require_admin(payload: dict = Depends(verify_jwt)) -> dict:
    """FastAPI dependency enforcing admin privileges — IMP-SEC-ADMIN.

    The User model has no ``role`` column, so admin status is determined by an
    explicit allowlist (ADMIN_EMAILS / ADMIN_USER_IDS) checked against the JWT
    claims. Fails closed: if no allowlist is configured (and we are not in an
    explicit test run) all admin access is denied.
    """
    allowlist = _load_admin_allowlist()
    if not allowlist:
        if not _IS_TESTING:
            raise HTTPException(
                status_code=403,
                detail="Admin access is not configured on this server.",
            )
    else:
        email = (payload.get("email") or "").strip().lower()
        user_id = (payload.get("user_id") or payload.get("sub") or "").strip().lower()
        if email not in allowlist and user_id not in allowlist:
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required.",
            )
    return payload
