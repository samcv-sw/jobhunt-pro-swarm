"""
JobHunt Pro — BYOSMTP (Bring Your Own SMTP)
Users provide their own Gmail credentials → PA sends through THEIR account.
Encrypted storage. Zero PA SMTP cost. Unlimited scaling.
"""

import json
import logging
import base64
import os
from typing import Optional, Dict, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


# Derive encryption key from APP_SECRET (consistent across PA restarts)
def _get_fernet() -> Optional[Fernet]:
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
    return Fernet(key)


def encrypt_credentials(email: str, password: str) -> Optional[str]:
    """Encrypt SMTP credentials. Returns base64 token or None."""
    f = _get_fernet()
    if not f:
        return None
    data = json.dumps({"e": email, "p": password}).encode()
    return f.encrypt(data).decode()


def decrypt_credentials(token: str) -> Optional[Dict[str, str]]:
    """Decrypt SMTP credentials. Returns {'email': ..., 'password': ...} or None."""
    f = _get_fernet()
    if not f:
        return None
    try:
        data = json.loads(f.decrypt(token.encode()))
        return {"email": data["e"], "password": data["p"]}
    except Exception as e:
        logger.error(f"[BYOSMTP] Decrypt failed: {e}")
        return None


def get_user_smtp(storage_token: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Get user's SMTP credentials from storage token.
    Returns dict with 'email', 'password' or None if not configured.
    """
    if not storage_token:
        return None
    return decrypt_credentials(storage_token)


def smtp_config_from_credentials(
    email: str, password: str, provider: str = "gmail"
) -> Dict[str, Any]:
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
) -> Tuple[bool, str]:
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
