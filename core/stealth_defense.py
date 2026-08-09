"""
Stealth Defense Engine for JobHunt Pro SaaS
Combines stealth request header obfuscation, proxy circuit breaker rotation, and zero-trust payload sanitization.
"""

import random
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
]

ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9,ar;q=0.8",
    "ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-GB,en;q=0.9,ar-AE;q=0.8",
    "fr-FR,fr;q=0.9,en;q=0.8",
]

class StealthDefenseEngine:
    def __init__(self):
        self.fail_counts: Dict[str, int] = {}
        self.circuit_open_proxies: set = set()

    def get_obfuscated_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Generate obfuscated HTTP headers to bypass anti-bot rate limiters."""
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": random.choice(ACCEPT_LANGUAGES),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers

    def record_proxy_failure(self, proxy_url: str, max_fails: int = 3):
        """Record proxy failure and trigger circuit breaker if failure threshold is reached."""
        current = self.fail_counts.get(proxy_url, 0) + 1
        self.fail_counts[proxy_url] = current
        if current >= max_fails:
            self.circuit_open_proxies.add(proxy_url)
            logger.warning(f"[StealthDefense] Circuit breaker OPEN for proxy: {proxy_url}")

    def record_proxy_success(self, proxy_url: str):
        """Reset proxy failure count on successful request."""
        self.fail_counts[proxy_url] = 0
        if proxy_url in self.circuit_open_proxies:
            self.circuit_open_proxies.remove(proxy_url)

    def is_proxy_healthy(self, proxy_url: str) -> bool:
        """Check if proxy circuit breaker is open (unhealthy)."""
        return proxy_url not in self.circuit_open_proxies

    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """Zero-trust HTML and script injection sanitizer for user input strings."""
        if not text:
            return ""
        clean = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r'<style.*?>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r'on\w+="[^"]*"', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'on\w+=\'[^\']*\'', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'javascript:', '', clean, flags=re.IGNORECASE)
        return clean.strip()

stealth_defense = StealthDefenseEngine()
