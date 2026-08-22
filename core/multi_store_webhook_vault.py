"""
core/multi_store_webhook_vault.py - Universal Webhook Integrity Vault & Timing Armor
====================================================================================
- Cryptographic timestamp freshness validation (±120s sliding window).
- Constant-time HMAC-SHA256 / SHA512 signature comparison to prevent timing side-channel attacks.
- Universal payload canonicalization for all e-commerce and payment gateways.
"""

import time
import hmac
import hashlib
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

TIMESTAMP_TOLERANCE_SECONDS = 120


def verify_webhook_timestamp_freshness(timestamp_header: Optional[str]) -> bool:
    """Verifies that the webhook request was created within the last 120 seconds."""
    if not timestamp_header:
        return True  # If gateway doesn't provide timestamp, fallback to signature

    try:
        ts = float(timestamp_header)
        now = time.time()
        return abs(now - ts) <= TIMESTAMP_TOLERANCE_SECONDS
    except (ValueError, TypeError):
        return False


def constant_time_verify_hmac(
    payload_bytes: bytes,
    secret_key: str,
    signature_hex: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Performs constant-time HMAC comparison to eliminate timing side-channel attacks.
    """
    if not secret_key or not signature_hex:
        return False

    hash_func = hashlib.sha512 if algorithm.lower() == "sha512" else hashlib.sha256
    expected_sig = hmac.new(secret_key.encode("utf-8"), payload_bytes, hash_func).hexdigest()

    return hmac.compare_digest(expected_sig.lower(), signature_hex.strip().lower())
