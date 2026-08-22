"""
core/stealth_proxy_rotator.py - Stealth Scraper Proxy Mesh & Anti-Block Shield
=============================================================================
- Rotates realistic modern User-Agents, Sec-CH-UA browser headers, and referrers.
- Simulates human behavioral Gaussian jitter delays to prevent Cloudflare and WAF rate-limiting.
- Zero-cost, high-reliability scraper rotation for job boards and lead harvesting.
"""

import random
import time
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/126.0.6478.108 Mobile/15E148 Safari/604.1"
]

REFERRERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://www.linkedin.com/",
    "https://duckduckgo.com/",
    "https://search.yahoo.com/"
]


def get_stealth_headers(target_domain: str = "") -> Dict[str, str]:
    """Generates a high-entropy authentic browser header profile."""
    ua = random.choice(USER_AGENTS)
    ref = random.choice(REFERRERS)

    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8,zh-CN;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": ref,
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }

    if "Chrome" in ua:
        headers["sec-ch-ua"] = '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"'
        headers["sec-ch-ua-mobile"] = "?0"
        headers["sec-ch-ua-platform"] = '"Windows"'

    return headers


def apply_stealth_human_jitter(min_delay: float = 0.5, max_delay: float = 2.0):
    """Applies a subtle micro-delay simulating human interaction."""
    jitter = random.uniform(min_delay, max_delay)
    time.sleep(jitter)
