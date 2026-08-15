"""
Sovereign Security Shield & Anti-DDoS Rate Limiter
JobHunt Pro SaaS - Sliding-window rate limiting, brute-force lockout, and webhook signature verification.
"""
import time
import hmac
import hashlib
from typing import Dict, List, Any, Optional
from collections import defaultdict


class SovereignSecurityShield:
    """
    Protects API routes from DDoS, brute-force credential stuffing,
    and unverified webhook injection.
    """

    def __init__(self):
        self._ip_request_timestamps = defaultdict(list)
        self._failed_login_attempts = defaultdict(list)
        self._blocked_ips = {}

    def is_rate_limited(self, client_ip: str, max_requests_per_minute: int = 120) -> bool:
        """Sliding-window rate limiter per IP address."""
        now = time.time()

        # Check if temporarily banned
        if client_ip in self._blocked_ips:
            if now < self._blocked_ips[client_ip]:
                return True
            else:
                del self._blocked_ips[client_ip]

        # Clean timestamps older than 60 seconds
        timestamps = self._ip_request_timestamps[client_ip]
        self._ip_request_timestamps[client_ip] = [t for t in timestamps if now - t < 60.0]

        if len(self._ip_request_timestamps[client_ip]) >= max_requests_per_minute:
            # Auto-ban for 5 minutes if heavily exceeding
            self._blocked_ips[client_ip] = now + 300.0
            return True

        self._ip_request_timestamps[client_ip].append(now)
        return False

    def record_login_attempt(self, client_ip: str, success: bool) -> Dict[str, Any]:
        """Tracks failed attempts and locks out brute-force attackers after 5 failures."""
        now = time.time()
        if success:
            if client_ip in self._failed_login_attempts:
                del self._failed_login_attempts[client_ip]
            return {"allowed": True, "failed_count": 0}

        # Failed attempt
        attempts = self._failed_login_attempts[client_ip]
        self._failed_login_attempts[client_ip] = [t for t in attempts if now - t < 900.0]  # 15 min window
        self._failed_login_attempts[client_ip].append(now)

        failure_count = len(self._failed_login_attempts[client_ip])
        if failure_count >= 5:
            self._blocked_ips[client_ip] = now + 900.0  # Ban IP for 15 minutes
            return {
                "allowed": False,
                "locked_out": True,
                "lockout_seconds_remaining": 900,
                "message": "Too many failed login attempts. IP temporarily locked for 15 minutes."
            }

        return {
            "allowed": True,
            "failed_count": failure_count,
            "attempts_remaining": 5 - failure_count
        }

    @staticmethod
    def verify_webhook_hmac(payload_bytes: bytes, received_signature: str, secret_key: str) -> bool:
        """Validates HMAC-SHA256 webhook signatures with constant-time comparison."""
        if not received_signature or not secret_key:
            return False
        expected_sig = hmac.new(secret_key.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, received_signature)

    def get_security_health(self) -> Dict[str, Any]:
        """Returns live security shield telemetry."""
        return {
            "active_tracked_ips": len(self._ip_request_timestamps),
            "currently_blocked_ips": len(self._blocked_ips),
            "anti_ddos_status": "ACTIVE",
            "brute_force_shield": "ACTIVE (5-Attempt Threshold)",
            "hmac_sha256_verifier": "READY",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }


# Global singleton instance
security_shield = SovereignSecurityShield()
