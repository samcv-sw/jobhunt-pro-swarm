"""
JobHunt Pro - Aegis Shield (L7 Anti-DDoS WAF & Security Hardener)
Provides military-grade protection against botnets, DDoS floods, hacker probes,
SQL Injection, Cross-Site Scripting, and Path Traversal.
Uses zero-CPU blackholing and global load shedding to prevent server crashes.
"""
import re
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse

logger = logging.getLogger(__name__)

# --- IN-MEMORY STATE (Hyper-fast, survives within the worker process) ---
# Format: {ip: [timestamp1, timestamp2, ...]}
_ip_hits = {}
# Format: {ip: unblock_timestamp}
_blackhole = {}

# --- AEGIS CONFIGURATION ---
MAX_HITS_PER_SECOND = 50       # If an IP hits 50x in 1 second, it's a bot.
BLACKHOLE_DURATION = 3600      # Block normal DDoS IPs for 1 hour.
PROBE_BLACKHOLE_DURATION = 86400  # Block malicious hacker probe IPs for 24 hours.
MAX_GLOBAL_CONCURRENCY = 1000  # Load Shedding limit

_current_concurrency = 0

# --- WAF REGEX PATTERNS (Pre-compiled for maximum performance) ---
# 1. Common hacker scan paths (WordPress, Git, env leaks, DB managers, backups)
PROBE_PATH_RE = re.compile(
    r"(\.env|\.git|\.aws/|wp-admin|wp-login|xmlrpc\.php|phpmyadmin|pma/|myadmin/|setup\.php|install\.php|backup\.sql|db\.sql|dump\.sql|backup\.tar|config\.php|web\.config)",
    re.IGNORECASE
)

# 2. SQL Injection signatures
SQLI_RE = re.compile(
    r"(\b(union|select|insert|update|delete|drop|alter|create|truncate|src|concat|char|sysdatabases)\b|['\"#]|\b(or|and)\b\s+[\d\w]+\s*=\s*[\d\w]+)",
    re.IGNORECASE
)

# 3. Cross-Site Scripting (XSS) signatures
XSS_RE = re.compile(
    r"(<script|javascript:|onerror\s*=|onload\s*=|alert\(|confirm\(|prompt\(|<iframe|<object|<embed)",
    re.IGNORECASE
)

# 4. Path Traversal & Command Injection signatures
TRAVERSAL_CMD_RE = re.compile(
    r"(\.\./|\.\.\\|/etc/passwd|/etc/shadow|/etc/hosts|win\.ini|boot\.ini|system\.ini|;\s*(rm|wget|curl|sh|bash|python|perl|php|nc|netcat)\b)",
    re.IGNORECASE
)


def get_client_ip(request: Request) -> str:
    """Safely resolve the real client IP behind Cloudflare and reverse proxies."""
    # 1. Cloudflare header
    cf_ip = request.headers.get("cf-connecting-ip") or request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    # 2. X-Real-IP
    real_ip = request.headers.get("x-real-ip") or request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    # 3. X-Forwarded-For
    xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    # 4. Fallback
    return request.client.host if request.client else "unknown"


class AegisShieldMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        global _current_concurrency
        client_ip = get_client_ip(request)
        now = time.time()

        # 1. 🕳️ IP BLACKHOLE CHECK (Absolute Zero CPU drop)
        if client_ip in _blackhole:
            if now < _blackhole[client_ip]:
                return PlainTextResponse("Access Denied (Blackholed).", status_code=403)
            else:
                del _blackhole[client_ip]  # Sentence served
                if client_ip in _ip_hits:
                    del _ip_hits[client_ip]

        # 2. 🛡️ WAF: HOST HEADER VALIDATION (Anti-Host Header Injection / BadHost CVE-2026-48710)
        host = request.headers.get("host", "")
        if host:
            host_clean = host.split(":")[0].lower()
            if host_clean not in {"localhost", "127.0.0.1", "testserver", "jhfguf.pythonanywhere.com"} and not host_clean.endswith(".pythonanywhere.com"):
                logger.critical(f"🛡️ [AEGIS WAF] Invalid Host header from {client_ip}: '{host}'. Blocking.")
                return PlainTextResponse("Invalid Host Header.", status_code=400)

        # 3. 🛡️ WAF: HACKER PROBE DETECTION (Immediate 24-hour block)
        path = request.url.path
        if PROBE_PATH_RE.search(path):
            logger.critical(f"🛡️ [AEGIS WAF] Malicious path probe detected from {client_ip} trying to access '{path}'. Blackholing for 24h.")
            _blackhole[client_ip] = now + PROBE_BLACKHOLE_DURATION
            return PlainTextResponse("Forbidden.", status_code=403)

        # 4. 🛡️ WAF: EXPLOIT SCANNING (Query Params & URL)
        query_string = request.url.query
        if query_string:
            if SQLI_RE.search(query_string) or XSS_RE.search(query_string) or TRAVERSAL_CMD_RE.search(query_string):
                logger.critical(f"🛡️ [AEGIS WAF] Malicious exploit payload detected in query string from {client_ip}. Blackholing for 24h.")
                _blackhole[client_ip] = now + PROBE_BLACKHOLE_DURATION
                return PlainTextResponse("Bad Request.", status_code=400)

        # 5. 🌊 RAPID-FIRE DDOS DETECTION (Per IP)
        if client_ip not in _ip_hits:
            _ip_hits[client_ip] = []
        
        # Keep only hits from the last 1 second
        _ip_hits[client_ip] = [t for t in _ip_hits[client_ip] if now - t < 1.0]
        _ip_hits[client_ip].append(now)

        if len(_ip_hits[client_ip]) > MAX_HITS_PER_SECOND:
            logger.critical(f"🛡️ [AEGIS SHIELD] Massive DDoS burst detected from {client_ip}. Blackholing IP.")
            _blackhole[client_ip] = now + BLACKHOLE_DURATION
            return PlainTextResponse("Too Many Requests (Blackholed).", status_code=429)

        # 6. ⚖️ GLOBAL LOAD SHEDDING (Anti-Crash)
        if _current_concurrency > MAX_GLOBAL_CONCURRENCY:
            # Allow logged in users (via cookies), but shed raw anonymous traffic.
            if "user_id" not in request.cookies and "session" not in request.cookies:
                logger.warning(f"🛡️ [AEGIS SHIELD] Load Shedding Active. Dropping anonymous request from {client_ip}")
                return PlainTextResponse("Server is under heavy load. Please try again in a few minutes.", status_code=503)

        # 7. 📦 PAYLOAD SIZE DEFENSE
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > 10 * 1024 * 1024:  # 10 MB absolute max for normal routes
                    logger.warning(f"🛡️ [AEGIS SHIELD] Payload too large from {client_ip}.")
                    return PlainTextResponse("Payload too large.", status_code=413)
            except (ValueError, TypeError):
                logger.warning(f"🛡️ [AEGIS SHIELD] Malformed Content-Length from {client_ip}: '{content_length}'")
                return PlainTextResponse("Bad Request.", status_code=400)

        # --- PROCESS REQUEST ---
        _current_concurrency += 1
        try:
            response = await call_next(request)
            
            # 8. 🛡️ SECURITY HEADERS INJECTION (Pentagon-grade)
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
            
            return response
        except Exception as e:
            logger.error(f"🛡️ [AEGIS SHIELD] Unhandled middleware error from {client_ip}: {e}")
            return PlainTextResponse("Internal Server Error.", status_code=500)
        finally:
            _current_concurrency -= 1
