"""
ScamDetector v1 — JobHunt Pro Scam & Fraud Protection
Prevents sending applications to MLM schemes, crypto scams, fake job postings, etc.

Created: 2026-06-24 — Deep Scan Session
"""

import re
import logging
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# SCAM PATTERNS
# ══════════════════════════════════════════════════════════════════════════

SCAM_COMPANY_PATTERNS = {
    "mlm_pyramid": [
        "amway", "herbalife", "nu skin", "primerica", "doterra", "young living",
        "world ventures", "isagenix", "usana", "arbonne", "monat", "senegence",
        "mary kay", "avon", "pampered chef", "tupperware", "scentsy",
        "kyani", "jeunesse", "qnet", "organo gold", "forever living",
        "it works global", "lifevantage", "melaleuca", "younique",
        "paparazzi accessories", "color street", "thirty-one gifts",
        "norwex", "partylite", "lularoe", "seacret", "jem jewels",
    ],
    "crypto_fraud": [
        "bitconnect", "onecoin", "plus token", "wootrade",
        "celsius network", "blockfi", "genesis", "gemini earn",
        "crypto exchange", "trading signals", "defi yield",
        "binary options", "forex signals", "trading bot",
        "crypto trading", "crypto arbitrage", "nft flipping",
        "bitcoin mining", "cloud mining", "coinbase remote",
        "binance remote", "kraken support", "crypto wallet support",
    ],
    "fake_agency": [
        "top recruitment", "expert staffing", "pro hiring",
        "elite placements", "alpha recruit", "prime talent",
        "global placement", "direct staffing solutions",
        "recruitment agency hiring 100 junior it",
        "hiring 50+ positions", "urgent requirement 500+",
        "mass recruitment", "walk in interview 200+",
    ],
    "ponzi_schemes": [
        "profit sharing", "passive income", "residual income",
        "financial freedom", "retire early", "earn while you sleep",
        "make money online", "work from home earn",
        "get rich quick", "double your income",
        "unlimited earning potential", "$500/day",
        "$1000/week", "earn $", "make $",
    ],
    "data_harvesting": [
        "data entry $", "typing jobs $", "form filling",
        "online survey", "mystery shopper", "envelope stuffing",
        "package forwarding", "reshipping", "rebate processing",
        "payment processing agent", "money transfer agent",
        "send/receive packages", "work at home assembly",
    ],
    "ghost_jobs": [
        "urgent hiring", "immediate joining", "no interview",
        "direct payroll", "apply by replying", "apply by whatsapp",
        "interview via telegram", "whatsapp interview only",
        "telegram interview", "no experience required $",
        "work from home no experience",
    ],
}

SCAM_TITLE_KEYWORDS = [
    "$500/day", "$1000/week", "earn $", "make money",
    "get rich", "work from home $", "passive income",
    "no experience $", "immediate start $", "guaranteed income",
    "unlimited earning", "financial freedom",
    "data entry clerk", "form filler", "online typist",
    "mystery shopper", "package handler home",
]

SCAM_TLD_BLOCKLIST = [
    ".xyz", ".top", ".tk", ".ml", ".ga", ".cf",
    ".gq", ".work", ".click", ".link", ".country",
    ".loan", ".stream", ".download", ".racing",
]

SCAM_SALARY_FLAGS = [
    # "Too good to be true" salary for entry/network roles
    (5000, "monthly"),  # $5K+/month for entry-level = suspect
    (200, "hourly"),    # $200+/hour for general roles
]

PHYSICAL_ADDRESS = "1084 Rue 54, Jnah, Beirut, Lebanon"
import sys
from pathlib import Path
_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))
try:
    import config
    SITE_URL = getattr(config, 'SITE_URL', 'https://jhfguf.pythonanywhere.com').rstrip('/')
except Exception:
    import os
    SITE_URL = os.getenv("SITE_URL", "https://jhfguf.pythonanywhere.com").rstrip('/')
UNSUBSCRIBE_URL = f"{SITE_URL}/unsubscribe"


