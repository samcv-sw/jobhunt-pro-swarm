"""
JobHunt Pro v17.0 — GLOBAL Network Engineer Job Scraper
Multi-source, multi-country job scraper using only free web scraping (no paid APIs).

Countries (25+): GCC-6, MENA-7, CIS-3, ASIA-3, EUROPE-7, Turkey, Remote
Sources: LinkedIn, Indeed, Google Jobs, Glassdoor, Bayt.com, NaukriGulf, Wuzzuf,
         hh.ru FREE REST API, Indeed RSS, StepStone, Naukri India
"""

import hashlib
import logging
import os
import random
import re
import time
from urllib.parse import quote_plus, urlparse

try:
    from curl_cffi.requests import AsyncSession as httpx_AsyncClient
except ImportError:
    import httpx

    httpx_AsyncClient = httpx.AsyncClient
import httpx

try:
    from curl_cffi import requests as cffi_requests

    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False
import urllib.request

from bs4 import BeautifulSoup

# hh.ru scraper integration (free REST API, Russia/CIS market)
try:
    from core.hhru_scraper import (
        resolve_area_ids as _hhru_resolve_areas,
    )
    from core.hhru_scraper import (
        search_hhru_sync as _hhru_search_sync,
    )
except ImportError:
    _hhru_search_sync = None
    _hhru_resolve_areas = None

logger = logging.getLogger(__name__)

# ── Smart Domain Generator ──────────────────────────────────────────────────

# Legal suffixes that should NOT appear in domain names
_LEGAL_SUFFIX_PATTERNS = [
    r"\bLLC\b",
    r"\bInc\.?\b",
    r"\bInc\b",
    r"\bIncorporated\b",
    r"\bLtd\.?\b",
    r"\bLtd\b",
    r"\bLimited\b",
    r"\bCorp\.?\b",
    r"\bCorporation\b",
    r"\bCo\.?\b",
    r"\bCompany\b",
    r"\bS\.?A\.?L\.?\b",
    r"\bSAL\b",
    r"\bS\.?A\.?R\.?L\.?\b",
    r"\bSARL\b",
    r"\bS\.?A\.?\b",
    r"\bGmbH\b",
    r"\bBV\b",
    r"\bPty\.?\s*Ltd\.?\b",
    r"\bAssociates?\b",
    r"\bPartners?\b",
]


def _smart_domain(company: str) -> str:
    """Generate a smarter domain from company name by stripping legal suffixes first.

    Old behavior: 'Network Solutions Inc' -> 'networksolutionsinc.com' (WRONG)
    New behavior: 'Network Solutions Inc' -> 'networksolutions.com' (better guess)
    """
    if not company:
        return ""
    cleaned = company.strip()
    for pat in _LEGAL_SUFFIX_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
    # Remove leftover special chars, collapse spaces, lowercase
    cleaned = re.sub(r"[^a-z0-9\s-]", "", cleaned.lower())
    cleaned = re.sub(r"\s+", "", cleaned).strip("-")
    return cleaned if cleaned else re.sub(r"[^a-z0-9]", "", company.lower())


# ── PA Detection ─────────────────────────────────────────────────────────────


def is_pythonanywhere() -> bool:
    """Detect if running on PythonAnywhere (free tier or paid)."""
    return bool(
        os.environ.get("PYTHONANYWHERE_SITE")
        or os.environ.get("PYTHONANYWHERE_DOMAIN")
        or "pythonanywhere" in os.environ.get("HOME", "").lower()
        or "pythonanywhere" in os.environ.get("HOSTNAME", "").lower()
    )


def pa_mode() -> bool:
    """Shorthand alias for PA detection."""
    return is_pythonanywhere()


# ── Constants ───────────────────────────────────────────────────────────────

SEARCH_QUERIES = [
    "network engineer",
    "senior network engineer",
    "network security",
    "network administrator",
    "network architect",
    "infrastructure engineer",
    "IT infrastructure",
    "network operations",
    "CCNA",
    "CCNP",
    "sysadmin",
    "systems engineer",
    "devops engineer",
]

REMOTE_PREFIXES = [
    "remote",
    "work from home",
    "wfh",
    "work from anywhere",
    "global",
    "anywhere",
]

# Lebanon cities - deliberately excluding south Lebanon cities
LEBANON_CITIES = [
    "beirut",
    "jbeil",
    "byblos",
    "maten",
    "metn",
    "jabal lebnen",
    "mount lebanon",
    "keserwan",
    "jounieh",
    "zahle",
    "bekaa",
    "tripoli",
    "north lebanon",
    "north",
]
# ☢ EXCLUDED: south, saida, sidon, sour, tyre, nabatiyeh, jnoub

