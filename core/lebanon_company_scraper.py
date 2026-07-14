"""
Lebanon Company Scraper - Maximum Multi-Source v17
Finds Lebanese companies hiring for specific roles with ZERO API cost.
Works within PA 250s timeout.
"""

import json
import logging
import os
import random
import time
from typing import Any

try:
    from curl_cffi.requests import AsyncSession as httpx_AsyncClient
except ImportError:
    import httpx

    httpx_AsyncClient = httpx.AsyncClient
from datetime import datetime
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Cache
_CACHE_FILE = os.path.join(
    os.path.dirname(__file__), "..", "_lebanon_companies_cache.json"
)
_CACHE_TTL = 86400  # 24 hours

# JSearch API config
JSEARCH_KEY = "7085d5ad11msh996c8add34ca2a5p106c72jsn7beaa25f86e2"
JSEARCH_HOST = "jsearch.p.rapidapi.com"

# Lebanon locations (Sam's preference)
LEBANON_LOCATIONS = [
    "Beirut",
    "Jbeil",
    "Byblos",
    "Keserwan",
    "Jounieh",
    "Zouk Mosbeh",
    "Metn",
    "Jal el Dib",
    "Dekwaneh",
    "Mount Lebanon",
    "Baabda",
    "Aley",
    "Broummana",
    "Rabieh",
    "Zahle",
    "Batroun",
]

# EXCLUDED locations (South Lebanon per Sam's preference)
EXCLUDED_LOCATIONS = [
    "Saida",
    "Sidon",
    "Tyre",
    "Sour",
    "Nabatieh",
    "Bint Jbeil",
    "Marjayoun",
]

# Target roles
SAM_ROLES = [
    "Network Engineer",
    "IT Manager",
    "Infrastructure Engineer",
    "System Administrator",
    "Network Administrator",
    "Security Engineer",
    "Cloud Engineer",
    "DevOps Engineer",
    "IT Support Manager",
    "Telecom Engineer",
    "Data Center Engineer",
    "IT Director",
]

demo_user_ROLES = [
    "HR Manager",
    "HR Coordinator",
    "HR Operations",
    "Recruitment Specialist",
    "Customer Operations",
    "People Operations",
    "HR Generalist",
    "Talent Acquisition",
    "HR Administrator",
    "Employee Relations",
    "HR Business Partner",
    "Training Coordinator",
    "Payroll Specialist",
]

# User-Agent rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]

# Lebanese company patterns for passive discovery
LEBANESE_COMPANY_PATTERNS = [
    "Bank",
    "Holding",
    "Group",
    "Telecom",
    "Pharma",
    "Hospital",
    "University",
    "Hotel",
    "Mall",
    "Insurance",
    "Airlines",
    "Construction",
    "Technology",
    "Software",
    "Digital",
    "Media",
    "Advertising",
    "Real Estate",
    "Investment",
    "Trading",
    "Industrial",
    "Manufacturing",
    "Retail",
    "Restaurant",
    "Cafe",
    "Bakery",
    "Fashion",
    "Beauty",
    "Medical",
    "Clinic",
    "Laboratory",
    "Logistics",
    "Shipping",
    "Travel",
    "Tourism",
]


