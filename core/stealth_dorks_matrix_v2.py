"""
Stealth Dorks Matrix V2 Engine
Autonomous $0-cost Google Dorking & Boolean search query generator and harvester
Specialized for Gulf (UAE, KSA, Qatar, Kuwait, Bahrain, Oman) and global remote high-yield tech roles.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional

logger = logging.getLogger("stealth_dorks_matrix_v2")

class StealthDorksMatrixV2:
    """
    Generates advanced Google Dork queries and simulates stealth harvesting
    without paid API dependencies.
    """

    TARGET_HUBS = {
        "dubai": {"country": "United Arab Emirates", "city": "Dubai", "currency": "AED", "tld": ".ae"},
        "riyadh": {"country": "Saudi Arabia", "city": "Riyadh", "currency": "SAR", "tld": ".sa"},
        "abu_dhabi": {"country": "United Arab Emirates", "city": "Abu Dhabi", "currency": "AED", "tld": ".ae"},
        "doha": {"country": "Qatar", "city": "Doha", "currency": "QAR", "tld": ".qa"},
        "kuwait": {"country": "Kuwait", "city": "Kuwait City", "currency": "KWD", "tld": ".kw"},
        "global_remote": {"country": "Global", "city": "Remote", "currency": "USD", "tld": ".com"}
    }

    ATS_PLATFORMS = [
        "greenhouse.io",
        "lever.co",
        "workday.com",
        "ashbyhq.com",
        "smartrecruiters.com",
        "jobs.personio.com",
        "bamboohr.com",
        "recruitee.com",
        "workable.com"
    ]

    BOOLEAN_OPERATORS = ["AND", "OR", "site:", "filetype:", "inurl:", "intitle:"]

    def __init__(self, default_hub: str = "dubai") -> None:
        self.default_hub = default_hub if default_hub in self.TARGET_HUBS else "dubai"

    def build_ats_dork(self, role: str, location: Optional[str] = None, platform: Optional[str] = None) -> Dict[str, Any]:
        """
        Build an advanced ATS Google Dork targeting unlisted or direct application links.
        """
        loc = location or self.default_hub
        hub_info = self.TARGET_HUBS.get(loc.lower(), self.TARGET_HUBS["dubai"])
        city = hub_info["city"]
        
        target_platform = platform if platform in self.ATS_PLATFORMS else "greenhouse.io"
        
        raw_query = f'site:{target_platform} "{role}" ("{city}" OR "{hub_info["country"]}" OR "Remote") -intitle:jobs'
        encoded_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(raw_query)}"
        
        return {
            "role": role,
            "location": city,
            "platform": target_platform,
            "query": raw_query,
            "search_url": encoded_url,
            "intent": "direct_ats_penetration"
        }

    def build_hiring_manager_boolean(self, role: str, department: str = "Engineering", location: str = "Dubai") -> Dict[str, Any]:
        """
        Build a Boolean search query to identify Hiring Managers / VP / Directors on LinkedIn.
        """
        query = (
            f'site:linkedin.com/in/ ("Hiring" OR "We are hiring" OR "Looking for") '
            f'("{role}" OR "{department}") ("{location}" OR "UAE" OR "GCC")'
        )
        encoded_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        
        return {
            "role": role,
            "department": department,
            "location": location,
            "query": query,
            "search_url": encoded_url,
            "intent": "hiring_manager_discovery"
        }

    def build_stealth_matrix(self, role: str, hub: str = "dubai") -> List[Dict[str, Any]]:
        """
        Generates a comprehensive 6-vector search matrix for maximum coverage.
        """
        matrix = []
        hub_info = self.TARGET_HUBS.get(hub.lower(), self.TARGET_HUBS["dubai"])
        city = hub_info["city"]
        country = hub_info["country"]

        # Vector 1: Greenhouse / Lever direct links
        for plat in ["greenhouse.io", "lever.co", "ashbyhq.com"]:
            matrix.append({
                "vector": f"ATS_{plat.split('.')[0].upper()}",
                "query": f'site:{plat} "{role}" ("{city}" OR "{country}")',
                "target_type": "Direct ATS Portal",
                "estimated_yield": "High Intent"
            })

        # Vector 2: Unlisted PDF job descriptions
        matrix.append({
            "vector": "UNLISTED_PDF_SPECS",
            "query": f'filetype:pdf intext:"Job Description" "{role}" ("{city}" OR "{country}") ("Apply" OR "contact")',
            "target_type": "Direct Employer Specs",
            "estimated_yield": "Exclusive Leads"
        })

        # Vector 3: Headhunter & Talent Acquisition posts
        matrix.append({
            "vector": "RECRUITER_POSTS",
            "query": f'site:linkedin.com/posts "urgently hiring" "{role}" ("{city}" OR "{country}")',
            "target_type": "Real-time Recruiter Postings",
            "estimated_yield": "Immediate Opening"
        })

        # Vector 4: GCC Startup & Scaleup Career Pages
        matrix.append({
            "vector": "GCC_CAREER_PAGES",
            "query": f'inurl:careers OR inurl:jobs "{role}" ("{city}" OR "{country}") ("salary" OR "{hub_info["currency"]}")',
            "target_type": "Direct Enterprise Career Boards",
            "estimated_yield": "Direct Company Connection"
        })

        return matrix

    def generate_stealth_queries(self, role: str, location: str = "dubai") -> List[str]:
        """Convenience method returning a flat list of formatted Google dork search queries."""
        matrix = self.build_stealth_matrix(role=role, hub=location)
        return [item["query"] for item in matrix]

    def parse_job_signal(self, raw_text: str) -> Dict[str, Any]:
        """
        Extract structured hiring signals and salary indications from raw scraped snippet.
        """
        has_urgency = bool(re.search(r"(urgent|immediate|asap|fast hiring|priority)", raw_text, re.IGNORECASE))
        has_remote = bool(re.search(r"(remote|hybrid|wfh|work from home)", raw_text, re.IGNORECASE))
        
        # Extract currency match before or after numbers
        currency_match = re.search(
            r"((?:AED|SAR|USD|QAR|KWD|EUR|GBP)\s*[\d,]+(?:\s*-\s*[\d,]+)?(?:\s*(?:AED|SAR|USD|QAR|KWD|EUR|GBP))?|"
            r"[\d,]+\s*(?:AED|SAR|USD|QAR|KWD|EUR|GBP)(?:\s*-\s*[\d,]+\s*(?:AED|SAR|USD|QAR|KWD|EUR|GBP))?)",
            raw_text,
            re.IGNORECASE
        )
        salary_est = currency_match.group(0).strip() if currency_match else "Competitive / Negotiable"

        return {
            "has_urgency": has_urgency,
            "has_remote": has_remote,
            "salary_range": salary_est,
            "signal_confidence": 0.95 if has_urgency else 0.85
        }


# Singleton instance
stealth_dorks_matrix = StealthDorksMatrixV2()