class ScamDetector:
    """Detects scam/fraudulent job postings before they reach candidates."""

    def __init__(self):
        self._compiled_company = {}
        for category, patterns in SCAM_COMPANY_PATTERNS.items():
            self._compiled_company[category] = [
                re.compile(re.escape(p), re.IGNORECASE) for p in patterns
            ]
        self._compiled_titles = [
            re.compile(re.escape(k), re.IGNORECASE) for k in SCAM_TITLE_KEYWORDS
        ]
        self._tld_re = re.compile(
            "\.(xyz|top|tk|ml|ga|cf|gq|work|click|link|country|loan|stream|download|racing)$",
            re.IGNORECASE
        )

    def is_scam(self, job: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if a job posting is a scam.
        Returns (is_scam: bool, reason: str)
        """
        company = (job.get("company") or "").strip()
        title = (job.get("title") or "").strip()
        snippet = (job.get("snippet") or job.get("description") or "").strip()
        url = (job.get("url") or job.get("apply_url") or "").strip()
        email = (job.get("email") or "").strip()
        salary = job.get("salary") or job.get("salary_max") or 0

        combined = f"{company} {title} {snippet} {url}".lower()

        # 1. Check company against scam patterns
        for category, patterns in self._compiled_company.items():
            for pat in patterns:
                if pat.search(company) or pat.search(combined):
                    return True, f"Scam detected: {category} pattern"

        # 2. Check title for obvious scam keywords
        for pat in self._compiled_titles:
            if pat.search(title) or pat.search(combined):
                return True, "Scam title keyword detected"

        # 3. Check for suspicious TLDs
        if url:
            from urllib.parse import urlparse
            try:
                domain = urlparse(url).netloc.lower()
                if self._tld_re.search(domain):
                    return True, f"Suspicious TLD detected: {domain}"
            except Exception:
                pass

        if email:
            try:
                email_domain = email.split("@")[-1].lower()
                if self._tld_re.search(email_domain):
                    return True, f"Suspicious email TLD: {email_domain}"
            except Exception:
                pass

        # 4. Salary sanity check
        if salary:
            try:
                s = float(salary)
                for threshold, period in SCAM_SALARY_FLAGS:
                    if (period == "monthly" and s > threshold) or \
                       (period == "hourly" and s > threshold):
                        return True, f"Suspicious salary: ${s:,.0f}/{period}"
            except (ValueError, TypeError):
                pass

        # 5. Ghost job patterns
        ghost_flags = ["no interview", "no experience", "apply by whatsapp",
                       "telegram interview", "immediate hire", "walk in",
                       "urgent opening", "send cv to whatsapp"]
        ghost_count = sum(1 for f in ghost_flags if f in combined)
        if ghost_count >= 2:
            return True, "Ghost/too-good-to-be-true job (multiple flags)"

        return False, ""

    def should_send(self, job: Dict[str, Any]) -> Tuple[bool, str]:
        """Alias: inverse of is_scam. Returns (safe_to_send, reason_if_not)."""
        scam, reason = self.is_scam(job)
        if scam:
            return False, reason
        return True, "Clean"

    def score(self, job: Dict[str, Any]) -> float:
        """Return job legitimacy score 0.0 (definitely scam) to 1.0 (clean)."""
        scam, _ = self.is_scam(job)
        return 0.0 if scam else 1.0


# Singleton
_scam_detector: Optional[ScamDetector] = None


def get_scam_detector() -> ScamDetector:
    global _scam_detector
    if _scam_detector is None:
        _scam_detector = ScamDetector()
    return _scam_detector


def is_scam_job(job: Dict[str, Any]) -> Tuple[bool, str]:
    """Convenience function."""
    return get_scam_detector().is_scam(job)


def get_email_footer() -> str:
    """CAN-SPAM compliant email footer with physical address."""
    return (
        '<br><br>'
        '<div style="font-size:11px;color:#888;border-top:1px solid #ddd;padding-top:12px;margin-top:20px;">'
        '<p style="margin:0 0 4px 0;">This application was sent via JobHunt Pro — '
        'an automated job search service for Sam Salameh.</p>'
        '<p style="margin:0 0 4px 0;">📫 1084 Rue 54, Jnah, Beirut, Lebanon</p>'
        f'<p style="margin:0;"><a href="{UNSUBSCRIBE_URL}" style="color:#888;">Unsubscribe</a> '
        '&bull; Not interested in this application? We apologize for the contact.</p>'
        '</div>'
    )