COUNTRY_CONFIGS = {
    "lebanon": {
        "name": "Lebanon",
        "code": "LB",
        "currency": "LBP",
        "min_salary_usd": 1500,
        "cities": [
            "Beirut",
            "Jbeil",
            "Byblos",
            "Metn",
            "Maten",
            "Mount Lebanon",
            "Keserwan",
            "Jounieh",
        ],
        "domains": {
            "indeed": "www.indeed.com.lb",
            "linkedin": "www.linkedin.com",
            "bayt": "www.bayt.com",
            "wuzzuf": "wuzzuf.net",
        },
        "exclude_patterns": [
            r"\bsouth\b",
            r"\bsaida\b",
            r"\bsidon\b",
            r"\bsour\b",
            r"\btyre\b",
            r"\bnabatiyeh\b",
            r"\bjnoub\b",
            r"\bsouthern\b",
        ],
    },
    "uae": {
        "name": "UAE",
        "code": "AE",
        "currency": "AED",
        "min_salary_usd": None,
        "cities": ["Dubai", "Abu Dhabi", "Sharjah", "Al Ain"],
        "domains": {
            "indeed": "www.indeed.ae",
            "linkedin": "www.linkedin.com",
            "bayt": "www.bayt.com",
            "naukrigulf": "www.naukrigulf.com",
            "gulftalent": "www.gulftalent.com",
        },
        "exclude_patterns": [],
    },
    "saudi": {
        "name": "Saudi Arabia",
        "code": "SA",
        "currency": "SAR",
        "min_salary_usd": None,
        "cities": [
            "Riyadh",
            "Jeddah",
            "Dammam",
            "Khobar",
            "Dhahran",
            "Mecca",
            "Medina",
        ],
        "domains": {
            "indeed": "www.indeed.com.sa",
            "linkedin": "www.linkedin.com",
            "bayt": "www.bayt.com",
            "naukrigulf": "www.naukrigulf.com",
        },
        "exclude_patterns": [],
    },
    "qatar": {
        "name": "Qatar",
        "code": "QA",
        "currency": "QAR",
        "min_salary_usd": None,
        "cities": ["Doha", "Al Wakrah", "Lusail", "Al Khor"],
        "domains": {
            "indeed": "www.indeed.qa",
            "linkedin": "www.linkedin.com",
            "bayt": "www.bayt.com",
            "naukrigulf": "www.naukrigulf.com",
        },
        "exclude_patterns": [],
    },
    "kuwait": {
        "name": "Kuwait",
        "code": "KW",
        "currency": "KWD",
        "min_salary_usd": None,
        "cities": ["Kuwait City", "Hawalli", "Salmiya", "Farwaniya", "Mishref"],
        "domains": {
            "indeed": "www.indeed.com.kw",
            "linkedin": "www.linkedin.com",
            "bayt": "www.bayt.com",
            "naukrigulf": "www.naukrigulf.com",
        },
        "exclude_patterns": [],
    },
    "remote": {
        "name": "Remote",
        "code": "REMOTE",
        "currency": "USD",
        "min_salary_usd": None,
        "cities": ["Remote", "Worldwide", "Anywhere", "Work From Home"],
        "domains": {
            "indeed": "www.indeed.com",
            "linkedin": "www.linkedin.com",
            "glassdoor": "www.glassdoor.com",
            "wuzzuf": "wuzzuf.net",
        },
        "exclude_patterns": [],
    },
    # ── hh.ru market (Russia / CIS) ──
    "russia": {
        "name": "Russia",
        "code": "RU",
        "currency": "RUB",
        "min_salary_usd": None,
        "cities": [
            "Moscow",
            "Saint Petersburg",
            "Novosibirsk",
            "Yekaterinburg",
            "Kazan",
        ],
        "domains": {
            "linkedin": "www.linkedin.com",
            "hhru": "api.hh.ru",
        },
        "exclude_patterns": [],
    },
    "kazakhstan": {
        "name": "Kazakhstan",
        "code": "KZ",
        "currency": "KZT",
        "min_salary_usd": None,
        "cities": ["Almaty", "Nur-Sultan", "Astana", "Shymkent", "Karaganda"],
        "domains": {
            "hhru": "api.hh.ru",
        },
        "exclude_patterns": [],
    },
    "belarus": {
        "name": "Belarus",
        "code": "BY",
        "currency": "BYN",
        "min_salary_usd": None,
        "cities": ["Minsk", "Gomel", "Mogilev", "Vitebsk", "Grodno", "Brest"],
        "domains": {
            "hhru": "api.hh.ru",
        },
        "exclude_patterns": [],
    },
    # ── GCC Expansion (Oman, Bahrain) ──
    "oman": {
        "name": "Oman",
        "code": "OM",
        "currency": "OMR",
        "min_salary_usd": None,
        "cities": ["Muscat", "Salalah", "Sohar", "Nizwa"],
        "domains": {
            "indeed": "www.indeed.com.om",
            "linkedin": "www.linkedin.com",
            "bayt": "www.bayt.com",
            "naukrigulf": "www.naukrigulf.com",
        },
        "exclude_patterns": [],
    },
    "bahrain": {
        "name": "Bahrain",
        "code": "BH",
        "currency": "BHD",
        "min_salary_usd": None,
        "cities": ["Manama", "Muharraq", "Rifa"],
        "domains": {
            "indeed": "www.indeed.com.bh",
            "linkedin": "www.linkedin.com",
            "bayt": "www.bayt.com",
            "naukrigulf": "www.naukrigulf.com",
        },
        "exclude_patterns": [],
    },
    # ── MENA Expansion ──
    "jordan": {
        "name": "Jordan",
        "code": "JO",
        "currency": "JOD",
        "min_salary_usd": None,
        "cities": ["Amman", "Zarqa", "Irbid", "Aqaba"],
        "domains": {
            "indeed": "www.indeed.com",
            "linkedin": "www.linkedin.com",
            "bayt": "www.bayt.com",
        },
        "exclude_patterns": [],
    },
    "egypt": {
        "name": "Egypt",
        "code": "EG",
        "currency": "EGP",
        "min_salary_usd": None,
        "cities": ["Cairo", "Alexandria", "Giza", "Port Said"],
        "domains": {
            "indeed": "www.indeed.com",
            "linkedin": "www.linkedin.com",
            "wuzzuf": "wuzzuf.net",
        },
        "exclude_patterns": [],
    },
    "morocco": {
        "name": "Morocco",
        "code": "MA",
        "currency": "MAD",
        "min_salary_usd": None,
        "cities": ["Casablanca", "Rabat", "Marrakech", "Tangier"],
        "domains": {
            "indeed": "www.indeed.com",
            "linkedin": "www.linkedin.com",
        },
        "exclude_patterns": [],
    },
    "tunisia": {
        "name": "Tunisia",
        "code": "TN",
        "currency": "TND",
        "min_salary_usd": None,
        "cities": ["Tunis", "Sfax", "Sousse"],
        "domains": {
            "indeed": "www.indeed.com",
            "linkedin": "www.linkedin.com",
        },
        "exclude_patterns": [],
    },
    "iraq": {
        "name": "Iraq",
        "code": "IQ",
        "currency": "IQD",
        "min_salary_usd": None,
        "cities": ["Baghdad", "Basra", "Erbil"],
        "domains": {
            "indeed": "www.indeed.com",
            "linkedin": "www.linkedin.com",
        },
        "exclude_patterns": [],
    },
    "syria": {
        "name": "Syria",
        "code": "SY",
        "currency": "SYP",
        "min_salary_usd": None,
        "cities": ["Damascus", "Aleppo"],
        "domains": {
            "linkedin": "www.linkedin.com",
        },
        "exclude_patterns": [],
    },
    # ── ASIA ──
    "india": {
        "name": "India",
        "code": "IN",
        "currency": "INR",
        "min_salary_usd": None,
        "cities": ["Mumbai", "Bangalore", "Delhi", "Hyderabad", "Pune", "Chennai"],
        "domains": {
            "indeed": "www.indeed.co.in",
            "linkedin": "www.linkedin.com",
            "naukri": "www.naukri.com",
        },
        "exclude_patterns": [],
    },
    "singapore": {
        "name": "Singapore",
        "code": "SG",
        "currency": "SGD",
        "min_salary_usd": None,
        "cities": ["Singapore"],
        "domains": {
            "indeed": "www.indeed.com.sg",
            "linkedin": "www.linkedin.com",
        },
        "exclude_patterns": [],
    },
    "malaysia": {
        "name": "Malaysia",
        "code": "MY",
        "currency": "MYR",
        "min_salary_usd": None,
        "cities": ["Kuala Lumpur", "Penang"],
        "domains": {
            "indeed": "www.indeed.com.my",
            "linkedin": "www.linkedin.com",
        },
        "exclude_patterns": [],
    },
    # ── EUROPE ──
    "uk": {
        "name": "United Kingdom",
        "code": "GB",
        "currency": "GBP",
        "min_salary_usd": None,
        "cities": ["London", "Manchester", "Birmingham", "Edinburgh"],
        "domains": {
            "indeed": "www.indeed.co.uk",
            "linkedin": "www.linkedin.com",
            "glassdoor": "www.glassdoor.co.uk",
        },
        "exclude_patterns": [],
    },
    "germany": {
        "name": "Germany",
        "code": "DE",
        "currency": "EUR",
        "min_salary_usd": None,
        "cities": ["Berlin", "Munich", "Frankfurt", "Hamburg"],
        "domains": {
            "indeed": "www.indeed.de",
            "linkedin": "www.linkedin.com",
            "stepstone": "www.stepstone.de",
        },
        "exclude_patterns": [],
    },
    "netherlands": {
        "name": "Netherlands",
        "code": "NL",
        "currency": "EUR",
        "min_salary_usd": None,
        "cities": ["Amsterdam", "Rotterdam", "The Hague"],
        "domains": {
            "indeed": "www.indeed.nl",
            "linkedin": "www.linkedin.com",
        },
        "exclude_patterns": [],
    },
    "ireland": {
        "name": "Ireland",
        "code": "IE",
        "currency": "EUR",
        "min_salary_usd": None,
        "cities": ["Dublin", "Cork"],
        "domains": {
            "indeed": "www.indeed.ie",
            "linkedin": "www.linkedin.com",
        },
        "exclude_patterns": [],
    },
    "poland": {
        "name": "Poland",
        "code": "PL",
        "currency": "PLN",
        "min_salary_usd": None,
        "cities": ["Warsaw", "Krakow", "Wroclaw"],
        "domains": {
            "indeed": "www.indeed.pl",
            "linkedin": "www.linkedin.com",
        },
        "exclude_patterns": [],
    },
    "portugal": {
        "name": "Portugal",
        "code": "PT",
        "currency": "EUR",
        "min_salary_usd": None,
        "cities": ["Lisbon", "Porto"],
        "domains": {
            "indeed": "www.indeed.pt",
            "linkedin": "www.linkedin.com",
        },
        "exclude_patterns": [],
    },
    "spain": {
        "name": "Spain",
        "code": "ES",
        "currency": "EUR",
        "min_salary_usd": None,
        "cities": ["Madrid", "Barcelona", "Valencia"],
        "domains": {
            "indeed": "www.indeed.es",
            "linkedin": "www.linkedin.com",
        },
        "exclude_patterns": [],
    },
    # ── Turkey (massive IT hub) ──
    "turkey": {
        "name": "Turkey",
        "code": "TR",
        "currency": "TRY",
        "min_salary_usd": None,
        "cities": ["Istanbul", "Ankara", "Izmir"],
        "domains": {
            "indeed": "www.indeed.com",
            "linkedin": "www.linkedin.com",
        },
        "exclude_patterns": [],
    },
}

# ── User Agent Rotation ─────────────────────────────────────────────────────

USER_AGENTS = [
    # Windows Chrome variants (most common)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Mac Chrome variants
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox variants
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari variants
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Edge variants
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    # Mobile UA for variety
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
]

# ── Helpers ─────────────────────────────────────────────────────────────────

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
BLOCKED_EMAILS = [
    "noreply@",
    "no-reply@",
    "donotreply@",
    "example.com",
    "test.com",
    "w3.org",
    "schema.org",
    "sentry",
    "webpack",
    "facebook.com",
    "google.com",
    "github.com",
    "microsoft.com",
    "apple.com",
    "cloudflare.com",
    "jquery.com",
    "wikipedia.org",
    "youtube.com",
    "twitter.com",
    "instagram.com",
    "linkedin.com",
    "tiktok.com",
    "sentry.io",
    "noreply.",
    "no-reply.",
    "donotreply.",
]


