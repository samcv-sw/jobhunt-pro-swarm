"""
Sovereign Security Shield Router
JobHunt Pro SaaS - REST endpoints for rate-limiting status and security telemetry.
"""
from fastapi import APIRouter, Request

from core.sovereign_security_shield import security_shield

router = APIRouter(prefix="/api/v2/security", tags=["Sovereign Security Shield"])


@router.get("/status")
def get_security_status(request: Request):
    """Returns real-time anti-DDoS, brute-force lockout, and rate limiting health."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    is_limited = security_shield.is_rate_limited(client_ip, max_requests_per_minute=180)
    shield_health = security_shield.get_security_health()
    shield_health["client_ip"] = client_ip
    shield_health["client_rate_limited"] = is_limited
    return shield_health
