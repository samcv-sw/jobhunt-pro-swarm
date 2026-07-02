"""
Indeed RSS Scraper — uses Indeed's public RSS feed (no API key, no blocks)
"""

import re
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict
from urllib.parse import urlencode

try:
    from curl_cffi.requests import AsyncSession as httpx_AsyncClient
except ImportError:
    import httpx

    httpx_AsyncClient = httpx.AsyncClient
import httpx

logger = logging.getLogger(__name__)


class IndeedRSSScraper:
    """Scrapes Indeed via RSS/Atom feed — never gets 403 since it's XML.
    Indeed RSS: https://www.indeed.com/rss?q={query}&l={location}&sort=date
    """

    source_name = "indeed_rss"

    REGION_CODES = {
        "Lebanon": "LB",
        "UAE": "AE",
        "Saudi Arabia": "SA",
        "Qatar": "QA",
        "Kuwait": "KW",
        "Bahrain": "BH",
        "Oman": "OM",
        "Jordan": "JO",
        "Egypt": "EG",
        "Remote": "",
        "default": "",
    }

    def __init__(self, timeout: int = 20):
        self._session = httpx.Client(timeout=timeout, follow_redirects=True)
        self._headers = {
            "User-Agent": "Mozilla/5.0 (compatible; JobHuntBot/1.0)",
            "Accept": "application/rss+xml, application/xml, text/xml",
        }

    def search(self, query: str, location: str = "", limit: int = 20) -> List[Dict]:
        jobs = []
        location_clean = location.strip()

        # Try primary location first
        for loc_try in [location_clean, ""]:  # empty = all locations
            try:
                # Build RSS URL
                params = {"q": query, "sort": "date"}
                if loc_try:
                    params["l"] = loc_try

                url = f"https://www.indeed.com/rss?{urlencode(params)}"
                logger.info(f"[IndeedRSS] Fetching: {url}")

                resp = self._session.get(url, headers=self._headers)
                if resp.status_code != 200:
                    logger.debug(f"[IndeedRSS] status {resp.status_code}")
                    if loc_try:
                        continue
                    break

                # Parse RSS XML
                try:
                    root = ET.fromstring(resp.text)
                except ET.ParseError:
                    logger.debug("[IndeedRSS] Parse error")
                    continue

                # RSS namespace
                ns = {
                    "": "http://purl.org/rss/1.0/",
                    "dc": "http://purl.org/dc/elements/1.1/",
                }

                for item in root.findall(".//item", ns) or root.findall("channel/item"):
                    title = ""
                    company = ""
                    loc = ""
                    link = ""

                    title_elem = item.find("title")
                    if title_elem is not None and title_elem.text:
                        # Parse "Job Title - Company Name" format
                        title_text = title_elem.text.strip()
                        if " - " in title_text:
                            parts = title_text.rsplit(" - ", 1)
                            title = parts[0].strip()
                            company = parts[1].strip()
                        else:
                            title = title_text

                    link_elem = item.find("link")
                    if link_elem is not None and link_elem.text:
                        link = link_elem.text.strip()

                    # Try to extract company from dc:creator
                    creator = item.find("dc:creator", ns) or item.find(
                        "{http://purl.org/dc/elements/1.1/}creator"
                    )
                    if creator is not None and creator.text and not company:
                        company = creator.text.strip()

                    # Location from description
                    desc_elem = item.find("description")
                    snippet = ""
                    if desc_elem is not None and desc_elem.text:
                        snippet = re.sub(r"<[^>]+>", "", desc_elem.text).strip()[:300]
                        loc_match = re.search(r"Location[:\s]+([^\n<]+)", snippet, re.I)
                        if loc_match:
                            loc = loc_match.group(1).strip()

                    if not loc:
                        loc = location_clean

                    if title and company:
                        jobs.append(
                            {
                                "job_id": re.sub(
                                    r"[^a-z0-9]", "", title.lower() + company.lower()
                                )[:12],
                                "title": title,
                                "company": company,
                                "location": loc,
                                "url": link,
                                "email": f"careers@{re.sub(r'[^a-z0-9]', '', company.lower())}.com",
                                "snippet": snippet,
                                "source": "indeed_rss",
                            }
                        )

                        if len(jobs) >= limit:
                            break

                if jobs:
                    break  # Got results from this location

            except Exception as e:
                logger.debug(f"[IndeedRSS] Error: {e}")
                continue

        logger.info(f"[IndeedRSS] Found {len(jobs)} jobs")
        return jobs[:limit]

    def close(self):
        try:
            self._session.close()
        except Exception:
            pass