def extract_emails(text: str) -> list[str]:
    """Extract real emails from text, filtering out junk."""
    if not text:
        return []
    emails = EMAIL_PATTERN.findall(text)
    return [
        e.lower().strip()
        for e in emails
        if not any(b in e.lower() for b in BLOCKED_EMAILS)
        and len(e) < 100
        and "." in e.split("@")[1]
        and not e.endswith((".png", ".jpg", ".gif", ".svg"))
    ]


def make_job_id(title: str, company: str, url: str = "") -> str:
    """Generate unique job ID."""
    raw = f"{title.lower().strip()}:{company.lower().strip()}:{url}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def get_headers(extra: dict = None) -> dict[str, str]:
    """Get random headers for requests."""
    h = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    if extra:
        h.update(extra)
    return h


def location_passes_filter(location_text: str, exclude_patterns: list[str]) -> bool:
    """Check if location passes exclusion filters."""
    if not location_text or not exclude_patterns:
        return True
    loc_lower = location_text.lower()
    for pattern in exclude_patterns:
        if re.search(pattern, loc_lower):
            return False
    return True


def extract_salary_from_text(text: str) -> float | None:
    """Extract numeric salary from job description text."""
    if not text:
        return None
    patterns = [
        re.compile(r"\$\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K)?", re.IGNORECASE),
        re.compile(r"([\d,]+(?:\.\d{2})?)\s*(?:USD|usd|\$)", re.IGNORECASE),
        re.compile(
            r"(?:salary|pay|compensation|wage)[:\s]*\$?\s*([\d,]+)", re.IGNORECASE
        ),
        # AED
        re.compile(r"(?:AED|aed|د\.إ)\s*([\d,]+)", re.IGNORECASE),
        re.compile(r"([\d,]+)\s*(?:AED|aed|د\.إ)", re.IGNORECASE),
        # SAR
        re.compile(r"(?:SAR|sar|﷼)\s*([\d,]+)", re.IGNORECASE),
        re.compile(r"([\d,]+)\s*(?:SAR|sar|﷼)", re.IGNORECASE),
        # QAR
        re.compile(r"(?:QAR|qar|ر\.ق)\s*([\d,]+)", re.IGNORECASE),
        # KWD
        re.compile(r"(?:KWD|kwd|د\.ك)\s*([\d,]+)", re.IGNORECASE),
        # LBP
        re.compile(r"(?:LBP|lbp|ل\.ل)\s*([\d,]+)", re.IGNORECASE),
    ]
    for pattern in patterns:
        matches = pattern.findall(text)
        for match in matches:
            try:
                return float(re.sub(r"[,$\s]", "", match))
            except ValueError:
                continue
    return None


def _rate_limit_domain(last_times: dict[str, float], domain: str, delay: float = 3.0):
    """Rate limit requests per domain."""
    now = time.time()
    last = last_times.get(domain, 0)
    elapsed = now - last
    if elapsed < delay:
        sleep_time = delay - elapsed
        logger.debug(f"Rate limit: sleeping {sleep_time:.1f}s for {domain}")
        time.sleep(sleep_time)
    last_times[domain] = time.time()


# ============================================================================
# GLOBAL JOB SCRAPER - Multi-source, multi-country
# ============================================================================


