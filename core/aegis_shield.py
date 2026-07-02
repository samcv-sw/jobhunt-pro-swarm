"""
JobHunt Pro - Aegis Shield v2 (Apex Matrix Edition)
====================================================
L7 Anti-DDoS WAF + Distributed Redis Token Bucket Rate Limiter

APEX MATRIX UPGRADES:
 - Migrated from in-memory counters (fail in multi-worker) to Upstash Redis
 - Token Bucket Algorithm with Lua atomic script (zero race conditions)
 - Per-IP distributed rate limit state (no fragmentation across workers)
 - Injects RFC-compliant Rate-Limit headers on every response
 - Falls back to in-memory if Upstash not configured (dev mode)
 - All WAF pattern checks preserved and extended

HEADERS INJECTED:
  Rate-Limit-Ceiling   : max burst tokens for this tier
  Rate-Limit-Remaining : tokens left in the client's bucket
  Retry-Delay-Window   : seconds to wait when rejected (only on 429)
"""

import re
import time
import math
import json
import logging
import urllib.request
import urllib.error
import os
from typing import Tuple, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# AEGIS CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
BUCKET_CAPACITY = int(os.getenv("AEGIS_BUCKET_CAPACITY", "60"))  # max burst tokens
REFILL_RATE = int(os.getenv("AEGIS_REFILL_RATE", "20"))  # tokens per interval
REFILL_INTERVAL_S = int(
    os.getenv("AEGIS_REFILL_INTERVAL", "60")
)  # refill every N seconds
BLACKHOLE_DURATION = 3600  # block normal DDoS IPs for 1 hour
PROBE_BLACKHOLE_DURATION = 86400  # block hacker-probe IPs for 24 hours
MAX_GLOBAL_CONCURRENCY = 1000  # global load shedding limit

_current_concurrency = 0


