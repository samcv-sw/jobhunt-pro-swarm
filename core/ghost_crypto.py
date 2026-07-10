"""
JobHunt Pro - Ghost Crypto
Provides AES-128 Fernet encryption for zero-knowledge data masking.
Protects sensitive user data from Ops / Government / Database Leaks.
"""

import logging
import os

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Master Ghost DB Key
# In production, this MUST be an environment variable.
GHOST_DB_KEY = os.getenv("GHOST_DB_KEY", Fernet.generate_key().decode("utf-8"))
_cipher = Fernet(GHOST_DB_KEY.encode("utf-8"))


def encrypt_data(plaintext: str) -> str:
    """Encrypts a string into a base64 encoded AES blob."""
    if not plaintext:
        return plaintext
    try:
        return _cipher.encrypt(plaintext.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"[GHOST CRYPTO] Encryption failed: {e}")
        return plaintext


def decrypt_data(ciphertext: str) -> str:
    """Decrypts a base64 encoded AES blob back into plain text."""
    if not ciphertext:
        return ciphertext
    try:
        return _cipher.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except Exception:
        # If it fails, it might just be legacy plain text data. Return as-is.
        return ciphertext