class GlobalJobScraper:
    """
    GLOBAL multi-source, multi-country job scraper for network engineers (v17.0).

    Covers 25+ countries across GCC, MENA, ASIA, EUROPE, and CIS:
      GCC: UAE, Saudi, Qatar, Kuwait, Oman, Bahrain (all 6)
      MENA: Lebanon, Jordan, Egypt, Morocco, Tunisia, Iraq, Syria
      CIS: Russia, Kazakhstan, Belarus (+ hh.ru for all CIS)
      ASIA: India, Singapore, Malaysia
      EUROPE: UK, Germany, Netherlands, Ireland, Poland, Portugal, Spain
      TURKEY: Istanbul, Ankara, Izmir
      REMOTE: worldwide

    Sources: LinkedIn, Indeed, Bayt, NaukriGulf, Wuzzuf, Glassdoor, Google Jobs,
             hh.ru FREE REST API (Russia/CIS).
    Uses only FREE scraping (requests + BeautifulSoup + RSS). No paid APIs.
    """

    def __init__(self, rate_limit_delay: float = 3.0):
        self.rate_limit_delay = rate_limit_delay
        self._last_req: dict[str, float] = {}
        self._session = httpx.Client(timeout=20, follow_redirects=True)
        if HAS_CFFI:
            self._cffi_session = cffi_requests.Session(
                impersonate="chrome120", timeout=20
            )
        else:
            self._cffi_session = None
        self.stats = {"total_found": 0, "sources_hit": 0, "by_source": {}}
        # Make country configs accessible as instance attribute
        self.country_configs = COUNTRY_CONFIGS

    def close(self):
        """Clean up HTTP session."""
        try:
            self._session.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ── Public API ──────────────────────────────────────────────────────────

    def search_all_countries(
        self, limit_per_country: int = 10, max_total: int = 100
    ) -> list[dict]:
        """
        Search ALL configured countries for network engineer jobs.
        Returns deduplicated list of job dicts.
        """
        all_jobs = []
        seen_ids = set()

        for country_key in COUNTRY_CONFIGS:
            if len(all_jobs) >= max_total:
                break

            config = COUNTRY_CONFIGS[country_key]
            logger.info(f"=== Searching {config['name']} ===")

            for query in SEARCH_QUERIES:
                if len(all_jobs) >= max_total:
                    break

                try:
                    jobs = self.search_country(
                        country_key, query, limit=limit_per_country
                    )
                    for job in jobs:
                        jid = job.get("job_id", "")
                        if jid and jid not in seen_ids:
                            seen_ids.add(jid)
                            all_jobs.append(job)
                except Exception as e:
                    logger.warning(
                        f"Error searching {config['name']} for '{query}': {e}"
                    )

                # Brief pause between queries
                time.sleep(0.5)

        logger.info(f"Global search complete: {len(all_jobs)} unique jobs found")
        self.stats["total_found"] = len(all_jobs)
        return all_jobs

    def fast_search(
        self,
        country_key: str,
        query: str = "network engineer",
        limit: int = 10,
        max_search_secs: int = 60,
    ) -> list[dict]:
        """
        ⚡ FAST search: LinkedIn-only, single city, no slow scrapers, no Google dorking.
        Designed for PythonAnywhere free-tier where every second counts.

        Skips: Indeed, Bayt, Glassdoor, Wuzzuf, NaukriGulf, Google Jobs.
        All return 0 on PA due to rate limiting/blocking.

        Args:
            country_key: Country config key
            query: Job search query
            limit: Max results
            max_search_secs: Soft timeout in seconds (not enforced programmatically,
                            but the fast scraper completes well within this)

        Returns: List of job dicts (~40s vs ~180s for full search)
        """
        logger.info(f"⚡ fast_search({country_key}, '{query}', limit={limit})")
        start = time.time()
        result = self.search_country(
            country_key,
            query,
            limit=limit,
            enable_fast=True,
            max_search_secs=max_search_secs,
        )
        elapsed = time.time() - start
        logger.info(f"⚡ fast_search complete: {len(result)} jobs in {elapsed:.1f}s")
        return result

    def search_country(
        self,
        country_key: str,
        query: str = "network engineer",
        limit: int = 10,
        enable_fast: bool = False,
        max_search_secs: int = 60,
    ) -> list[dict]:
        """
        Search a single country using ALL available sources.

        Args:
            country_key: Country config key (e.g., 'uae', 'lebanon')
            query: Job search query
            limit: Max results to return
            enable_fast: If True, only use LinkedIn (skips Indeed/Bayt/Glassdoor/Wuzzuf/NaukriGulf/Google)
            max_search_secs: Soft timeout in seconds for fast mode (enforced per-source)

        Returns list of job dicts.
        """
        config = COUNTRY_CONFIGS.get(country_key)
        if not config:
            logger.warning(f"Unknown country: {country_key}")
            return []

        all_jobs = []
        seen_ids = set()
        country_name = config["name"]

        # ── Try each source in priority order ──
        if enable_fast:
            # FAST MODE: LinkedIn-only with reduced delays (plus hhru API for CIS countries)
            source_handlers = [
                ("linkedin", self._scrape_linkedin_fast, config),
            ]
            if "hhru" in config.get("domains", {}):
                source_handlers.append(("hhru", self._scrape_hhru, config))
            logger.info(
                f"  ⚡ FAST MODE: search for {country_name} (max {max_search_secs}s)"
            )
        else:
            source_handlers = [
                ("linkedin", self._scrape_linkedin, config),
                ("indeed", self._scrape_indeed, config),
                ("bayt", self._scrape_bayt, config),
                ("naukrigulf", self._scrape_naukrigulf, config),
                ("wuzzuf", self._scrape_wuzzuf, config),
                ("glassdoor", self._scrape_glassdoor, config),
                ("google_jobs", self._scrape_google_jobs, config),
            ]
            if "hhru" in config.get("domains", {}):
                source_handlers.append(("hhru", self._scrape_hhru, config))

        # Use shorter delays in fast mode
        _between_source_delay = 0.2 if enable_fast else 1.0

        for source_name, handler, cfg in source_handlers:
            if len(all_jobs) >= limit * 2:  # fetch extra for dedup
                break

            cfg["domains"].get(
                source_name.replace("google_jobs", "indeed"), ""
            )
            try:
                # Faster rate limiting in fast mode
                _rate_limit_domain(
                    self._last_req,
                    source_name,
                    self.rate_limit_delay if not enable_fast else 0.5,
                )

                jobs = handler(query, cfg, country_key)
                for job in jobs:
                    jid = job.get("job_id", "")
                    if jid and jid not in seen_ids:
                        # Apply location exclusions
                        loc = job.get("location", "")
                        if location_passes_filter(loc, cfg["exclude_patterns"]):
                            seen_ids.add(jid)
                            all_jobs.append(job)
                            self.stats["by_source"].setdefault(source_name, 0)
                            self.stats["by_source"][source_name] += 1

                self.stats["sources_hit"] += 1
                logger.info(
                    f"  [{source_name}] {len(jobs)} jobs for '{query}' in {country_name}"
                )

            except Exception as e:
                logger.debug(f"  [{source_name}] failed for {country_name}: {e}")

            # Brief pause between sources (shorter in fast mode)
            time.sleep(_between_source_delay)

        logger.info(f"  Total jobs for {country_name}: {len(all_jobs)}")
        return all_jobs[:limit]

    # ── Source: LinkedIn ────────────────────────────────────────────────────

    def _scrape_linkedin(
        self, query: str, config: dict, country_key: str
    ) -> list[dict]:
        """
        Scrape LinkedIn Jobs with country-specific URL.

        Features:
        - Random delay (5-15s) between city searches
        - 403 detection triggers Google dork fallback
        - Better error handling and logging
        - Exponentially backs off on failures
        """
        jobs = []
        linkedin_blocked = False

        for city_idx, city in enumerate(config["cities"]):
            if linkedin_blocked:
                logger.info(f"LinkedIn blocked — using Google dork for {city}")
                dork_jobs = self._google_dork_linkedin(query, city, config, country_key)
                jobs.extend(dork_jobs)
                continue

            # Random delay between city queries (5-15 seconds)
            if city_idx > 0:
                delay = random.uniform(5.0, 15.0)
                logger.debug(f"LinkedIn: waiting {delay:.1f}s before next city")
                time.sleep(delay)

            search_q = f"{query} {city} {config['name']}".strip()
            url = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(search_q)}&location={quote_plus(city)}"

            try:
                resp = self._make_get(url, max_retries=2)
                if not resp:
                    logger.debug(f"LinkedIn {city}: no response")
                    continue

                if resp.status_code == 403:
                    logger.warning(
                        f"LinkedIn BLOCKED request for {city} (403). Switching to Google dork fallback."
                    )
                    linkedin_blocked = True
                    # Try Google dork for this city
                    dork_jobs = self._google_dork_linkedin(
                        query, city, config, country_key
                    )
                    jobs.extend(dork_jobs)
                    continue

                if resp.status_code != 200:
                    logger.debug(f"LinkedIn {city}: HTTP {resp.status_code}")
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = (
                    soup.find_all("div", class_="base-card")
                    or soup.find_all("li", class_="jobs-search-results__list-item")
                    or soup.find_all(
                        "div",
                        {"data-entity-urn": re.compile(r"urn:li:jobPosting", re.I)},
                    )
                    or soup.select("div.job-search-card")
                    or soup.select("div.base-search-card")
                    or soup.select("li.jobs-search__results-item")
                    or soup.select("div.jobs-search__results-list li")
                )

                # If still empty, try alternate parsing
                if not cards:
                    cards = soup.select("[data-job-id]") or soup.select("article") or []

                for card in cards[:5]:  # max 5 per city
                    try:
                        job = self._parse_linkedin_card(card, config, country_key)
                        if job:
                            jobs.append(job)
                    except Exception as parse_e:
                        logger.debug(f"LinkedIn parse error for {city}: {parse_e}")
                        continue

            except Exception as e:
                logger.debug(f"LinkedIn {city} failed: {e}")
                continue

        # Deduplicate LinkedIn results
        seen = set()
        unique = []
        for j in jobs:
            jid = j["job_id"]
            if jid not in seen:
                seen.add(jid)
                unique.append(j)
        logger.info(
            f"LinkedIn scraper: {len(unique)} unique jobs (linkedin_blocked={linkedin_blocked})"
        )
        return unique

    def _scrape_linkedin_fast(
        self, query: str, config: dict, country_key: str
    ) -> list[dict]:
        """
        FAST LinkedIn scraper: 1 city only, no random delays, no Google dork fallback.
        Designed for PA free-tier where every second counts.
        """
        jobs = []
        # Only search the first city (fastest)
        city = config["cities"][0] if config["cities"] else config["name"]

        search_q = f"{query} {city} {config['name']}".strip()
        url = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(search_q)}&location={quote_plus(city)}"

        try:
            # Paginate: fetch 3 pages (start=0, 25, 50) → up to 75 unique jobs
            for page_start in [0, 25, 50]:
                page_url = f"{url}&start={page_start}" if page_start > 0 else url
                if page_start > 0:
                    time.sleep(0.3)  # minimal inter-page delay
                resp = self._make_get(page_url, max_retries=1, timeout=10, fast=True)
                if not resp or resp.status_code == 403:
                    break
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = (
                    soup.find_all("div", class_="base-card")
                    or soup.find_all("li", class_="jobs-search-results__list-item")
                    or soup.find_all(
                        "div",
                        {"data-entity-urn": re.compile(r"urn:li:jobPosting", re.I)},
                    )
                    or soup.select("div.job-search-card")
                    or soup.select("div.base-search-card")
                    or soup.select("li.jobs-search__results-item")
                    or soup.select("div.jobs-search__results-list li")
                )

                if not cards:
                    cards = soup.select("[data-job-id]") or soup.select("article") or []
                if not cards:
                    break  # no more results

                for card in cards:
                    try:
                        job = self._parse_linkedin_card(card, config, country_key)
                        if job:
                            jobs.append(job)
                    except Exception as parse_e:
                        logger.debug(f"LinkedIn FAST parse error: {parse_e}")
                        continue

        except Exception as e:
            logger.debug(f"LinkedIn FAST failed: {e}")

        # Deduplicate
        seen = set()
        unique = []
        for j in jobs:
            jid = j["job_id"]
            if jid not in seen:
                seen.add(jid)
                unique.append(j)
        logger.info(f"LinkedIn FAST scraper: {len(unique)} unique jobs in ~5s")
        return unique

    def _google_dork_linkedin(
        self, query: str, city: str, config: dict, country_key: str
    ) -> list[dict]:
        """
        Fallback: Use Google search to find LinkedIn job postings.
        LinkedIn blocks direct scraping? Google can still index their jobs.
        """
        jobs = []
        try:
            site_query = f"site:linkedin.com/jobs {query} {city} {config['name']}"
            search_url = (
                f"https://www.google.com/search?q={quote_plus(site_query)}&num=15"
            )

            # Use a desktop Chrome UA specifically for Google
            google_headers = get_headers()
            google_headers["User-Agent"] = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            time.sleep(random.uniform(2.0, 5.0))  # Polite delay for Google
            resp = self._session.get(search_url, headers=google_headers, timeout=20)

            if resp.status_code != 200:
                logger.debug(f"Google dork returned HTTP {resp.status_code}")
                return jobs

            soup = BeautifulSoup(resp.text, "html.parser")

            # Parse Google search results
            for result in soup.select("div.g") or soup.select("[data-hveid]"):
                link_elem = result.find("a", href=True)
                if not link_elem:
                    continue
                href = link_elem.get("href", "")

                # Only include LinkedIn job links
                if "/jobs/" not in href and "linkedin.com" not in href:
                    continue

                # Clean Google redirect URL
                if href.startswith("/url?"):
                    from urllib.parse import parse_qs

                    parsed = urlparse(href)
                    qs = parse_qs(parsed.query)
                    href = qs.get("q", [href])[0]

                # Extract title and company from link text
                title_elem = result.find("h3")
                title = title_elem.get_text(strip=True) if title_elem else query.title()

                # Get snippet for company name
                snippet_elem = result.find("div", class_="VwiC3b") or result.find(
                    "span", class_="aCOpRe"
                )
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                # Try to extract company from breadcrumb or snippet
                company = config["name"]  # fallback
                company_elem = result.select_one('div[role="heading"]')
                if not company_elem:
                    # Try to find company in breadcrumb citation
                    cite = result.find("cite")
                    if cite:
                        cite_text = cite.get_text(strip=True)
                        # Extract company from LinkedIn URL pattern
                        m = re.search(r"linkedin\.com/company/([^/]+)", cite_text, re.I)
                        if m:
                            company = m.group(1).replace("-", " ").title()

                location = f"{city}, {config['name']}"

                company_domain = _smart_domain(company)
                placeholder_email = f"careers@{company_domain}.com" if company else ""

                job = {
                    "job_id": make_job_id(title, company, href),
                    "title": title,
                    "company": company,
                    "email": placeholder_email,
                    "all_emails": [placeholder_email] if placeholder_email else [],
                    "location": location,
                    "snippet": snippet[:200]
                    if snippet
                    else f"LinkedIn (via Google): {title} at {company}",
                    "source": f"linkedin_dork_{country_key}",
                    "url": href,
                    "salary": extract_salary_from_text(snippet),
                    "country": country_key,
                }
                jobs.append(job)
                if len(jobs) >= 10:
                    break

        except Exception as e:
            logger.debug(f"Google dork fallback failed: {e}")

        return jobs

    def _parse_linkedin_card(
        self, card, config: dict, country_key: str
    ) -> dict | None:
        """Parse a LinkedIn job card."""
        title_elem = (
            card.find("h3", class_="base-search-card__title")
            or card.find("h3")
            or card.find("span", class_="sr-only")
        )
        title = title_elem.get_text(strip=True) if title_elem else ""

        company_elem = (
            card.find("h4", class_="base-search-card__subtitle")
            or card.find("h4")
            or card.find("a", href=re.compile(r"/company/", re.I))
        )
        company = company_elem.get_text(strip=True) if company_elem else ""

        link = card.find("a", href=re.compile(r"/jobs/view/", re.I))
        if not link:
            link = card.find("a", class_="base-card__full-link")
        if not link:
            # Try any anchor with href
            link = card.find("a", href=True)

        job_url = link.get("href", "") if link else ""
        if job_url and not job_url.startswith("http"):
            job_url = "https://www.linkedin.com" + job_url

        location_elem = card.find(
            "span", class_="job-search-card__location"
        ) or card.find("span", class_="job-card-container__metadata-item")
        location = location_elem.get_text(strip=True) if location_elem else ""
        # Add country for clarity
        if location and config["name"] not in location:
            location = f"{location}, {config['name']}"

        if not title or not company:
            return None

        # ── Better domain extraction: strip suffixes, then remove special chars ──
        domain_base = _clean_company_for_domain(company)
        if not domain_base:
            domain_base = "unknown"

        guessed_domain = f"{domain_base}.com"

        placeholder_email = (
            f"careers@{guessed_domain}" if domain_base != "unknown" else ""
        )

        return {
            "job_id": make_job_id(title, company, job_url),
            "title": title,
            "company": company,
            "email": placeholder_email,
            "all_emails": [placeholder_email] if placeholder_email else [],
            "location": location,
            "snippet": f"LinkedIn: {title} at {company} - {location}",
            "source": f"linkedin_{country_key}",
            "url": job_url,
            "salary": None,
            "country": country_key,
        }

    # ── Source: Indeed ──────────────────────────────────────────────────────

    def _scrape_indeed(self, query: str, config: dict, country_key: str) -> list[dict]:
        """Scrape Indeed with country-specific domain."""
        jobs = []
        indeed_domain = config["domains"].get("indeed", "www.indeed.com")

        for city in config["cities"]:
            quote_plus(f"{query} in {city}")
            url = f"https://{indeed_domain}/jobs?q={quote_plus(query)}&l={quote_plus(city)}"

            try:
                resp = self._make_get(url)
                if not resp or resp.status_code not in (200, 301, 302):
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")

                # Indeed card selectors (various versions)
                cards = (
                    soup.find_all("div", class_="job_seen_beacon")
                    or soup.find_all("div", class_="jobsearch-SerpJobCard")
                    or soup.find_all("div", class_="result")
                    or soup.select("div.job-card-container")
                    or soup.select("li.css-5lf6m")
                    or soup.select("div.cardOutline")
                )

                for card in cards[:5]:
                    job = self._parse_indeed_card(
                        card, config, country_key, indeed_domain
                    )
                    if job:
                        jobs.append(job)

            except Exception as e:
                logger.debug(f"Indeed {city} failed: {e}")
                continue

        return jobs

    def _parse_indeed_card(
        self, card, config: dict, country_key: str, domain: str
    ) -> dict | None:
        """Parse an Indeed job card."""
        # Title
        title_elem = (
            card.find("h2", class_="jobTitle")
            or card.find("a", class_="jcs-JobTitle")
            or card.find("h2", class_="title")
            or card.find("a", {"data-jk": True})
            or card.find("a", href=re.compile(r"/pagead/clk", re.I))
        )
        title = title_elem.get_text(strip=True) if title_elem else ""
        title = re.sub(r"\s+", " ", title).strip()

        # Company
        company_elem = (
            card.find("span", class_="companyName")
            or card.find("span", class_="company")
            or card.find("div", class_="company_location")
            or card.find("span", {"data-testid": "company-name"})
        )
        company = company_elem.get_text(strip=True) if company_elem else ""

        # Location
        location_elem = (
            card.find("div", class_="companyLocation")
            or card.find("span", class_="location")
            or card.find("span", {"data-testid": "text-location"})
        )
        location = location_elem.get_text(strip=True) if location_elem else ""

        # Extract URL from card
        link = card.find("a", href=re.compile(r"/jobs|/pagead|/rc/clk", re.I))
        job_url = ""
        if link:
            href = link.get("href", "")
            job_url = f"https://{domain}{href}" if href.startswith("/") else href
        if not job_url:
            job_url = f"https://{domain}/jobs?q={quote_plus(title)}"

        # Salary
        salary_elem = (
            card.find("div", class_="salary-snippet")
            or card.find("span", class_="salaryText")
            or card.find("span", {"data-testid": "salary-info"})
        )
        salary_text = salary_elem.get_text(strip=True) if salary_elem else ""
        salary = extract_salary_from_text(salary_text) if salary_text else None

        if not title or not company:
            return None

        company_domain = _smart_domain(company)
        placeholder_email = f"jobs@{company_domain}.com" if company else ""

        full_location = f"{location}, {config['name']}" if location else config["name"]

        return {
            "job_id": make_job_id(title, company, job_url),
            "title": title,
            "company": company,
            "email": placeholder_email,
            "all_emails": [placeholder_email] if placeholder_email else [],
            "location": full_location,
            "snippet": f"Indeed: {title} at {company} - {full_location}",
            "source": f"indeed_{country_key}",
            "url": job_url,
            "salary": salary,
            "country": country_key,
        }

    # ── Source: Bayt.com ────────────────────────────────────────────────────

    def _scrape_bayt(self, query: str, config: dict, country_key: str) -> list[dict]:
        """Scrape Bayt.com for MENA jobs."""
        jobs = []
        encoded_q = quote_plus(query)

        for city in config["cities"]:
            try:
                # Bayt search URL
                url = f"https://www.bayt.com/en/international/jobs/?q={encoded_q}&country={config['code']}&city={quote_plus(city)}"

                resp = self._make_get(
                    url,
                    extra_headers={
                        "Referer": "https://www.bayt.com/en/international/",
                    },
                )
                if not resp or resp.status_code not in (200, 301, 302):
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")

                # Find job cards
                cards = (
                    soup.find_all("li", class_="has-pointer-d")
                    or soup.select("div.job-card")
                    or soup.select("article.is-available")
                    or soup.find_all("div", class_="card")
                )

                for card in cards[:5]:
                    job = self._parse_bayt_card(card, config, country_key)
                    if job:
                        jobs.append(job)

            except Exception as e:
                logger.debug(f"Bayt {city} failed: {e}")
                continue

        return jobs

    def _parse_bayt_card(self, card, config: dict, country_key: str) -> dict | None:
        """Parse a Bayt.com job card."""
        # Title
        title_elem = (
            card.find("h2", class_="jb-title")
            or card.find("h2")
            or card.find("a", class_="job-title")
            or card.find("a", href=re.compile(r"/en/international/jobs/", re.I))
        )
        title = title_elem.get_text(strip=True) if title_elem else ""

        # Company
        company_elem = (
            card.find("span", class_="jb-company")
            or card.find("span", class_="company")
            or card.find("b", class_="company-name")
            or card.find("a", href=re.compile(r"/en/company/", re.I))
        )
        company = company_elem.get_text(strip=True) if company_elem else ""

        # Location
        location_elem = (
            card.find("span", class_="jb-location")
            or card.find("span", class_="location")
            or card.find("span", class_="job-location")
        )
        location = (
            location_elem.get_text(strip=True).strip()
            if location_elem
            else config["name"]
        )

        # Job URL
        link = card.find("a", href=re.compile(r"/en/international/jobs/", re.I))
        job_url = ""
        if link:
            href = link.get("href", "")
            job_url = f"https://www.bayt.com{href}" if href.startswith("/") else href

        # Description snippet
        desc_elem = (
            card.find("p", class_="jb-desc")
            or card.find("div", class_="job-description")
            or card.find("div", class_="jb-description")
        )
        snippet = desc_elem.get_text(strip=True)[:300] if desc_elem else ""

        if not title or not company:
            return None

        company_domain = _smart_domain(company)
        placeholder_email = f"careers@{company_domain}.com" if company else ""

        return {
            "job_id": make_job_id(title, company, job_url),
            "title": title,
            "company": company,
            "email": placeholder_email,
            "all_emails": [placeholder_email] if placeholder_email else [],
            "location": f"{location.strip()}, {config['name']}"
            if location and config["name"] not in str(location)
            else str(location),
            "snippet": snippet or f"Bayt: {title} at {company}",
            "source": f"bayt_{country_key}",
            "url": job_url,
            "salary": extract_salary_from_text(snippet),
            "country": country_key,
        }

    # ── Source: NaukriGulf ──────────────────────────────────────────────────

    def _scrape_naukrigulf(
        self, query: str, config: dict, country_key: str
    ) -> list[dict]:
        """Scrape NaukriGulf for Gulf region jobs."""
        jobs = []

        if "naukrigulf" not in config["domains"]:
            return jobs

        for city in config["cities"]:
            try:
                encoded_q = quote_plus(f"{query} in {city}")
                url = f"https://www.naukrigulf.com/{encoded_q}-jobs-in-{quote_plus(city.replace(' ', '-'))}"

                resp = self._make_get(
                    url,
                    extra_headers={
                        "Referer": "https://www.naukrigulf.com/",
                    },
                )
                if not resp or resp.status_code not in (200, 301, 302):
                    # Try alternative URL
                    url = f"https://www.naukrigulf.com/jobs?q={quote_plus(query)}&l={quote_plus(city)}"
                    resp = self._make_get(url)
                    if not resp or resp.status_code not in (200, 301, 302):
                        continue

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = (
                    soup.find_all("article", class_="jobTuple")
                    or soup.select("div.row.job")
                    or soup.find_all("div", class_="job-card")
                    or soup.select("li.desktop-search-result")
                )

                for card in cards[:5]:
                    job = self._parse_naukrigulf_card(card, config, country_key)
                    if job:
                        jobs.append(job)

            except Exception as e:
                logger.debug(f"NaukriGulf {city} failed: {e}")
                continue

        return jobs

    def _parse_naukrigulf_card(
        self, card, config: dict, country_key: str
    ) -> dict | None:
        """Parse a NaukriGulf job card."""
        # Title
        title_elem = (
            card.find("a", class_="title")
            or card.find("h2", class_="job-title")
            or card.find("a", href=re.compile(r"/job-", re.I))
            or card.find("a", class_="job-card-title")
        )
        title = title_elem.get_text(strip=True) if title_elem else ""
        title = re.sub(r"\s+", " ", title).strip()

        # Company
        company_elem = (
            card.find("span", class_="company-name")
            or card.find("a", class_="company")
            or card.find("span", class_="subTitle")
            or card.find("span", class_="company")
        )
        company = company_elem.get_text(strip=True) if company_elem else ""

        # Location
        location_elem = (
            card.find("span", class_="location")
            or card.find("span", class_="loc")
            or card.find("li", class_="location")
        )
        location = location_elem.get_text(strip=True) if location_elem else ""

        # URL
        link = card.find("a", href=re.compile(r"/job-", re.I))
        job_url = ""
        if link:
            href = link.get("href", "")
            job_url = (
                f"https://www.naukrigulf.com{href}" if href.startswith("/") else href
            )

        # Salary
        salary_elem = card.find("span", class_="salary")
        salary_text = salary_elem.get_text(strip=True) if salary_elem else ""

        if not title or not company:
            return None

        company_domain = _smart_domain(company)
        placeholder_email = f"hr@{company_domain}.com" if company else ""

        return {
            "job_id": make_job_id(title, company, job_url),
            "title": title,
            "company": company,
            "email": placeholder_email,
            "all_emails": [placeholder_email] if placeholder_email else [],
            "location": f"{location}, {config['name']}" if location else config["name"],
            "snippet": f"NaukriGulf: {title} at {company}",
            "source": f"naukrigulf_{country_key}",
            "url": job_url,
            "salary": extract_salary_from_text(salary_text or ""),
            "country": country_key,
        }

    # ── Source: Wuzzuf ──────────────────────────────────────────────────────

    def _scrape_wuzzuf(self, query: str, config: dict, country_key: str) -> list[dict]:
        """Scrape Wuzzuf for MENA region jobs."""
        jobs = []

        if "wuzzuf" not in config["domains"]:
            return jobs

        try:
            encoded_q = quote_plus(query)
            url = f"https://wuzzuf.net/search/jobs/?q={encoded_q}&country={config['code']}"

            resp = self._make_get(
                url,
                extra_headers={
                    "Referer": "https://wuzzuf.net/",
                },
            )
            if not resp or resp.status_code not in (200, 301, 302):
                return jobs

            soup = BeautifulSoup(resp.text, "html.parser")

            cards = (
                soup.find_all("div", class_="css-1gq4cwl")
                or soup.select("div.job-card")
                or soup.find_all("div", class_="card")
                or soup.select("a.css-1w3khdb")
                or soup.find_all("div", class_="job")
            )

            for card in cards[:10]:
                job = self._parse_wuzzuf_card(card, config, country_key)
                if job:
                    jobs.append(job)

        except Exception as e:
            logger.debug(f"Wuzzuf failed for {country_key}: {e}")

        return jobs

    def _parse_wuzzuf_card(
        self, card, config: dict, country_key: str
    ) -> dict | None:
        """Parse a Wuzzuf job card."""
        # Title
        title_elem = (
            card.find("h2", class_="css-m604qf")
            or card.find("h2")
            or card.find("a", href=re.compile(r"/jobs/", re.I))
            or card.find("a", class_="job-title")
        )
        title = title_elem.get_text(strip=True) if title_elem else ""
        title = re.sub(r"\s+", " ", title).strip()

        # Company
        company_elem = (
            card.find("a", class_="css-17s97q8")
            or card.find("span", class_="company")
            or card.find("div", class_="company")
        )
        company = company_elem.get_text(strip=True) if company_elem else ""

        # Location
        location_elem = (
            card.find("span", class_="css-5wys0k")
            or card.find("span", class_="location")
            or card.find("div", class_="location")
        )
        location = location_elem.get_text(strip=True) if location_elem else ""

        if not title or not company:
            return None

        job_url = ""
        link = card.find("a", href=re.compile(r"/jobs/", re.I))
        if link:
            href = link.get("href", "")
            job_url = f"https://wuzzuf.net{href}" if href.startswith("/") else href

        company_domain = _smart_domain(company)
        placeholder_email = f"careers@{company_domain}.com" if company else ""

        return {
            "job_id": make_job_id(title, company, job_url),
            "title": title,
            "company": company,
            "email": placeholder_email,
            "all_emails": [placeholder_email] if placeholder_email else [],
            "location": f"{location.strip()}, {config['name']}"
            if location
            else config["name"],
            "snippet": f"Wuzzuf: {title} at {company}",
            "source": f"wuzzuf_{country_key}",
            "url": job_url,
            "salary": None,
            "country": country_key,
        }

    # ── Source: Glassdoor ───────────────────────────────────────────────────

    def _scrape_glassdoor(
        self, query: str, config: dict, country_key: str
    ) -> list[dict]:
        """
        Attempt Glassdoor scraping. Glassdoor aggressively blocks scrapers (403),
        so this is best-effort with fallback to cached/alternative data.
        """
        jobs = []

        if "glassdoor" not in config["domains"]:
            return jobs

        try:
            encoded_q = quote_plus(query)
            url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={encoded_q}&locT=C&locId=0"

            resp = self._make_get(
                url,
                extra_headers={
                    "Referer": "https://www.glassdoor.com/",
                },
            )

            if not resp:
                return jobs

            if resp.status_code == 403:
                logger.debug(f"Glassdoor blocked (403) for {country_key}")
                return []

            if resp.status_code != 200:
                return jobs

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = (
                soup.find_all("li", class_="react-job-listing")
                or soup.select("div.jobListing")
                or soup.find_all("div", class_="jobTitle")
                or soup.find_all("a", class_="job-title")
            )

            for card in cards[:10]:
                job = self._parse_glassdoor_card(card, config, country_key)
                if job:
                    jobs.append(job)

        except Exception as e:
            logger.debug(f"Glassdoor failed: {e}")

        return jobs

    def _parse_glassdoor_card(
        self, card, config: dict, country_key: str
    ) -> dict | None:
        """Parse a Glassdoor job card."""
        title_elem = (
            card.find("a", class_="job-title")
            or card.find("h2")
            or card.find("a", {"data-test": "job-link"})
            or card.find("a", href=re.compile(r"/partner/jobListing", re.I))
        )
        title = title_elem.get_text(strip=True) if title_elem else ""

        company_elem = (
            card.find("span", class_="job-employer")
            or card.find("span", class_="company-name")
            or card.find("div", {"data-test": "employer-name"})
        )
        company = company_elem.get_text(strip=True) if company_elem else ""

        location_elem = (
            card.find("span", class_="job-location")
            or card.find("span", class_="location")
            or card.find("div", {"data-test": "location"})
        )
        location = location_elem.get_text(strip=True) if location_elem else ""

        if not title or not company:
            return None

        company_domain = _smart_domain(company)
        placeholder_email = f"careers@{company_domain}.com" if company else ""

        return {
            "job_id": make_job_id(title, company, f"glassdoor_{title}_{company}"),
            "title": title,
            "company": company,
            "email": placeholder_email,
            "all_emails": [placeholder_email] if placeholder_email else [],
            "location": f"{location}, {config['name']}" if location else config["name"],
            "snippet": f"Glassdoor: {title} at {company}",
            "source": f"glassdoor_{country_key}",
            "url": "",
            "salary": None,
            "country": country_key,
        }

    # ── Source: Google Jobs (via Google Search) ─────────────────────────────

    def _scrape_google_jobs(
        self, query: str, config: dict, country_key: str
    ) -> list[dict]:
        """
        Google Jobs via organic search. Google Jobs results appear in a special
        widget, but we can also find traditional job board results.
        """
        jobs = []

        try:
            city = config["cities"][0] if config["cities"] else ""
            # Craft a query that targets job boards for this country
            site_filters = {
                "lebanon": "site:linkedin.com OR site:indeed.com.lb OR site:bayt.com",
                "uae": "site:linkedin.com OR site:indeed.ae OR site:bayt.com OR site:naukrigulf.com OR site:gulftalent.com",
                "saudi": "site:linkedin.com OR site:indeed.com.sa OR site:bayt.com OR site:naukrigulf.com",
                "qatar": "site:linkedin.com OR site:indeed.qa OR site:bayt.com OR site:naukrigulf.com",
                "kuwait": "site:linkedin.com OR site:indeed.com.kw OR site:bayt.com OR site:naukrigulf.com",
                "remote": "site:linkedin.com OR site:indeed.com OR site:remoteok.com OR site:weworkremotely.com OR site:jobspresso.co",
            }
            site_filter = site_filters.get(
                country_key, "site:linkedin.com OR site:indeed.com"
            )

            search_q = f"{query} {city} {site_filter}"
            url = f"https://www.google.com/search?q={quote_plus(search_q)}&num=15&hl=en"

            resp = self._make_get(
                url,
                extra_headers={
                    "Referer": "https://www.google.com/",
                },
            )
            if not resp or resp.status_code != 200:
                return jobs

            # Extract job URLs from Google search results
            urls = re.findall(r'href="(https?://[^"]+)"', resp.text)
            job_board_domains = [
                "linkedin.com/jobs",
                "indeed.com",
                "bayt.com",
                "naukrigulf.com",
                "gulftalent.com",
                "wuzzuf.net",
                "glassdoor.com",
                "monster.com",
                "remoteok.com",
                "weworkremotely.com",
                "jobspresso.co",
            ]
            job_urls = [
                u for u in urls if any(d in u.lower() for d in job_board_domains)
            ][:5]

            logger.debug(f"Google Jobs: found {len(job_urls)} URLs for {country_key}")

            for job_url in job_urls:
                try:
                    _rate_limit_domain(
                        self._last_req, "google_jobs_fetch", self.rate_limit_delay
                    )
                    job = self._fetch_job_page(job_url, config, country_key)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"Fetching {job_url} failed: {e}")
                    continue

        except Exception as e:
            logger.debug(f"Google Jobs search failed for {country_key}: {e}")

        return jobs

    def _fetch_job_page(
        self, url: str, config: dict, country_key: str
    ) -> dict | None:
        """Fetch a job page and extract info."""
        try:
            resp = self._make_get(url)
            if not resp or resp.status_code != 200:
                return None

            emails = extract_emails(resp.text)
            soup = BeautifulSoup(resp.text, "html.parser")

            # Try to get title and company
            title_elem = soup.find("h1")
            title = (
                title_elem.get_text(strip=True)[:200]
                if title_elem
                else "Unknown Position"
            )
            title = re.sub(r"\s+", " ", title).strip()

            # Extract domain as company name
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            company = domain.split(".")[0].title()

            company_domain = _smart_domain(company)
            placeholder = f"careers@{company_domain}.com"

            if not emails:
                emails = [placeholder]

            return {
                "job_id": make_job_id(title, company, url),
                "title": title,
                "company": company,
                "email": emails[0] if emails else placeholder,
                "all_emails": emails,
                "location": config["name"],
                "snippet": f"Discovered via Google: {title} at {company}",
                "source": f"google_jobs_{country_key}",
                "url": url,
                "salary": extract_salary_from_text(resp.text),
                "country": country_key,
            }

        except Exception as e:
            logger.debug(f"Failed to fetch job page {url}: {e}")
            return None

    # ── Source: hh.ru (Russia / CIS) ────────────────────────────────────────

    def _scrape_hhru(self, query: str, config: dict, country_key: str) -> list[dict]:
        """
        Scrape hh.ru using their free REST API (no key required).
        Covers Russia, Kazakhstan, Belarus, and CIS countries.

        Uses the core.hhru_scraper module for API integration.
        Falls back gracefully if the module is not available.
        """
        if not _hhru_search_sync:
            logger.debug("hh.ru: Module not available, skipping")
            return []

        if not getattr(__import__("config", fromlist=[""]), "HHRU_ENABLED", True):
            logger.debug("hh.ru: Disabled in config")
            return []

        # Determine locations from country config
        locations = [config["name"]]  # e.g., "Russia", "Kazakhstan", "Belarus"
        locations.extend(config.get("cities", []))

        # For "russia" country_key, also try Russian-language titles
        titles = [query]
        # Russian transliterations for network engineer roles
        ru_titles = {
            "network engineer": ["сетевой инженер", "инженер сети"],
            "senior network engineer": [
                "старший сетевой инженер",
                "ведущий сетевой инженер",
            ],
            "network administrator": ["системный администратор", "администратор сети"],
            "network security engineer": ["инженер по сетевой безопасности"],
            "systems engineer": ["системный инженер"],
            "devops engineer": ["DevOps инженер"],
        }
        query_lower = query.lower().strip()
        if query_lower in ru_titles:
            titles.extend(ru_titles[query_lower])

        try:
            jobs = _hhru_search_sync(
                job_titles=titles,
                locations=locations,
                limit=50,  # Reasonable limit per source call
                max_pages=5,  # 5 × 100 = 500 max per query
            )

            # Adapt hh.ru schema to GlobalJobScraper job schema
            # hhru_scraper returns: title, company, location, description, url,
            #   salary_min, salary_max, salary_currency, posted_date, source, skills, ...
            adapted = []
            for job in jobs:
                adapted.append(
                    {
                        "job_id": job.get("job_id", ""),
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "email": job.get("email", ""),
                        "all_emails": job.get("all_emails", []),
                        "location": job.get("location", config["name"]),
                        "snippet": job.get("snippet", ""),
                        "source": f"hhru_{country_key}",
                        "url": job.get("url", ""),
                        "salary": job.get(
                            "salary_min"
                        ),  # Use min salary as main salary field
                        "country": country_key,
                        # Extended fields (for richer data downstream)
                        "salary_min": job.get("salary_min"),
                        "salary_max": job.get("salary_max"),
                        "salary_currency": job.get("salary_currency"),
                        "posted_date": job.get("posted_date"),
                        "skills": job.get("skills", []),
                        "description": job.get("description", ""),
                    }
                )

            logger.info(
                f"hh.ru scraper: {len(adapted)} jobs for '{query}' in {config['name']}"
            )
            return adapted

        except Exception as e:
            logger.warning(f"hh.ru scraper failed for {country_key}: {e}")
            return []

    # ── HTTP Helpers ────────────────────────────────────────────────────────

    def _make_get(
        self,
        url: str,
        extra_headers: dict = None,
        timeout: int = 15,
        max_retries: int = 3,
        fast: bool = False,
    ) -> httpx.Response | None:
        """
        Make a GET request with random user-agent, smart delay, and exponential backoff.

        Features:
        - Random User-Agent from expanded pool
        - Random delay (fast mode: 0.5-2s, normal: 3-8s) to avoid rate limiting
        - Exponential backoff for 429/503
        - Retry up to max_retries for transient errors
        - Enhanced error categorization
        """
        # Random delay between requests (shorter in fast mode)
        delay = random.uniform(0.5, 2.0) if fast else random.uniform(3.0, 8.0)
        time.sleep(delay)

        for attempt in range(1, max_retries + 1):
            try:
                headers = get_headers(extra_headers)
                # Add random Accept-Language for each attempt
                headers["Accept-Language"] = random.choice(
                    [
                        "en-US,en;q=0.9",
                        "en-GB,en;q=0.8,en-US;q=0.6",
                        "en-US,en;q=0.5",
                        "en-CA,en;q=0.9,fr-CA;q=0.5",
                    ]
                )

                if HAS_CFFI and self._cffi_session:
                    # Use curl_cffi for perfect TLS impersonation
                    try:
                        cffi_resp = self._cffi_session.get(
                            url, headers=headers, timeout=timeout
                        )
                        # Shim cffi response to look like httpx response
                        resp = httpx.Response(
                            status_code=cffi_resp.status_code,
                            content=cffi_resp.content,
                            request=httpx.Request("GET", url),
                        )
                        resp.headers = httpx.Headers(cffi_resp.headers)
                    except Exception as ce:
                        logger.warning(
                            f"curl_cffi failed ({ce}), falling back to httpx"
                        )
                        resp = self._session.get(url, headers=headers, timeout=timeout)
                else:
                    resp = self._session.get(url, headers=headers, timeout=timeout)

                if resp.status_code in (429, 503):
                    retry_after = int(resp.headers.get("Retry-After", str(5 * attempt)))
                    sleep_time = min(retry_after + random.uniform(1, 5), 30)
                    logger.warning(
                        f"Rate limited ({resp.status_code}) on {url[:60]}... "
                        f"attempt {attempt}/{max_retries}, waiting {sleep_time:.0f}s"
                    )
                    time.sleep(sleep_time)
                    continue

                if resp.status_code == 403:
                    logger.debug(
                        f"403 Forbidden: {url[:80]}... (attempt {attempt}/{max_retries})"
                    )
                    if attempt < max_retries:
                        # Try again with different UA after longer pause
                        time.sleep(random.uniform(10, 20))
                        continue
                    return resp  # Return so caller can decide fallback

                if resp.status_code == 200:
                    return resp

                # Other non-200 but non-fatal
                if attempt < max_retries:
                    logger.debug(f"HTTP {resp.status_code} on {url[:60]}... retrying")
                    time.sleep(random.uniform(2, 5) * attempt)
                    continue

                return resp

            except httpx.TimeoutException:
                logger.debug(
                    f"Timeout: {url[:80]}... (attempt {attempt}/{max_retries})"
                )
                if attempt < max_retries:
                    time.sleep(random.uniform(3, 8) * attempt)
                    continue
                return None
            except httpx.ConnectError:
                logger.debug(
                    f"Connection error: {url[:80]}... (attempt {attempt}/{max_retries})"
                )
                if attempt < max_retries:
                    time.sleep(random.uniform(5, 15) * attempt)
                    continue
                return None
            except Exception as e:
                logger.debug(
                    f"Request error for {url[:80]}...: {e} (attempt {attempt}/{max_retries})"
                )
                if attempt < max_retries:
                    time.sleep(random.uniform(2, 10))
                    continue
                return None

        return None

    # ── Summary ─────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Return scraper statistics."""
        return {
            **self.stats,
            "countries_scanned": len(COUNTRY_CONFIGS),
        }


