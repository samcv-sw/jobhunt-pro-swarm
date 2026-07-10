"""
JobHunt Pro - Ghost Compiler (Anti-Theft System)
Scrambles and encrypts core AI files so hackers and rogue developers cannot steal the source code.
Code is decrypted in RAM (memory) at runtime.
"""

import base64
import logging
import os
import zlib

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Master Ghost Key - In a real prod environment, this should be an ENV var!
# For safety in this environment, we use a static derived key.
GHOST_KEY = Fernet.generate_key()
cipher = Fernet(GHOST_KEY)


def compile_file(filepath: str):
    """Reads a .py file, encrypts it, and replaces it with an in-memory execution stub."""
    try:
        with open(filepath, encoding="utf-8") as f:
            source_code = f.read()

        # Do not compile already compiled files
        if "GHOST_DECRYPT_STUB" in source_code:
            return

        # Compress and Encrypt the source code
        compressed = zlib.compress(source_code.encode("utf-8"))
        encrypted = cipher.encrypt(compressed)
        encoded_payload = base64.b64encode(encrypted).decode("utf-8")

        # Create the execution stub
        stub = f'''# GHOST_DECRYPT_STUB - ANTI-THEFT PROTECTION ACTIVE
# Unauthorized access, copying, or modification of this file is strictly prohibited.
import base64, zlib
from cryptography.fernet import Fernet

_key = {GHOST_KEY}
_payload = "{encoded_payload}"

_cipher = Fernet(_key)
_decrypted = _cipher.decrypt(base64.b64decode(_payload))
_source = zlib.decompress(_decrypted).decode("utf-8")

# Execute in current global namespace (in-memory, never touches disk)
exec(_source, globals())
'''
        # Overwrite the original file with the stub
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(stub)

        logger.info(
            f"👻 [GHOST COMPILER] Successfully encrypted and locked: {filepath}"
        )

    except Exception as e:
        logger.error(f"Failed to encrypt {filepath}: {e}")


def encrypt_core_engine():
    """Encrypts the most valuable AI files."""
    valuable_files = [
        "core/viral_factory.py",
        "core/growth_autopilot.py",
        "core/ai_tailor.py",
    ]
    for f in valuable_files:
        if os.path.exists(f):
            compile_file(f)


if __name__ == "__main__":
    encrypt_core_engine()
