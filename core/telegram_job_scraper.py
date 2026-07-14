"""
JobHunt Pro v17.1 — Telegram Job Channels Scraper
Scrapes job postings from public Telegram channels/groups worldwide.
Zero investment — uses public Telegram web views and t.me RSS feeds.
"""

import hashlib
import logging
import random
import re
import time

try:
    from curl_cffi.requests import AsyncSession as httpx_AsyncClient
except ImportError:
    import httpx

    httpx_AsyncClient = httpx.AsyncClient
import contextlib

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Public Telegram Job Channels (worldwide, by region) ──────────
TELEGRAM_JOB_CHANNELS = {
    # 🌍 Global / Remote
    "global": [
        "remoteokjobs",
        "remote_jobs",
        "wfh_jobs",
        "workfromhomejobs",
        "remoteworker",
        "digitalnomadjobs",
        "global_jobs",
        "remote4dev",
        "freelance_jobs",
        "onlinejobs",
        "worldwide_jobs",
    ],
    # 🇺🇸 USA / Canada
    "north_america": [
        "usajobs",
        "techjobsusa",
        "itjobsusa",
        "canadajobs",
        "us_jobs_alerts",
        "nyc_jobs",
        "sf_jobs",
        "siliconvalleyjobs",
    ],
    # 🇪🇺 Europe
    "europe": [
        "europeremotejobs",
        "ukjobs",
        "germanyjobs",
        "netherlandsjobs",
        "irelandjobs",
        "polandjobs",
        "spainjobs",
        "portugaljobs",
        "switzerlandjobs",
        "swedenjobs",
        "norwayjobs",
        "denmarkjobs",
        "francejobs",
        "italyjobs",
        "austriajobs",
        "belgiumjobs",
        "czechjobs",
        "romaniajobs",
        "hungaryjobs",
        "greecejobs",
    ],
    # 🇷🇺 Russia / CIS
    "cis": [
        "russiajobs",
        "it_vacancies_ru",
        "moscowjobs",
        "spbjobs",
        "kazakhstanjobs",
        "belarusjobs",
        "ukrainejobs",
        "remote_cis",
        "cis_it_jobs",
    ],
    # 🇮🇳 India / South Asia
    "south_asia": [
        "indiajobs",
        "itjobsindia",
        "bangalorejobs",
        "mumbaijobs",
        "delhijobs",
        "hyderabadjobs",
        "chennaijobs",
        "punejobs",
        "srilankajobs",
        "pakistanjobs",
        "bangladeshjobs",
    ],
    # 🌏 Asia Pacific
    "asia_pacific": [
        "singaporejobs",
        "malaysiajobs",
        "indonesiajobs",
        "thailandjobs",
        "vietnamjobs",
        "philippinesjobs",
        "japanjobs",
        "koreajobs",
        "australiajobs",
        "nzjobs",
        "taiwanjobs",
        "hongkongjobs",
        "dubai_jobs",
        "uaejobs",
        "saudijobs",
        "qatarjobs",
    ],
    # 🌍 Africa / Middle East
    "mena_africa": [
        "egyptjobs",
        "moroccojobs",
        "tunisiajobs",
        "algeriajobs",
        "nigeriaremote",
        "kenyajobs",
        "southafricajobs",
        "lebanonjobs",
        "jordanjobs",
        "iraqjobs",
        "gulf_jobs",
        "middleeastjobs",
    ],
    # 💻 Tech-specific
    "tech_specific": [
        "pythonjobs",
        "devops_jobs",
        "networkengineerjobs",
        "cybersecurityjobs",
        "cloudjobs",
        "sre_jobs",
        "backendjobs",
        "frontendjobs",
        "fullstackjobs",
        "sysadminjobs",
        "infrastructure_jobs",
        "it_jobs",
    ],
}

# ── Channel URL templates ────────────────────────────────────────
TGRAM_WEB_URL = "https://t.me/s/{channel}"
TGRAM_RSS_URL = "https://t.me/s/{channel}?before={before}"

