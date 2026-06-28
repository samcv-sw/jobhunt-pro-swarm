"""
JobHunt Pro - Aegis Shield (L7 Anti-DDoS WAF)
Provides military-grade protection against botnets, DDoS floods, and hackers.
Uses zero-CPU blackholing and global load shedding to prevent server crashes.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
import time
import logging

logger = logging.getLogger(__name__)

# --- IN-MEMORY STATE (Hyper-fast, survives within the worker process) ---
# Format: {ip: [timestamp1, timestamp2, ...]}
_ip_hits = {}
# Format: {ip: unblock_timestamp}
_blackhole = {}

# --- AEGIS CONFIGURATION ---
MAX_HITS_PER_SECOND = 50       # If an IP hits 50x in 1 second, it's a bot.
BLACKHOLE_DURATION = 3600      # Block the IP entirely for 1 hour.
MAX_GLOBAL_CONCURRENCY = 1000  # Load Shedding limit

_current_concurrency = 0

class AegisShieldMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        global _current_concurrency
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # 1. 🕳️ IP BLACKHOLE CHECK (Absolute Zero CPU drop)
        if client_ip in _blackhole:
            if now < _blackhole[client_ip]:
                # In standard ASGI we can't do a raw TCP 444 easily, so we return a tiny 429
                return PlainTextResponse("Blackholed.", status_code=429)
            else:
                del _blackhole[client_ip] # Sentence served
                if client_ip in _ip_hits:
                    del _ip_hits[client_ip]

        # 2. 🌊 RAPID-FIRE DDOS DETECTION (Per IP)
        if client_ip not in _ip_hits:
            _ip_hits[client_ip] = []
        
        # Keep only hits from the last 1 second
        _ip_hits[client_ip] = [t for t in _ip_hits[client_ip] if now - t < 1.0]
        _ip_hits[client_ip].append(now)

        if len(_ip_hits[client_ip]) > MAX_HITS_PER_SECOND:
            logger.critical(f"🛡️ [AEGIS SHIELD] Massive DDoS burst detected from {client_ip}. BLACKHOLING IP.")
            _blackhole[client_ip] = now + BLACKHOLE_DURATION
            return PlainTextResponse("Blackholed.", status_code=429)

        # 3. ⚖️ GLOBAL LOAD SHEDDING (Anti-Crash)
        if _current_concurrency > MAX_GLOBAL_CONCURRENCY:
            # If we have 1000 active connections, we are drowning.
            # Allow logged in users (via cookies), but shed raw anonymous traffic.
            if "session" not in request.cookies:
                logger.warning(f"🛡️ [AEGIS SHIELD] Load Shedding Active. Dropping anonymous request from {client_ip}")
                return PlainTextResponse("Server is under heavy load. Please try again in a few minutes.", status_code=503)

        # 4. 📦 PAYLOAD SIZE DEFENSE
        # Prevent hackers from uploading 5GB files to crash the disk.
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > 10 * 1024 * 1024:  # 10 MB absolute max for normal routes
                    logger.warning(f"🛡️ [AEGIS SHIELD] Payload too large from {client_ip}.")
                    return PlainTextResponse("Payload too large.", status_code=413)
            except (ValueError, TypeError):
                # Malformed Content-Length header — attacker probe, reject it
                logger.warning(f"🛡️ [AEGIS SHIELD] Malformed Content-Length from {client_ip}: '{content_length}'")
                return PlainTextResponse("Bad Request.", status_code=400)

        # --- PROCESS REQUEST ---
        _current_concurrency += 1
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"🛡️ [AEGIS SHIELD] Unhandled middleware error from {client_ip}: {e}")
            return PlainTextResponse("Internal Server Error.", status_code=500)
        finally:
            _current_concurrency -= 1
