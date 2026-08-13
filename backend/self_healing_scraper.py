"""
Autonomous Self-Healing Scraper Engine
JobHunt Pro SaaS - Zero-Downtime Web Scraper Resilience Module
"""

import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger("self_healing_scraper")

DEFAULT_SELECTORS: Dict[str, Dict[str, str]] = {
    "bayt": {
        "job_card": "li.has-pointer",
        "title": "h2.jb-title",
        "company": "b.p10r",
        "location": "span.p10l",
        "link": "a[href*='/en/job/']",
    },
    "gulftalent": {
        "job_card": "tr.job-row",
        "title": "a.job-title",
        "company": "td.company-name",
        "location": "td.location",
        "link": "a.job-title",
    },
    "linkedin": {
        "job_card": "div.base-card",
        "title": "h3.base-search-card__title",
        "company": "h4.base-search-card__subtitle",
        "location": "span.job-search-card__location",
        "link": "a.base-card__full-link",
    }
}


class SelfHealingScraper:
    """
    Autonomous DOM inspector and self-healing selector engine.
    Detects selector failures in HTML responses, inspects document structure,
    and dynamically infers corrected CSS selectors.
    """

    def __init__(self, platform: str = "bayt"):
        self.platform = platform.lower()
        self.active_selectors = DEFAULT_SELECTORS.get(self.platform, DEFAULT_SELECTORS["bayt"]).copy()
        self.heal_count = 0

    def parse_job_listings(self, html_content: str) -> List[Dict[str, Any]]:
        """Parses job listings using active selectors, auto-triggering healing if selectors fail."""
        if not html_content or len(html_content.strip()) == 0:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        cards = soup.select(self.active_selectors["job_card"])

        # If zero cards found, trigger self-healing fallback search
        if not cards:
            logger.warning(f"Self-Healing Triggered: Primary selector '{self.active_selectors['job_card']}' returned 0 matches on {self.platform}")
            healed = self._auto_heal_selectors(soup)
            if healed:
                cards = soup.select(self.active_selectors["job_card"])

        results = []
        for card in cards:
            title_el = card.select_one(self.active_selectors["title"]) or card.find(re.compile(r"h[1-4]|a"))
            company_el = card.select_one(self.active_selectors["company"]) or card.find(["b", "strong", "span"])
            location_el = card.select_one(self.active_selectors["location"])
            link_el = card.select_one(self.active_selectors["link"]) or card.find("a")

            title = title_el.get_text(strip=True) if title_el else "Unknown Position"
            company = company_el.get_text(strip=True) if company_el else "Target Company"
            location = location_el.get_text(strip=True) if location_el else "Gulf Region"
            url = link_el.get("href") if link_el and link_el.get("href") else "#"

            if len(title) > 2:
                results.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "platform": self.platform,
                    "healed_by_ai": self.heal_count > 0
                })

        return results

    def _auto_heal_selectors(self, soup: BeautifulSoup) -> bool:
        """Inspects HTML DOM tree to discover updated job card container and child elements."""
        candidate_containers = [
            "article", "li", "div[class*='job']", "div[class*='card']",
            "tr[class*='job']", "div[data-job-id]", "div[class*='result']"
        ]

        for container_query in candidate_containers:
            found = soup.select(container_query)
            if len(found) >= 2:  # Repeating job items found
                self.active_selectors["job_card"] = container_query
                self.active_selectors["title"] = "h1, h2, h3, a[class*='title'], a[href*='job']"
                self.active_selectors["company"] = "span[class*='company'], div[class*='company'], b"
                self.active_selectors["link"] = "a[href]"
                self.heal_count += 1
                logger.info(f"Self-Healing Successful: New selector array for {self.platform} set to {self.active_selectors}")
                return True

        return False


# Global instance dictionary
_scrapers: Dict[str, SelfHealingScraper] = {}

def get_self_healing_scraper(platform: str = "bayt") -> SelfHealingScraper:
    """Factory helper returning a persistent SelfHealingScraper instance per platform."""
    if platform not in _scrapers:
        _scrapers[platform] = SelfHealingScraper(platform)
    return _scrapers[platform]
