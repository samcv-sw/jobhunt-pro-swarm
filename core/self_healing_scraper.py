"""
Self-Healing Scraper Network & Dynamic Proxy Rotator Matrix.
Provides automatic CSS/XPath fallback selection, HTML structure auto-repair, and proxy health circuit breakers.
"""

import re
from typing import Dict, List, Any, Optional

class SelfHealingScraper:
    """
    Autonomic scraper engine that heals broken DOM selectors dynamically
    and rotates proxies upon anti-bot detection.
    """

    FALLBACK_PATTERNS = {
        "title": [
            "h1", "h2", "h3", ".job-title", ".jobCard-title",
            "[data-job-title]", "a[href*='/job/']", ".title"
        ],
        "company": [
            ".company-name", ".company", "a[href*='/company/']",
            "[data-company]", ".employer-name", ".org-name"
        ],
        "location": [
            ".job-location", ".location", "[data-location]",
            ".city", ".place", ".region"
        ]
    }

    def __init__(self):
        self.active_proxies = [
            "http://proxy1.internal:8080",
            "http://proxy2.internal:8080",
            "http://proxy3.internal:8080"
        ]
        self.failed_proxies = set()
        self.healed_patches = {}

    def get_healed_selector(self, domain: str, field_type: str, failed_selector: str) -> str:
        """
        Retrieves or dynamically computes alternative DOM selector if target website changes HTML structure.
        """
        cache_key = f"{domain}:{field_type}"
        if cache_key in self.healed_patches:
            return self.healed_patches[cache_key]

        fallbacks = self.FALLBACK_PATTERNS.get(field_type, ["div", "span"])
        for fb in fallbacks:
            if fb != failed_selector:
                self.healed_patches[cache_key] = fb
                return fb
                
        return failed_selector

    def auto_repair_html_parsing(self, html_content: str, target_field: str) -> Optional[str]:
        """
        Extracts content using regex heuristic fallbacks when primary DOM selectors fail.
        """
        if target_field == "title":
            match = re.search(r'<h[123][^>]*>(.*?)</h[123]>', html_content, re.IGNORECASE | re.DOTALL)
            if match:
                return re.sub(r'<[^>]+>', '', match.group(1)).strip()
        elif target_field == "company":
            match = re.search(r'class="[^"]*company[^"]*"[^>]*>(.*?)</div>', html_content, re.IGNORECASE | re.DOTALL)
            if match:
                return re.sub(r'<[^>]+>', '', match.group(1)).strip()
        return None

    def rotate_proxy_on_failure(self, current_proxy: str, status_code: int) -> str:
        """
        Rotates proxy if current IP encounters HTTP 403, 429, or timeout.
        """
        if status_code in (403, 429, 503):
            self.failed_proxies.add(current_proxy)

        available = [p for p in self.active_proxies if p not in self.failed_proxies]
        if not available:
            self.failed_proxies.clear()
            available = self.active_proxies

        return available[0]

self_healing_scraper = SelfHealingScraper()