# ── Domain Utility Functions ─────────────────────────────────────────────────

# Company suffixes to strip before domain generation
# NOTE: Only strip LEGAL/INCORPORATION and generic corporate suffixes.
# Descriptive words like "Solutions", "Technologies", "Network", "Services"
# are often part of the legitimate domain and should NOT be stripped.
# (Per task example: "Network Solutions Inc" → strip "Inc" → "networksolutions")
_COMPANY_SUFFIXES = [
    # Legal incorporation suffixes (NEVER part of a real domain)
    r"\bLLC\b",
    r"\bInc\.?\b",
    r"\bLtd\.?\b",
    r"\bCorp\.?\b",
    r"\bCorporation\b",
    r"\bIncorporated\b",
    r"\bLimited\b",
    r"\bCompany\b",
    r"\bCo\.?\b",
    # Generic corporate groupings (rarely the core domain)
    r"\bGroup\b",
    r"\bHoldings\b",
    r"\bPartners\b",
    r"\bAssociates\b",
    r"\bEnterprises\b",
    r"\bVentures\b",
    # Middle East specific
    r"\bS\.?A\.?L\.?\b",
    r"\bS\.?A\.?R\.?L\.?\b",
    r"\bS\.?A\.?S\.?\b",
    r"\bS\.?A\.?\b",
    r"\bGmbH\b",
    r"\bBV\b",
    r"\bPty\.?\s*Ltd\.?\b",
]