class LebanonCompanyScraper:
    """Multi-source scraper for Lebanese companies."""

    def __init__(self):
        self.cache = self._load_cache()
        self.session = None

    def _load_cache(self):
        try:
            if os.path.exists(_CACHE_FILE):
                with open(_CACHE_FILE) as f:
                    data = json.load(f)
                if time.time() - data.get("ts", 0) < _CACHE_TTL:
                    return data.get("companies", [])
        except Exception:
            pass
        return []

    def _save_cache(self, companies):
        try:
            with open(_CACHE_FILE, "w") as f:
                json.dump({"ts": time.time(), "companies": companies}, f)
        except Exception:
            pass

    async def _get_session(self):
        if self.session is None:
            self.session = httpx_AsyncClient(impersonate="chrome120", timeout=30.0)
        return self.session

    async def search_jsearch(self, role: str, location: str) -> list:
        """Search using JSearch API (RapidAPI)."""
        companies = []
        try:
            client = await self._get_session()
            resp = await client.get(
                "https://jsearch.p.rapidapi.com/search",
                params={
                    "query": f"{role} {location} Lebanon",
                    "page": "1",
                    "num_pages": "3",
                },
                headers={
                    "X-RapidAPI-Key": JSEARCH_KEY,
                    "X-RapidAPI-Host": JSEARCH_HOST,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                for job in data.get("data", []):
                    company_name = job.get("employer_name", "")
                    if company_name and company_name not in [
                        c["company"] for c in companies
                    ]:
                        companies.append(
                            {
                                "company": company_name,
                                "industry": job.get("job_employment_type", "Unknown"),
                                "location": job.get("job_city", location),
                                "emails": self._guess_emails(company_name),
                                "linkedin": "",
                                "website": job.get("employer_website", ""),
                                "relevance_score": 85,
                                "source": "jsearch",
                                "target_role": role,
                                "company_size": "",
                                "job_title": job.get("job_title", role),
                                "last_updated": datetime.now().isoformat(),
                            }
                        )
        except Exception as e:
            logger.warning(f"JSearch error: {e}")
        return companies

    def _guess_emails(self, company_name: str) -> list:
        """Generate likely email patterns for a company."""
        domain_hint = (
            company_name.lower()
            .replace(" ", "")
            .replace("sal", "")
            .replace("group", "")
            .replace("holding", "")
            .strip()
        )
        emails = [
            f"careers@{domain_hint}.com",
            f"hr@{domain_hint}.com",
            f"jobs@{domain_hint}.com",
            f"careers@{domain_hint}.com.lb",
            f"hr@{domain_hint}.com.lb",
        ]
        return emails

    async def search_bayt(self, role: str, location: str) -> list:
        """Search Bayt.com Lebanon section."""
        companies = []
        try:
            client = await self._get_session()
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            url = f"https://www.bayt.com/en/lebanon/jobs/{quote_plus(role.lower().replace(' ', '-'))}-jobs/"
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select(
                    '[data-js-aid="job-card"], .job-card, .has-pointer-d, .media-body'
                )
                for card in cards[:20]:
                    company_el = card.select_one(
                        '.t-small, .p10r, [data-js-aid="company-name"]'
                    )
                    if company_el:
                        company_name = company_el.get_text(strip=True)
                        if company_name and len(company_name) > 2:
                            companies.append(
                                {
                                    "company": company_name,
                                    "industry": "",
                                    "location": location,
                                    "emails": self._guess_emails(company_name),
                                    "linkedin": "",
                                    "website": "",
                                    "relevance_score": 70,
                                    "source": "bayt",
                                    "target_role": role,
                                    "company_size": "",
                                    "job_title": role,
                                    "last_updated": datetime.now().isoformat(),
                                }
                            )
        except Exception as e:
            logger.warning(f"Bayt error: {e}")
        return companies

    async def search_linkedin_passive(self, role: str, location: str) -> list:
        """Passive LinkedIn search via DuckDuckGo."""
        companies = []
        try:
            query = f'site:linkedin.com/company "{location}" Lebanon "{role}"'
            encoded = quote_plus(query)
            client = await self._get_session()
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            resp = await client.get(
                f"https://html.duckduckgo.com/html/?q={encoded}",
                headers=headers,
                follow_redirects=True,
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for result in soup.select(".result__body")[:15]:
                    text = result.get_text()
                    # Extract company name patterns
                    for pattern in LEBANESE_COMPANY_PATTERNS:
                        if pattern.lower() in text.lower():
                            # Rough extraction
                            company_match = text.split(pattern)[0].strip().split()[-3:]
                            company_name = " ".join(company_match) + " " + pattern
                            if company_name and company_name not in [
                                c["company"] for c in companies
                            ]:
                                companies.append(
                                    {
                                        "company": company_name.strip(),
                                        "industry": pattern,
                                        "location": location,
                                        "emails": self._guess_emails(
                                            company_name.strip()
                                        ),
                                        "linkedin": "",
                                        "website": "",
                                        "relevance_score": 55,
                                        "source": "linkedin_passive",
                                        "target_role": role,
                                        "company_size": "",
                                        "job_title": role,
                                        "last_updated": datetime.now().isoformat(),
                                    }
                                )
        except Exception as e:
            logger.warning(f"LinkedIn passive error: {e}")
        return companies

    def _get_prebuilt_tech_companies(self) -> list[dict[str, Any]]:
        """Return the pre-compiled list of major Lebanese tech companies.

        Returns:
            List of dictionaries representing tech companies and their metadata.
        """
        return [
            {
                "company": "Murex",
                "industry": "Financial Software",
                "location": "Beirut",
                "relevance_score": 95,
            },
            {
                "company": "CME Offshore",
                "industry": "Technology",
                "location": "Beirut",
                "relevance_score": 90,
            },
            {
                "company": "Touch Lebanon",
                "industry": "Telecommunications",
                "location": "Beirut",
                "relevance_score": 90,
            },
            {
                "company": "Alfa Telecom",
                "industry": "Telecommunications",
                "location": "Beirut",
                "relevance_score": 90,
            },
            {
                "company": "Berytech",
                "industry": "Technology",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "Malia Group",
                "industry": "Technology",
                "location": "Beirut",
                "relevance_score": 80,
            },
            {
                "company": "TerraNet",
                "industry": "ISP/Telecom",
                "location": "Beirut",
                "relevance_score": 82,
            },
            {
                "company": "Sodetel",
                "industry": "Telecommunications",
                "location": "Beirut",
                "relevance_score": 80,
            },
            {
                "company": "Ogero Telecom",
                "industry": "Telecommunications",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "Cyberia",
                "industry": "ISP",
                "location": "Beirut",
                "relevance_score": 78,
            },
            {
                "company": "Cedarcom",
                "industry": "ISP",
                "location": "Jdeideh",
                "relevance_score": 75,
            },
            {
                "company": "Inconet Data",
                "industry": "IT Services",
                "location": "Beirut",
                "relevance_score": 80,
            },
            {
                "company": "IT Works",
                "industry": "IT Services",
                "location": "Beirut",
                "relevance_score": 78,
            },
            {
                "company": "ElementN",
                "industry": "Software",
                "location": "Beirut",
                "relevance_score": 82,
            },
            {
                "company": "Anghami",
                "industry": "Music/Tech",
                "location": "Beirut",
                "relevance_score": 88,
            },
            {
                "company": "Toters",
                "industry": "Delivery/Tech",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "NAR Technologies",
                "industry": "IT Services",
                "location": "Metn",
                "relevance_score": 75,
            },
            {
                "company": "Cedarcom",
                "industry": "Telecom",
                "location": "Metn",
                "relevance_score": 75,
            },
            {
                "company": "Solidere",
                "industry": "Real Estate",
                "location": "Beirut",
                "relevance_score": 82,
            },
        ]

    def _get_prebuilt_hr_companies(self) -> list[dict[str, Any]]:
        """Return the pre-compiled list of major Lebanese non-tech/HR-focused companies.

        Returns:
            List of dictionaries representing HR/non-tech companies and their metadata.
        """
        return [
            {
                "company": "Murex",
                "industry": "Financial Software",
                "location": "Beirut",
                "relevance_score": 90,
            },
            {
                "company": "Bank Audi",
                "industry": "Banking",
                "location": "Beirut",
                "relevance_score": 95,
            },
            {
                "company": "BLOM Bank",
                "industry": "Banking",
                "location": "Beirut",
                "relevance_score": 95,
            },
            {
                "company": "Byblos Bank",
                "industry": "Banking",
                "location": "Jbeil",
                "relevance_score": 95,
            },
            {
                "company": "Bank of Beirut",
                "industry": "Banking",
                "location": "Beirut",
                "relevance_score": 90,
            },
            {
                "company": "Credit Libanais",
                "industry": "Banking",
                "location": "Beirut",
                "relevance_score": 90,
            },
            {
                "company": "Fransabank",
                "industry": "Banking",
                "location": "Beirut",
                "relevance_score": 88,
            },
            {
                "company": "Bankmed",
                "industry": "Banking",
                "location": "Beirut",
                "relevance_score": 88,
            },
            {
                "company": "BBAC",
                "industry": "Banking",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "Azadea Group",
                "industry": "Retail",
                "location": "Beirut",
                "relevance_score": 90,
            },
            {
                "company": "Malia Group",
                "industry": "Conglomerate",
                "location": "Beirut",
                "relevance_score": 88,
            },
            {
                "company": "Berytech",
                "industry": "Technology",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "Chalhoub Group",
                "industry": "Luxury Retail",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "Hikma Pharmaceuticals",
                "industry": "Pharma",
                "location": "Beirut",
                "relevance_score": 88,
            },
            {
                "company": "Holdal Group",
                "industry": "Distribution",
                "location": "Beirut",
                "relevance_score": 82,
            },
            {
                "company": "Fattal Group",
                "industry": "Distribution",
                "location": "Beirut",
                "relevance_score": 82,
            },
            {
                "company": "Kettaneh Group",
                "industry": "Automotive",
                "location": "Beirut",
                "relevance_score": 80,
            },
            {
                "company": "Khatib & Alami",
                "industry": "Engineering",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "Dar Al Handasah",
                "industry": "Engineering",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "Nestle Lebanon",
                "industry": "FMCG",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "Unilever Lebanon",
                "industry": "FMCG",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "PepsiCo Lebanon",
                "industry": "FMCG",
                "location": "Beirut",
                "relevance_score": 82,
            },
            {
                "company": "Coca-Cola Lebanon",
                "industry": "FMCG",
                "location": "Beirut",
                "relevance_score": 82,
            },
            {
                "company": "L'Oreal Lebanon",
                "industry": "Cosmetics",
                "location": "Beirut",
                "relevance_score": 82,
            },
            {
                "company": "Deloitte Lebanon",
                "industry": "Consulting",
                "location": "Beirut",
                "relevance_score": 90,
            },
            {
                "company": "PwC Lebanon",
                "industry": "Consulting",
                "location": "Beirut",
                "relevance_score": 90,
            },
            {
                "company": "EY Lebanon",
                "industry": "Consulting",
                "location": "Beirut",
                "relevance_score": 90,
            },
            {
                "company": "KPMG Lebanon",
                "industry": "Consulting",
                "location": "Beirut",
                "relevance_score": 90,
            },
            {
                "company": "AUBMC",
                "industry": "Healthcare",
                "location": "Beirut",
                "relevance_score": 88,
            },
            {
                "company": "Clemenceau Medical Center",
                "industry": "Healthcare",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "Hotel Dieu de France",
                "industry": "Healthcare",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "Bellevue Medical Center",
                "industry": "Healthcare",
                "location": "Metn",
                "relevance_score": 82,
            },
            {
                "company": "Mount Lebanon Hospital",
                "industry": "Healthcare",
                "location": "Mount Lebanon",
                "relevance_score": 82,
            },
            {
                "company": "Phoenicia Hotel",
                "industry": "Hospitality",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "Four Seasons Beirut",
                "industry": "Hospitality",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "Hilton Beirut",
                "industry": "Hospitality",
                "location": "Beirut",
                "relevance_score": 82,
            },
            {
                "company": "Middle East Airlines",
                "industry": "Aviation",
                "location": "Beirut",
                "relevance_score": 88,
            },
            {
                "company": "AUB",
                "industry": "Education",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "LAU",
                "industry": "Education",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "USJ",
                "industry": "Education",
                "location": "Beirut",
                "relevance_score": 82,
            },
            {
                "company": "NDU",
                "industry": "Education",
                "location": "Keserwan",
                "relevance_score": 80,
            },
            {
                "company": "Solidere",
                "industry": "Real Estate",
                "location": "Beirut",
                "relevance_score": 85,
            },
            {
                "company": "ABC Mall",
                "industry": "Retail",
                "location": "Beirut",
                "relevance_score": 82,
            },
            {
                "company": "Spinneys Lebanon",
                "industry": "Retail",
                "location": "Beirut",
                "relevance_score": 80,
            },
            {
                "company": "Transmed",
                "industry": "Distribution",
                "location": "Beirut",
                "relevance_score": 80,
            },
            {
                "company": "Aishti",
                "industry": "Luxury Retail",
                "location": "Beirut",
                "relevance_score": 82,
            },
            {
                "company": "Contact Lebanon",
                "industry": "Call Center",
                "location": "Beirut",
                "relevance_score": 78,
            },
        ]

    def get_prebuilt_lebanese_companies(self, role_type: str = "tech") -> list[dict[str, Any]]:
        """Pre-built list of major Lebanese companies by sector.

        Args:
            role_type: The sector category, either 'tech' or something else (for HR/other).

        Returns:
            List of dictionaries containing company details.
        """
        return self._get_prebuilt_tech_companies() if role_type == "tech" else self._get_prebuilt_hr_companies()

    def _is_excluded_location(self, location: str) -> bool:
        loc_lower = location.lower()
        return any(excl.lower() in loc_lower for excl in EXCLUDED_LOCATIONS)

    def _calculate_relevance(self, company: dict, target_role: str) -> int:
        """Rate company relevance based on role/industry match."""
        score = company.get("relevance_score", 50)
        if self._is_excluded_location(company.get("location", "")):
            score = 0
        return score

    async def scrape_for_role(
        self,
        role: str,
        location: str = "Beirut",
        role_type: str = "tech",
        limit: int = 50,
    ) -> list:
        """Main scrape entry point. Gets companies for a specific role."""
        all_companies = []

        # 1. Try JSearch (primary)
        try:
            jsearch_results = await self.search_jsearch(role, location)
            all_companies.extend(jsearch_results)
            logger.info(
                f"JSearch found {len(jsearch_results)} for {role} in {location}"
            )
        except Exception as e:
            logger.warning(f"JSearch failed: {e}")

        # 2. Get pre-built Lebanese companies
        prebuilt = self.get_prebuilt_lebanese_companies(role_type)
        for company in prebuilt:
            company["source"] = "prebuilt"
            company["target_role"] = role
            company["emails"] = self._guess_emails(company["company"])
            company["last_updated"] = datetime.now().isoformat()
            company["job_title"] = role
            company["linkedin"] = ""
            company["website"] = ""
            company["company_size"] = ""
        all_companies.extend(prebuilt)

        # 3. Try Bayt
        try:
            bayt_results = await self.search_bayt(role, location)
            all_companies.extend(bayt_results)
            logger.info(f"Bayt found {len(bayt_results)} for {role}")
        except Exception as e:
            logger.warning(f"Bayt failed: {e}")

        # 4. Passive LinkedIn
        try:
            linkedin_results = await self.search_linkedin_passive(role, location)
            all_companies.extend(linkedin_results)
            logger.info(f"Passive LinkedIn found {len(linkedin_results)} for {role}")
        except Exception as e:
            logger.warning(f"Passive LinkedIn failed: {e}")

        # Deduplicate by company name
        seen = set()
        unique = []
        for c in all_companies:
            name_key = c["company"].lower().strip()
            if name_key not in seen:
                seen.add(name_key)
                # Exclude South Lebanon
                if not self._is_excluded_location(c.get("location", "")):
                    c["relevance_score"] = self._calculate_relevance(c, role)
                    unique.append(c)

        # Sort by relevance
        unique.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Limit
        result = unique[:limit]

        # Cache
        self.cache.extend(result)
        self._save_cache(self.cache)

        logger.info(f"Total unique companies found: {len(result)}")
        return result

    async def scrape_all_roles(self) -> dict:
        """Scrape for all roles (Sam + demo_user)."""
        results = {}

        # Sam's roles
        sam_companies = []
        for role in SAM_ROLES[:3]:  # Top 3 most relevant
            companies = await self.scrape_for_role(role, "Beirut", "tech", 15)
            sam_companies.extend(companies)

        # Dedup Sam
        seen_sam = set()
        sam_unique = []
        for c in sam_companies:
            if c["company"].lower() not in seen_sam:
                seen_sam.add(c["company"].lower())
                sam_unique.append(c)
        results["sam"] = sam_unique[:50]

        # demo_user's roles
        demo_user_companies = []
        for role in demo_user_ROLES[:3]:
            companies = await self.scrape_for_role(role, "Beirut", "hr", 15)
            demo_user_companies.extend(companies)

        seen_demo_user = set()
        demo_user_unique = []
        for c in demo_user_companies:
            if c["company"].lower() not in seen_demo_user:
                seen_demo_user.add(c["company"].lower())
                demo_user_unique.append(c)
        results["demo_user"] = demo_user_unique[:50]

        return results


# Singleton
_lebanon_scraper = None


def get_lebanon_scraper() -> LebanonCompanyScraper:
    global _lebanon_scraper
    if _lebanon_scraper is None:
        _lebanon_scraper = LebanonCompanyScraper()
    return _lebanon_scraper