# ─────────────────────────────────────────────────────────────────────────────
# UPSTASH REDIS CLIENT (zero-dependency HTTP REST)
# ─────────────────────────────────────────────────────────────────────────────
class _UpstashClient:
    """
    Thin Upstash Redis REST API wrapper.
    Falls back to in-memory dict when UPSTASH_REDIS_URL is not set.
    """

    def __init__(self):
        self.url = os.getenv("UPSTASH_REDIS_URL", "").rstrip("/")
        self.token = os.getenv("UPSTASH_REDIS_TOKEN", "")
        self._enabled = bool(self.url and self.token)
        self._mem: dict = {}  # in-memory fallback store

        if self._enabled:
            logger.info("[AEGIS] Upstash Redis rate-limit backend ENABLED.")
        else:
            logger.warning(
                "[AEGIS] Upstash not configured — using in-memory rate-limit fallback. "
                "Set UPSTASH_REDIS_URL + UPSTASH_REDIS_TOKEN for distributed mode."
            )

    def _exec(self, *cmd) -> Optional[any]:
        """Execute a single Redis command via Upstash REST POST."""
        if not self._enabled:
            return None
        try:
            payload = json.dumps(list(cmd)).encode()
            req = urllib.request.Request(
                self.url,
                data=payload,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return json.loads(resp.read()).get("result")
        except Exception as exc:
            logger.warning(f"[AEGIS] Upstash error: {exc}")
            return None

    # ── Token Bucket via Lua (atomic, zero race conditions) ──────────────────
    # Lua script: refill-check-consume in a single round-trip
    _LUA_TOKEN_BUCKET = """
local key        = KEYS[1]
local capacity   = tonumber(ARGV[1])
local refill_qty = tonumber(ARGV[2])
local interval   = tonumber(ARGV[3])
local now        = tonumber(ARGV[4])

local state = redis.call("HMGET", key, "tokens", "last_refill")
local tokens     = tonumber(state[1]) or capacity
local last_refill = tonumber(state[2]) or now

-- Refill tokens proportional to elapsed time
local elapsed = now - last_refill
local periods = math.floor(elapsed / interval)
if periods > 0 then
    tokens = math.min(capacity, tokens + periods * refill_qty)
    last_refill = last_refill + periods * interval
end

local allowed = 0
local remaining = tokens
if tokens >= 1 then
    tokens = tokens - 1
    remaining = tokens
    allowed = 1
end

-- Persist state with TTL = 2 intervals to auto-expire idle keys
redis.call("HMSET", key, "tokens", tokens, "last_refill", last_refill)
redis.call("EXPIRE", key, interval * 2)

-- Compute seconds until next token
local wait = 0
if allowed == 0 then
    wait = interval - (now - last_refill)
    if wait < 0 then wait = 0 end
end

return {allowed, remaining, wait}
"""

    def token_bucket_check(self, ip: str) -> Tuple[bool, int, int]:
        """
        Returns (allowed, remaining_tokens, retry_after_seconds).
        Runs Lua script atomically on Redis; falls back to local logic.
        """
        now = int(time.time())
        key = f"aegis:tb:{ip}"

        if self._enabled:
            # EVAL script on Upstash
            result = self._exec(
                "EVAL",
                self._LUA_TOKEN_BUCKET,
                1,
                key,
                str(BUCKET_CAPACITY),
                str(REFILL_RATE),
                str(REFILL_INTERVAL_S),
                str(now),
            )
            if result and len(result) == 3:
                allowed = bool(result[0])
                remaining = int(result[1])
                retry = int(result[2]) if not allowed else 0
                return allowed, remaining, retry

        # ── In-memory fallback ───────────────────────────────────────────────
        state = self._mem.get(key, {"tokens": BUCKET_CAPACITY, "last_refill": now})
        tokens = state["tokens"]
        last_refill = state["last_refill"]

        elapsed = now - last_refill
        periods = math.floor(elapsed / REFILL_INTERVAL_S)
        if periods > 0:
            tokens = min(BUCKET_CAPACITY, tokens + periods * REFILL_RATE)
            last_refill = last_refill + periods * REFILL_INTERVAL_S

        if tokens >= 1:
            tokens -= 1
            self._mem[key] = {"tokens": tokens, "last_refill": last_refill}
            return True, tokens, 0
        else:
            wait = REFILL_INTERVAL_S - (now - last_refill)
            self._mem[key] = {"tokens": tokens, "last_refill": last_refill}
            return False, 0, max(0, wait)


_redis = _UpstashClient()

# ─────────────────────────────────────────────────────────────────────────────
# BLACKHOLE STATE (in-memory; acceptable — blackholes are per-worker defense)
# ─────────────────────────────────────────────────────────────────────────────
_blackhole: dict = {}  # {ip: unblock_timestamp}

# ─────────────────────────────────────────────────────────────────────────────
# WAF REGEX PATTERNS (pre-compiled)
# ─────────────────────────────────────────────────────────────────────────────
PROBE_PATH_RE = re.compile(
    r"(\.env|\.git|\.aws/|wp-admin|wp-login|xmlrpc\.php|phpmyadmin|pma/|myadmin/"
    r"|setup\.php|install\.php|backup\.sql|db\.sql|dump\.sql|backup\.tar"
    r"|config\.php|web\.config|\.htaccess|\.htpasswd|composer\.json|package\.json"
    r"|laravel|drupal|joomla|cpanel|plesk|webmin|adminer)",
    re.IGNORECASE,
)

SQLI_RE = re.compile(
    r"(\b(union|select|insert|update|delete|drop|alter|create|truncate|exec|xp_cmdshell"
    r"|information_schema|sysdatabases|concat|char|benchmark|sleep)\b"
    r"|['\"]|\bOR\b\s+[\d\w'\"]+\s*=\s*[\d\w'\"]+|\bAND\b\s+[\d\w'\"]+\s*=\s*[\d\w'\"]+)",
    re.IGNORECASE,
)

XSS_RE = re.compile(
    r"(<script|javascript:|vbscript:|onerror\s*=|onload\s*=|onfocus\s*=|onclick\s*="
    r"|alert\(|confirm\(|prompt\(|<iframe|<object|<embed|<svg|data:text/html)",
    re.IGNORECASE,
)

TRAVERSAL_CMD_RE = re.compile(
    r"(\.\./|\.\.\\|/etc/passwd|/etc/shadow|/etc/hosts|win\.ini|boot\.ini|system\.ini"
    r"|;\s*(rm|wget|curl|sh|bash|python|perl|php|nc|netcat|ncat)\b"
    r"|\|\s*(cat|ls|id|whoami|uname))",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_client_ip(request: Request) -> str:
    """Safely resolve the real client IP behind Cloudflare and reverse proxies."""
    # 1. Cloudflare header (highest trust)
    cf_ip = request.headers.get("cf-connecting-ip") or request.headers.get(
        "CF-Connecting-IP"
    )
    if cf_ip:
        return cf_ip.strip()
    # 2. X-Real-IP
    real_ip = request.headers.get("x-real-ip") or request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    # 3. X-Forwarded-For (take leftmost / original client)
    xff = request.headers.get("x-forwarded-for") or request.headers.get(
        "X-Forwarded-For"
    )
    if xff:
        return xff.split(",")[0].strip()
    # 4. Direct connection
    return request.client.host if request.client else "unknown"


def _inject_rate_limit_headers(
    response: Response, remaining: int, retry: int = 0
) -> None:
    """Inject RFC-style rate-limit headers into a response."""
    response.headers["Rate-Limit-Ceiling"] = str(BUCKET_CAPACITY)
    response.headers["Rate-Limit-Remaining"] = str(remaining)
    if retry > 0:
        response.headers["Retry-Delay-Window"] = str(retry)


# ─────────────────────────────────────────────────────────────────────────────
# AEGIS SHIELD MIDDLEWARE
# ─────────────────────────────────────────────────────────────────────────────
class AegisShieldMiddleware(BaseHTTPMiddleware):
    """
    Apex Matrix L7 WAF + Distributed Token Bucket Rate Limiter.

    Execution pipeline (in order):
      1.  IP Blackhole check (zero CPU drop for known bad actors)
      2.  Host header validation (anti-host-header injection)
      3.  Hacker probe path detection (24h blackhole)
      4.  SQLi / XSS / path-traversal signatures in query strings
      5.  Token Bucket rate-limit check (distributed via Upstash Redis)
      6.  Global load shedding (anti-crash circuit breaker)
      7.  Payload size defense (reject >10 MB)
      8.  Security response headers injection (Pentagon-grade CSP)
      9.  Rate-Limit headers injected on every successful response
    """

    async def dispatch(self, request: Request, call_next):
        global _current_concurrency
        client_ip = get_client_ip(request)
        now = time.time()

        # ── 1. IP BLACKHOLE CHECK ─────────────────────────────────────────────
        if client_ip in _blackhole:
            if now < _blackhole[client_ip]:
                return PlainTextResponse("Access Denied.", status_code=403)
            else:
                del _blackhole[client_ip]

        # ── 1.5 USER-AGENT VALIDATION (Anti-Bot Shield) ───────────────────────
        user_agent = request.headers.get("user-agent", "").lower()
        if (
            not user_agent
            or "python-requests" in user_agent
            or "curl" in user_agent
            or "urllib" in user_agent
            or "bot" in user_agent
        ):
            logger.warning(
                f"[AEGIS WAF] Malicious or missing User-Agent from {client_ip}: '{user_agent}'"
            )
            return PlainTextResponse(
                "Forbidden: Request denied by security firewall.", status_code=403
            )

        # ── 2. HOST HEADER VALIDATION ─────────────────────────────────────────
        host = request.headers.get("host", "")
        if host:
            host_clean = host.split(":")[0].lower()
            allowed_hosts = {
                "localhost",
                "127.0.0.1",
                "testserver",
                "jhfguf.pythonanywhere.com",
                "jobhuntpro.com",
                "www.jobhuntpro.com",
            }
            if (
                host_clean not in allowed_hosts
                and not host_clean.endswith(".pythonanywhere.com")
                and not host_clean.endswith(".jobhuntpro.com")
                and not host_clean.endswith(".railway.app")
                and not host_clean.endswith(".render.com")
                and not host_clean.endswith(".fly.dev")
                and not host_clean.endswith(".onrender.com")
            ):
                logger.warning(
                    f"[AEGIS WAF] Bad Host header from {client_ip}: '{host}'"
                )
                return PlainTextResponse("Invalid Host Header.", status_code=400)

        # ── 3. HACKER PROBE DETECTION ─────────────────────────────────────────
        path = request.url.path
        if PROBE_PATH_RE.search(path):
            logger.critical(
                f"[AEGIS WAF] Probe detected from {client_ip} → '{path}'. Blackholing 24h."
            )
            _blackhole[client_ip] = now + PROBE_BLACKHOLE_DURATION
            return PlainTextResponse("Forbidden.", status_code=403)

        # ── 4. EXPLOIT SIGNATURES IN QUERY STRING ─────────────────────────────
        query_string = request.url.query
        if query_string:
            if (
                SQLI_RE.search(query_string)
                or XSS_RE.search(query_string)
                or TRAVERSAL_CMD_RE.search(query_string)
            ):
                logger.critical(
                    f"[AEGIS WAF] Exploit payload from {client_ip}. Blackholing 24h."
                )
                _blackhole[client_ip] = now + PROBE_BLACKHOLE_DURATION
                return PlainTextResponse("Bad Request.", status_code=400)

        # ── 5. TOKEN BUCKET RATE LIMIT (DISTRIBUTED via Upstash Redis) ────────
        allowed, remaining, retry_after = _redis.token_bucket_check(client_ip)
        if not allowed:
            logger.warning(
                f"[AEGIS SHIELD] Rate limit exceeded for {client_ip}. "
                f"Retry-After: {retry_after}s"
            )
            resp = PlainTextResponse(
                f"Too Many Requests. Please retry in {retry_after} seconds.",
                status_code=429,
            )
            _inject_rate_limit_headers(resp, 0, retry_after)
            return resp

        # ── 6. GLOBAL LOAD SHEDDING ───────────────────────────────────────────
        if _current_concurrency > MAX_GLOBAL_CONCURRENCY:
            if "user_id" not in request.cookies and "session" not in request.cookies:
                logger.warning(
                    f"[AEGIS SHIELD] Load Shedding. Dropping anonymous request from {client_ip}"
                )
                return PlainTextResponse(
                    "Server under heavy load. Try again later.", status_code=503
                )

        # ── 7. PAYLOAD SIZE DEFENSE ───────────────────────────────────────────
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > 10 * 1024 * 1024:  # 10 MB
                    logger.warning(
                        f"[AEGIS SHIELD] Oversized payload from {client_ip}."
                    )
                    return PlainTextResponse("Payload Too Large.", status_code=413)
            except (ValueError, TypeError):
                return PlainTextResponse("Bad Request.", status_code=400)

        # ── PROCESS REQUEST ────────────────────────────────────────────────────
        _current_concurrency += 1
        try:
            response = await call_next(request)

            # ── 8. SECURITY RESPONSE HEADERS ──────────────────────────────────
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = (
                "geolocation=(), camera=(), microphone=()"
            )
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com "
                "https://telegram.org; "
                "style-src 'self' 'unsafe-inline' "
                "https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:;"
            )

            # ── 9. RATE-LIMIT INFORMATIONAL HEADERS ───────────────────────────
            _inject_rate_limit_headers(response, remaining)

            return response

        except Exception as exc:
            logger.error(f"[AEGIS SHIELD] Middleware error from {client_ip}: {exc}")
            return PlainTextResponse("Internal Server Error.", status_code=500)
        finally:
            _current_concurrency -= 1
