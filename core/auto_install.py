"""Auto-install missing packages on PA startup - v16.310"""

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

REQUIRED_PACKAGES = ["fpdf", "aiosmtplib"]


def ensure_packages():
    """Install missing packages on PA."""
    import os
    if os.getenv("SKIP_INSTALL") == "true" or os.getenv("TESTING") == "true":
        logger.info("[PACKAGE] Skipping auto-install in verification/testing environment")
        return
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            logger.warning(f"[PACKAGE] Installing {pkg}...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--user", pkg],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=60,
                )
                logger.info(f"[PACKAGE] {pkg} installed successfully")
            except Exception as e:
                logger.error(f"[PACKAGE] Failed to install {pkg}: {e}")
