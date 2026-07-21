"""
core/tor_router.py — Tor SOCKS5 & Onion Router Engine

Provides native support for routing JobHunt Pro network traffic through the Tor network,
renewing Tor IP circuits dynamically, and generating Tor Hidden Service (.onion) configurations.
"""
from __future__ import annotations

import logging
import os
import socket
import time
from typing import Any

logger = logging.getLogger(__name__)


class TorRouter:
    """Tor Network Manager for JobHunt Pro.
    
    Supports:
    - Checking Tor SOCKS5 service availability (ports 9050, 9052).
    - Exposing proxy dicts for requests/httpx/urllib.
    - Renewing Tor circuit IP addresses via Tor Control Port (9051) using SIGNAL NEWNYM.
    - Generating Torrc Hidden Service (.onion) configuration blocks.
    """

    def __init__(
        self,
        socks_host: str = "127.0.0.1",
        socks_port: int = 9050,
        control_port: int = 9051,
        control_password: str = "",
    ):
        self.socks_host = os.getenv("TOR_SOCKS_HOST", socks_host)
        self.socks_port = int(os.getenv("TOR_SOCKS_PORT", socks_port))
        self.control_port = int(os.getenv("TOR_CONTROL_PORT", control_port))
        self.control_password = os.getenv("TOR_CONTROL_PASSWORD", control_password)

    def is_tor_active(self) -> bool:
        """Check if local Tor SOCKS5 port is accessible."""
        try:
            with socket.create_connection((self.socks_host, self.socks_port), timeout=2.0):
                return True
        except (socket.error, OSError):
            # Try Tor Browser default port 9052 if 9050 is closed
            if self.socks_port == 9050:
                try:
                    with socket.create_connection((self.socks_host, 9052), timeout=2.0):
                        self.socks_port = 9052
                        return True
                except (socket.error, OSError):
                    pass
            return False

    def get_tor_proxy_dict(self) -> dict[str, str]:
        """Return proxy configuration dict suitable for requests / httpx."""
        url = f"socks5h://{self.socks_host}:{self.socks_port}"
        return {
            "http": url,
            "https": url,
        }

    def renew_circuit(self, timeout: float = 5.0) -> bool:
        """Connect to Tor Control Port (9051) and send SIGNAL NEWNYM to get a fresh IP."""
        try:
            with socket.create_connection((self.socks_host, self.control_port), timeout=timeout) as s:
                s.settimeout(timeout)
                # Read initial response if any or authenticate
                auth_cmd = f'AUTHENTICATE "{self.control_password}"\r\n' if self.control_password else 'AUTHENTICATE ""\r\n'
                s.sendall(auth_cmd.encode("utf-8"))
                resp = s.recv(1024).decode("utf-8", errors="ignore")
                
                if "250 OK" not in resp:
                    logger.warning("Tor Control Auth failed: %s", resp.strip())
                    return False

                s.sendall(b"SIGNAL NEWNYM\r\n")
                signal_resp = s.recv(1024).decode("utf-8", errors="ignore")
                
                if "250 OK" in signal_resp:
                    logger.info("Tor circuit renewed successfully (SIGNAL NEWNYM)")
                    time.sleep(1.0)  # Wait briefly for circuit creation
                    return True
                else:
                    logger.warning("Tor NEWNYM signal failed: %s", signal_resp.strip())
                    return False
        except Exception as err:
            logger.debug("Tor control connection failed: %s", err)
            return False

    @staticmethod
    def generate_onion_torrc(
        service_name: str = "jobhunt_pro",
        service_dir: str = "/var/lib/tor/jobhunt_pro_onion/",
        local_port: int = 8000,
        onion_port: int = 80,
    ) -> str:
        """Generate torrc configuration lines for hosting JobHunt Pro as a .onion service."""
        return (
            f"# JobHunt Pro Hidden Service ({service_name})\n"
            f"HiddenServiceDir {service_dir}\n"
            f"HiddenServicePort {onion_port} 127.0.0.1:{local_port}\n"
        )


# Singleton instance helper
_tor_router_instance: TorRouter | None = None


def get_tor_router() -> TorRouter:
    """Get or initialize the global TorRouter singleton."""
    global _tor_router_instance
    if _tor_router_instance is None:
        _tor_router_instance = TorRouter()
    return _tor_router_instance
