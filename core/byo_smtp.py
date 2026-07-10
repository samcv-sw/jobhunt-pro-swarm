"""
JobHunt Pro — BYOSMTP (Bring Your Own SMTP)
Users provide their own Gmail credentials → PA sends through THEIR account.
Encrypted storage. Zero PA SMTP cost. Unlimited scaling.
"""

import base64
import json
import logging
import os
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


# Derive encryption key from APP_SECRET (consistent across PA restarts)
_cached_fernet = None

def _get_fernet() -> Fernet | None:
    global _cached_fernet
    if _cached_fernet is not None:
        return _cached_fernet

    secret = os.getenv("SECRET_KEY") or os.getenv("APP_SECRET")
    if not secret:
        logger.error("[BYOSMTP] No SECRET_KEY/APP_SECRET set! Cannot encrypt.")
        return None
    # Use PBKDF2 to derive a 32-byte key from SECRET_KEY
    salt = b"jobhunt_byo_smtp_v1"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    _cached_fernet = Fernet(key)
    return _cached_fernet


def encrypt_credentials(email: str, password: str) -> str | None:
    """Encrypt SMTP credentials. Returns base64 token or None."""
    f = _get_fernet()
    if not f:
        return None
    data = json.dumps({"e": email, "p": password}).encode()
    return f.encrypt(data).decode()


def decrypt_credentials(token: str) -> dict[str, str] | None:
    """Decrypt SMTP credentials. Returns {'email': ..., 'password': ...} or None."""
    f = _get_fernet()
    if f:
        try:
            data = json.loads(f.decrypt(token.encode()))
            return {"email": data["e"], "password": data["p"]}
        except Exception as e:
            logger.warning(f"[BYOSMTP] Fernet decrypt failed, attempting fallback: {e}")

    try:
        # Fallback: ROT13 character shift-13 used by Cloudflare edge worker
        decoded_bytes = bytes([ord(c) - 13 for c in token])
        decoded = decoded_bytes.decode('utf-8')
        parts = decoded.split(":")
        if len(parts) >= 2:
            return {"email": parts[0], "password": ":".join(parts[1:])}
    except Exception as rot_err:
        logger.error(f"[BYOSMTP] Fallback ROT13 Decrypt failed: {rot_err}")

    return None


def get_user_smtp(storage_token: str | None) -> dict[str, str] | None:
    """
    Get user's SMTP credentials from storage token.
    Returns dict with 'email', 'password' or None if not configured.
    """
    if not storage_token:
        return None
    return decrypt_credentials(storage_token)


def smtp_config_from_credentials(
    email: str, password: str, provider: str = "gmail"
) -> dict[str, Any]:
    """Build SMTP config dict from user credentials."""
    if provider == "gmail":
        return {
            "host": "smtp.gmail.com",
            "port": 587,
            "user": email,
            "password": password,
            "use_tls": True,
        }
    elif provider == "outlook":
        return {
            "host": "smtp-mail.outlook.com",
            "port": 587,
            "user": email,
            "password": password,
            "use_tls": True,
        }
    else:
        return {
            "host": "smtp.gmail.com",
            "port": 587,
            "user": email,
            "password": password,
            "use_tls": True,
        }


def test_smtp_connection(
    email: str, password: str, provider: str = "gmail"
) -> tuple[bool, str]:
    """Test if SMTP credentials work. Returns (success, message)."""
    try:
        import smtplib

        cfg = smtp_config_from_credentials(email, password, provider)
        server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=10)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(cfg["user"], cfg["password"])
        server.quit()
        return True, "✅ SMTP connection successful!"
    except smtplib.SMTPAuthenticationError:
        return (
            False,
            "❌ Authentication failed. Need App Password (not regular password). Create one at: https://myaccount.google.com/apppasswords",
        )
    except Exception as e:
        return False, f"❌ Connection failed: {str(e)}"