# ── Job extraction patterns ──────────────────────────────────────
JOB_TITLE_PATTERNS = [
    r"(?:hiring|we need|looking for|position|vacancy|job opening|urgent)\s*[:\-]?\s*([^\\n]{3,80})",
    r"(Network Engineer|DevOps|SysAdmin|Cloud Engineer|SRE|Infrastructure)",
    r"(Python|Java|Go|Rust|Kubernetes|Docker|AWS|Azure|GCP)",
    r"(Senior|Lead|Principal|Staff|Junior|Mid-level)\s+\w+",
]

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
SALARY_PATTERN = re.compile(
    r"(?:\$|€|£|AED|SAR|QAR)\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K|/yr|/year|/month|/mo)?",
    re.IGNORECASE,
)
LOCATION_PATTERN = re.compile(
    r"(?:location|loc|based in|place|city)[:\s]*([A-Za-z\s,]+?)(?:\n|$|\.)",
    re.IGNORECASE,
)


class TelegramJobScraper:
    """Scrapes job postings from public Telegram channels worldwide."""

    source_name = "telegram"

    def __init__(self, timeout: int = 20, rate_delay: float = 3.0):
        self.timeout = timeout
        self.rate_delay = rate_delay
        self._last_request = 0.0
        self._client = httpx.Client(timeout=timeout, follow_redirects=True)
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36",
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        ]

    def _rate_limit(self):
        now = time.time()
        elapsed = now - self._last_request
        if elapsed < self.rate_delay:
            time.sleep(self.rate_delay - elapsed)
        self._last_request = time.time()

    def _get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(self._user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": random.choice(
                ["en-US,en;q=0.9", "en-GB,en;q=0.9", "en;q=0.9"]
            ),
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def _make_job_id(self, title: str, company: str, channel: str) -> str:
        raw = f"{title.lower().strip()}:{company.lower().strip()}:{channel}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def _extract_company(self, text: str) -> str:
        """Extract company name from message text."""
        patterns = [
            r"(?:at|@|for|with|company)[:\s]*([A-Z][A-Za-z0-9\s&.]+?)(?:\n|$|\.|\s+is\s+)",
            r"^([A-Z][A-Za-z0-9\s&.]+?)(?:\s+(?:is|are|hiring|looking))",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()[:60]
        return "Unknown Company"

    def _extract_title(self, text: str) -> str | None:
        """Extract job title from message text."""
        for pat in JOB_TITLE_PATTERNS:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                title = m.group(1) if m.lastindex and m.group(1) else m.group(0)
                return title.strip()[:80]
        return None

    def _extract_salary(self, text: str) -> float | None:
        m = SALARY_PATTERN.search(text)
        if m:
            try:
                return float(re.sub(r"[,$\s]", "", m.group(1)))
            except ValueError:
                pass
        return None

    def _extract_location(self, text: str) -> str:
        m = LOCATION_PATTERN.search(text)
        if m:
            return m.group(1).strip()[:50]
        # Try to find common location keywords
        locations = re.findall(
            r"\b(Remote|Worldwide|Dubai|London|Berlin|Amsterdam|Singapore|Tokyo|NYC|San Francisco|Austin|Seattle|Toronto|Sydney|Mumbai|Bangalore|Moscow|Riyadh|Cairo)\b",
            text,
            re.IGNORECASE,
        )
        if locations:
            return locations[0]
        return "Remote"

    def _extract_emails(self, text: str) -> list[str]:
        return list(set(EMAIL_PATTERN.findall(text)))

    def _extract_contact(self, text: str) -> str:
        """Extract contact info (Telegram handle or email)."""
        tg_handle = re.search(r"@(\w+)", text)
        if tg_handle:
            return f"https://t.me/{tg_handle.group(1)}"
        emails = self._extract_emails(text)
        if emails:
            return emails[0]
        return ""

    def _parse_message(self, msg_text: str, channel: str) -> dict | None:
        """Parse a single Telegram message into a job dict."""
        if not msg_text or len(msg_text) < 20:
            return None

        title = self._extract_title(msg_text)
        if not title:
            return None

        company = self._extract_company(msg_text)
        location = self._extract_location(msg_text)
        salary = self._extract_salary(msg_text)
        emails = self._extract_emails(msg_text)
        contact = self._extract_contact(msg_text)

        # Build snippet
        snippet = msg_text[:500].replace("\n", " ").strip()

        return {
            "job_id": self._make_job_id(title, company, channel),
            "title": title,
            "company": company,
            "email": emails[0] if emails else contact,
            "all_emails": emails,
            "location": location,
            "snippet": snippet,
            "source": f"telegram/{channel}",
            "url": f"https://t.me/{channel}",
            "salary": salary,
            "contact": contact,
        }

    def scrape_channel(self, channel: str, limit: int = 10) -> list[dict]:
        """Scrape job postings from a single Telegram channel."""
        jobs = []
        try:
            url = TGRAM_WEB_URL.format(channel=channel)
            self._rate_limit()
            headers = self._get_headers()
            resp = self._client.get(url, headers=headers)

            if resp.status_code != 200:
                logger.debug(f"Telegram channel '{channel}': HTTP {resp.status_code}")
                return jobs

            soup = BeautifulSoup(resp.text, "html.parser")
            messages = soup.select(".tgme_widget_message_text") or soup.select(
                ".message-text"
            )

            for msg in messages[: limit * 2]:  # Fetch more, filter later
                text = msg.get_text(strip=True)
                job = self._parse_message(text, channel)
                if job:
                    jobs.append(job)
                    if len(jobs) >= limit:
                        break

            logger.debug(f"Telegram channel '{channel}': {len(jobs)} jobs found")
        except Exception as e:
            logger.debug(f"Telegram channel '{channel}': error: {e}")

        return jobs

    def search(
        self, query: str = "", location: str = "", limit: int = 10
    ) -> list[dict]:
        """Search across all Telegram job channels."""
        all_jobs = []
        query_lower = query.lower() if query else ""

        # Determine which regions to search based on location
        regions_to_search = list(TELEGRAM_JOB_CHANNELS.keys())
        if location:
            location_lower = location.lower()
            # Prioritize region based on location
            region_map = {
                "usa": "north_america",
                "canada": "north_america",
                "us": "north_america",
                "uk": "europe",
                "germany": "europe",
                "france": "europe",
                "russia": "cis",
                "kazakhstan": "cis",
                "india": "south_asia",
                "pakistan": "south_asia",
                "china": "asia_pacific",
                "japan": "asia_pacific",
                "singapore": "asia_pacific",
                "uae": "mena_africa",
                "saudi": "mena_africa",
                "egypt": "mena_africa",
                "remote": "global",
                "worldwide": "global",
            }
            for key, region in region_map.items():
                if key in location_lower:
                    regions_to_search = [region] + [
                        r for r in regions_to_search if r != region
                    ]
                    break

        for region in regions_to_search:
            channels = TELEGRAM_JOB_CHANNELS.get(region, [])
            random.shuffle(channels)  # Rotate channel order

            for channel in channels[:5]:  # Max 5 channels per region per search
                if len(all_jobs) >= limit:
                    break
                channel_jobs = self.scrape_channel(channel, limit=max(3, limit // 5))
                for job in channel_jobs:
                    # Filter by query if provided
                    if query_lower:
                        title_lower = job["title"].lower()
                        snippet_lower = job["snippet"].lower()
                        if (
                            query_lower not in title_lower
                            and query_lower not in snippet_lower
                        ):
                            continue
                    all_jobs.append(job)
                    if len(all_jobs) >= limit:
                        break

            if len(all_jobs) >= limit:
                break

        return all_jobs[:limit]

    def close(self):
        with contextlib.suppress(Exception):
            self._client.close()


# ── Singleton ────────────────────────────────────────────────────
_telegram_scraper: TelegramJobScraper | None = None


def get_telegram_scraper() -> TelegramJobScraper:
    global _telegram_scraper
    if _telegram_scraper is None:
        _telegram_scraper = TelegramJobScraper()
    return _telegram_scraper


def search_telegram_jobs(
    query: str = "", location: str = "", limit: int = 10
) -> list[dict]:
    """Convenience function to search Telegram job channels."""
    scraper = get_telegram_scraper()
    try:
        return scraper.search(query=query, location=location, limit=limit)
    finally:
        scraper.close()


# ── Quick test ───────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    jobs = search_telegram_jobs(query="network engineer", limit=5)
    logger.debug(f"Found {len(jobs)} jobs from Telegram:")
    for j in jobs:
        logger.debug(f"  - {j['title']} @ {j['company']} ({j['location']}) [{j['source']}]")