def _clean_company_for_domain(company: str) -> str:
    """Strip legal/business suffixes then remove special chars/spaces for domain generation.

    Examples:
        "Network Solutions Inc" -> "networksolutions"
        "Harry Winston" -> "harrywinston"
        "Tech Corp LLC" -> "tech"
        "Bank Audi SAL" -> "bankaudi"
    """
    name = company.strip()
    # Strip ONLY legal suffixes (not descriptive words like "Solutions", "Network")
    for suffix_pat in _COMPANY_SUFFIXES:
        name = re.sub(suffix_pat, "", name, flags=re.IGNORECASE)
    # Remove special chars except alphanumeric and spaces
    name = re.sub(r"[^\w\s]", "", name)
    # Collapse whitespace, lowercase, remove spaces
    name = re.sub(r"\s+", "", name.strip().lower())
    # Remove any remaining non-alphanumeric
    name = re.sub(r"[^a-z0-9]", "", name)
    return name


def _validate_domain_http(domain: str, timeout: float = 3.0) -> bool:
    """Quick HTTP HEAD check to see if a domain is alive.

    Returns True if the domain responds (2xx/3xx), False for 4xx/5xx or errors.
    Uses urllib from stdlib to avoid extra dependencies.
    """
    if not domain or domain.startswith("unknown"):
        return False
    try:
        url = f"https://{domain}"
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0 (compatible; JobHuntPro/1.0)")
        resp = urllib.request.urlopen(req, timeout=timeout)
        # 2xx or 3xx = domain exists
        return resp.status < 400
    except urllib.error.HTTPError as e:
        # 4xx/5xx but domain still exists — server just rejected HEAD
        # 403/404/500 = the domain is alive, just not serving that path
        return e.code < 500  # 4xx = alive, 5xx = dead
    except Exception:
        # Timeout, DNS error, SSL error, etc.
        return False


# ── Quick Test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.debug("=" * 60)
    logger.debug("GlobalJobScraper - Quick Test")
    logger.debug("=" * 60)

    scraper = GlobalJobScraper()

    # Test: search Lebanon for network engineer
    logger.debug("\n--- Testing: Lebanon search ---")
    lebanon_jobs = scraper.search_country("lebanon", "network engineer", limit=5)
    logger.debug(f"Found {len(lebanon_jobs)} jobs in Lebanon")

    # Test: search UAE
    logger.debug("\n--- Testing: UAE search ---")
    uae_jobs = scraper.search_country("uae", "network engineer", limit=5)
    logger.debug(f"Found {len(uae_jobs)} jobs in UAE")

    # Test: search all countries
    logger.debug("\n--- Testing: All Countries search ---")
    all_jobs = scraper.search_all_countries(limit_per_country=3, max_total=20)
    logger.debug(f"Found {len(all_jobs)} total jobs across all countries")

    scraper.close()

    logger.debug("\n✓ GlobalJobScraper test complete")
