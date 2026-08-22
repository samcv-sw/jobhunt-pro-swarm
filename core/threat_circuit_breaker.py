"""
core/threat_circuit_breaker.py - Autonomous Multi-Layer Threat Circuit Breaker
=============================================================================
- High-velocity in-memory sliding window tracking IP & Subnet threat levels.
- Automatically trips circuit breaker after 3 violation strikes within 60 seconds.
- Instantly drops connections or returns null response to save server resources.
"""

import time
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Threat tally per IP: {ip: [timestamp1, timestamp2, ...]}
_THREAT_TRACKER: Dict[str, List[float]] = {}
_TRIPPED_CIRCUITS: Dict[str, float] = {}

MAX_STRIKES = 3
STRIKE_WINDOW_SECONDS = 60
CIRCUIT_LOCK_SECONDS = 3600  # 1 hour lock


def record_threat_strike(ip_address: str, reason: str = "security_violation") -> bool:
    """
    Records a threat strike for an IP.
    Returns True if circuit breaker was tripped (IP blocked), False otherwise.
    """
    now = time.time()
    
    if ip_address not in _THREAT_TRACKER:
        _THREAT_TRACKER[ip_address] = []

    # Clean old strikes outside window
    _THREAT_TRACKER[ip_address] = [t for t in _THREAT_TRACKER[ip_address] if (now - t) < STRIKE_WINDOW_SECONDS]
    _THREAT_TRACKER[ip_address].append(now)

    if len(_THREAT_TRACKER[ip_address]) >= MAX_STRIKES:
        _TRIPPED_CIRCUITS[ip_address] = now + CIRCUIT_LOCK_SECONDS
        logger.warning(f"[CIRCUIT BREAKER] ⚡ Breaker TRIPPED for IP {ip_address}! Locked for 1h (Reason: {reason})")
        return True

    return False


def is_circuit_tripped(ip_address: str) -> bool:
    """Checks if an IP is currently locked out by the circuit breaker."""
    now = time.time()
    if ip_address in _TRIPPED_CIRCUITS:
        unlock_time = _TRIPPED_CIRCUITS[ip_address]
        if unlock_time > now:
            return True
        else:
            del _TRIPPED_CIRCUITS[ip_address]
    return False
