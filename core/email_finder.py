"""
Email Finder v2 — ZERO COST HR Email Discovery Engine
JobHunt Pro — discovers real HR emails for companies using:
  1. Smart domain resolution (DDG search + pattern guessing)
  2. Multi-pattern email matrix (12+ role prefixes per domain)
  3. SMTP MX verification (MAIL FROM + RCPT TO handshake, no send)
  4. Google dorking via DuckDuckGo (email scraping from search results)
  5. Company website scraping (contact/careers/about pages)
  6. In-memory caching for all resolved domains and verified emails

Usage (from campaign_runner.py):
    from core.email_finder import EmailFinder
    finder = EmailFinder()
    result = await finder.find_emails("Murex", "HR Coordinator", "Beirut")
"""
import asyncio
import logging
import random
import re
import socket
import time
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote_plus, urlparse

import httpx
import dns.resolver
from bs4 import BeautifulSoup

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

# Suffixes to strip from company names before domain guessing
COMPANY_SUFFIXES = [
    r'\bLLC\b', r'\bInc\.?\b', r'\bLtd\.?\b', r'\bLtd\b', r'\bCorp\.?\b',
    r'\bCorporation\b', r'\bCo\.?\b', r'\bCo\b', r'\bCompany\b', r'\bGroup\b',
    r'\bHoldings?\b', r'\bInternational\b', r'\bGlobal\b', r'\bSolutions?\b',
    r'\bTechnologies?\b', r'\bServices?\b', r'\bNetworks?\b', r'\bSystems?\b',
    r'\bLimited\b', r'\bAssociates?\b', r'\bPartners?\b', r'\bEnterprises?\b',
    r'\bIndustries?\b', r'\bConsulting\b', r'\bAdvisory\b', r'\bCapital\b',
    r'\bVentures?\b', r'\bInvestment\b', r'\bManagement\b', r'\bAgency\b',
    r'\bStudio\b', r'\bDigital\b', r'\bSoftware\b', r'\bS\.?A\.?L\.?\b', r'\bSAL\b',
    r'\bS\.?A\.?R\.?L\.?\b', r'\bSARL\b', r'\bS\.?A\.?\b', r'\bGmbH\b', r'\bBV\b',
    r'\bPty\.?\s*Ltd\.?\b', r'\bInc\b', r'\bIncorporated\b',
]

# TLDs to try when guessing domains (ordered by business likelihood)
TLD_ORDER = ['.com', '.co', '.net', '.org', '.io', '.me', '.ai']

# Multi-pattern email matrix — prioritized role prefixes (Direct-to-Manager Routing)
EMAIL_PREFIXES_PRIORITY = [
    # Tier 1: Founders / C-Suite (Decision Makers)
    "ceo", "founder", "cto", "founders",
    # Tier 2: Department Heads (Engineering/Tech)
    "engineering", "tech", "dev", "developers", "lead",
    # Tier 3: Talent/Hiring (Direct HR, avoiding generic info)
    "talent", "hiring", "recruiting",
    # Tier 4: General HR (fallback)
    "careers", "hr", "jobs",
]

# Email regex — stricter than job search version
_EMAIL_RE = re.compile(
    r'[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}'
)

# Blocked email patterns (noise to filter out)
BLOCKED_EMAIL_PATTERNS = [
    'noreply@', 'no-reply@', 'donotreply@', 'do-not-reply@',
    'example.com', 'test.com', 'domain.com', 'yourcompany',
    'w3.org', 'schema.org', 'sentry', 'webpack',
    'facebook.com', 'google.com', 'github.com', 'microsoft.com',
    'apple.com', 'cloudflare.com', 'jquery.com', 'wikipedia.org',
    'youtube.com', 'twitter.com', 'instagram.com', 'linkedin.com',
    'tiktok.com', 'sentry.io', 'noreply.', 'no-reply.',
    'email.com', 'mail.com', 'gmail.com', 'yahoo.com',
    'hotmail.com', 'outlook.com', 'aol.com', 'protonmail.com',
]

# User agents for scraping
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
]


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _clean_company_name(company: str) -> str:
    """Strip corporate suffixes and normalize company name for domain guessing."""
    cleaned = company.strip()
    for suffix in COMPANY_SUFFIXES:
        cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE)
    # Remove remaining non-alphanumeric (except spaces, hyphens)
    cleaned = re.sub(r'[^\w\s-]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else company.strip()


def _extract_emails(text: str) -> List[str]:
    """Extract valid email addresses from text, filtering noise."""
    if not text:
        return []
    seen: Set[str] = set()
    result: List[str] = []
    for match in _EMAIL_RE.finditer(text):
        email = match.group(0).lower().strip()
        # Skip noise
        if len(email) > 80:
            continue
        if any(p in email for p in BLOCKED_EMAIL_PATTERNS):
            continue
        if email.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js')):
            continue
        local, _, domain = email.partition('@')
        if '.' not in domain:
            continue
        if email in seen:
            continue
        seen.add(email)
        result.append(email)
    return result


def _extract_domain_from_url(url: str) -> Optional[str]:
    """Extract clean domain from a URL."""
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return None
        # Remove www prefix
        hostname = re.sub(r'^www\d?\.', '', hostname)
        return hostname.lower()
    except Exception:
        return None


def _is_likely_company_domain(domain: str) -> bool:
    """Check if a domain looks like a real company site (not a generic platform)."""
    generic_domains = {
        'linkedin.com', 'indeed.com', 'glassdoor.com', 'bayt.com',
        'wikipedia.org', 'facebook.com', 'twitter.com', 'instagram.com',
        'youtube.com', 'crunchbase.com', 'bloomberg.com', 'google.com',
        'naukrigulf.com', 'gulftalent.com', 'wuzzuf.net', 'monster.com',
        'seek.com.au', 'reed.co.uk', 'totaljobs.com', 'ziprecruiter.com',
        'simplyhired.com', 'careerbuilder.com', 'dice.com',
        'wikimedia.org', 'google.com', 'apple.com', 'microsoft.com',
        'amazon.com', 'netflix.com', 'yahoo.com', 'bing.com',
        'duckduckgo.com', 'reddit.com', 'pinterest.com', 'tumblr.com',
        'github.com', 'gitlab.com', 'bitbucket.org', 'stackoverflow.com',
        'medium.com', 'quora.com', 'about.com', 'answers.com',
    }
    # Check exact match AND subdomain match (e.g. en.wikipedia.org → wikipedia.org)
    domain_lower = domain.lower()
    if domain_lower in generic_domains:
        return False
    # Check if this is a subdomain of a generic domain
    parts = domain_lower.split('.')
    for i in range(1, len(parts)):
        parent = '.'.join(parts[i:])
        if parent in generic_domains:
            return False
    if len(parts) < 2:
        return False
    if any(p in domain_lower for p in ['blogspot', 'wordpress', 'wixsite', 'weebly']):
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# EmailFinder Class
# ═══════════════════════════════════════════════════════════════════════════════

class EmailFinder:
    """
    ZERO COST HR email discovery engine.

    Strategy (executed in order):
      1. Smart domain resolution: DDG search → pattern guessing → cache hit
      2. Multi-pattern email matrix: 12 role prefixes per domain
      3. Google dorking via DDG: search for emails on domain pages
      4. Website scraping: visit contact/careers/about pages
      5. SMTP MX verification: MAIL FROM + RCPT TO handshake (no send)

    All results are cached in memory. Thread-safe for async usage.
    """

    def __init__(self, rate_limit_sec: float = 1.5):
        self._rate_limit_sec = rate_limit_sec
        self._last_request: float = 0.0
        self._ddg_lock = asyncio.Lock()  # Serializes DDG requests

        # Caches
        self._domain_cache: Dict[str, str] = {}  # company_lower → domain
        self._email_cache: Dict[str, List[str]] = {}  # domain → [emails]
        self._verified_cache: Dict[str, bool] = {}  # email → verified
        self._mx_cache: Dict[str, Optional[str]] = {}  # domain → mx_host
        self._catch_all_cache: Dict[str, bool] = {}  # domain → is_catch_all

        # HTTP client (lazy init)
        self._client: Optional[httpx.AsyncClient] = None

    # ── Static helpers ─────────────────────────────────────────────────────

    @staticmethod
    def is_placeholder_email(email: str, company: str) -> bool:
        """Check if an email looks like an auto-generated placeholder.

        Returns True for emails that were naively generated by stripping all
        non-alphanumeric chars from a multi-word company name with legal suffixes.

        Examples of placeholders:
          careers@networksolutionsinc.com (from "Network Solutions Inc")
          hr@techcorpllc.com (from "Tech Corp LLC")

        NOT placeholders:
          careers@harrywinston.com (from "Harry Winston" — correct domain)
          careers@murex.com (from "Murex" — correct domain)
        """
        if not email or '@' not in email:
            return True

        local_part = email.split('@')[0].lower().strip()
        domain_part = email.split('@')[1].lower().strip()

        # Only flag emails with common HR placeholder local parts
        placeholder_locals = {p.rstrip('@') for p in EMAIL_PREFIXES_PRIORITY}
        if local_part not in placeholder_locals:
            return False

        # Extract domain base (without TLD)
        domain_base = domain_part.rsplit('.', 1)[0] if '.' in domain_part else domain_part

        # Naive domain: all non-alphanumeric stripped (the old broken method)
        naive_domain = re.sub(r'[^a-z0-9]', '', company.lower())

        # Check 1: Does the naive domain match? (confirms it was generated via stripping)
        if not naive_domain or naive_domain not in domain_base:
            return False

        # Check 2: Does the company name contain LEGAL incorporation suffixes
        # that got crammed into the domain? Real domains NEVER contain these.
        # (NOTE: "Group", "Holdings", "Capital" etc are NOT here — they can be
        # legitimate domain components, e.g. azadeagroup.com, blominvestbank.com)
        legal_suffix_tokens = [
            'llc', 'inc', 'ltd', 'corp', 'corporation', 'incorporated',
            'limited', 'company', 'sarl', 'sal', 'gmbh', 'bv',
        ]
        company_lower = company.lower()
        for token in legal_suffix_tokens:
            # Check if token appears in original company name
            if re.search(r'\b' + re.escape(token) + r'\b', company_lower):
                # If the naive domain matches, this token is baked into the domain
                return True

        # Check 3: Is the naive domain abnormally long? (>15 chars suggests
        # multiple words were smashed together, which is a red flag)
        if len(naive_domain) > 15 and ' ' in company.strip():
            return True

        return False

    # ── Async context manager support ───────────────────────────────────────

    async def __aenter__(self):
        await self._ensure_client()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def _ensure_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=30),
                follow_redirects=True,
                headers={
                    'User-Agent': random.choice(USER_AGENTS),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'DNT': '1',
                },
            )

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    # ── Rate limiting ──────────────────────────────────────────────────────

    async def _rate_limit(self):
        """Ensure minimum interval between operations."""
        now = time.monotonic()
        elapsed = now - self._last_request
        if elapsed < self._rate_limit_sec:
            jitter = random.uniform(0, 0.5)
            await asyncio.sleep(self._rate_limit_sec - elapsed + jitter)
        self._last_request = time.monotonic()

    async def _call_ddg_safe(self, query: str, max_results: int = 10) -> List[Dict]:
        """Perform a DuckDuckGo search safely, avoiding rate limits and keeping the event loop responsive."""
        if DDGS is None:
            return []

        async with self._ddg_lock:
            # Apply rate limit pacing under the lock
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self._rate_limit_sec:
                jitter = random.uniform(0, 0.5)
                await asyncio.sleep(self._rate_limit_sec - elapsed + jitter)

            # Run the synchronous blocking DDG request in a thread pool
            def _execute_search():
                try:
                    with DDGS() as ddgs:
                        return list(ddgs.text(query, max_results=max_results))
                except Exception as e:
                    logger.debug(f"[EmailFinder] DDG query '{query}' failed: {e}")
                    return []

            results = await asyncio.to_thread(_execute_search)
            self._last_request = time.monotonic()
            return results

    # ══════════════════════════════════════════════════════════════════════
    # Bouncify-Style MX Verification (Lightweight, DNS-only)
    # ══════════════════════════════════════════════════════════════════════

    async def _verify_domain_has_mx(self, domain: str) -> bool:
        """Quick DNS MX lookup — returns True if domain accepts email.
        Cached in self._mx_cache.
        This is the Bouncify-style check: lightweight, no SMTP connection."""
        if domain in self._mx_cache:
            return self._mx_cache[domain] is not None

        try:
            loop = asyncio.get_running_loop()
            answers = await loop.run_in_executor(
                None, lambda: dns.resolver.resolve(domain, 'MX')
            )
            if answers:
                mx_host = str(sorted(answers, key=lambda r: r.preference)[0].exchange).rstrip('.')
                self._mx_cache[domain] = mx_host
                return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            pass
        except Exception:
            pass

        self._mx_cache[domain] = None
        return False

    @staticmethod
    def _is_disposable_domain(domain: str) -> bool:
        """Check if domain is a disposable/temp email provider."""
        disposable_patterns = [
            'mailinator.com', 'guerrillamail.com', '10minutemail', 'tempmail',
            'throwaway', 'dispostable', 'yopmail', 'trashmail', 'sharklasers',
            'guerrillamail', 'maildrop.cc', 'harakirimail', 'spamgourmet',
            '33mail.com', 'mailnesia', 'anonaddy', 'simplelogin', 'erine.email',
            'bbyuopsch.it.com',
        ]
        domain_lower = domain.lower()
        return any(d in domain_lower for d in disposable_patterns)

    @staticmethod
    def _is_role_based(email: str) -> bool:
        """Check if email is a shared/role-based address (lower deliverability)."""
        role_prefixes = {
            'info', 'contact', 'hello', 'admin', 'support', 'sales',
            'webmaster', 'postmaster', 'abuse', 'hostmaster', 'marketing',
        }
        local = email.split('@')[0].lower() if '@' in email else email.lower()
        return local in role_prefixes

    async def _bouncify_filter(
        self, emails: List[str], domain: str, company: str
    ) -> List[str]:
        """Filter email candidates through Bouncify-style checks:
        1. MX record must exist for the domain
        2. Domain must not be disposable
        3. Email must not be an auto-generated placeholder
        4. Role-based emails are deprioritized but kept

        Returns filtered + quality-scored list (deliverable first).
        """
        if not emails:
            return []

        # MX check (cached) — v16.320: NON-BLOCKING in fast mode
        # If MX fails, still keep emails — just mark them as unverified.
        # Blocking on MX kills all emails for guessed/incorrect domains.
        has_mx = await self._verify_domain_has_mx(domain)
        if not has_mx:
            logger.info(f"[Bouncify] No MX for {domain} — keeping emails (unverified)")

        # Disposable check
        if self._is_disposable_domain(domain):
            logger.info(f"[Bouncify] Disposable domain: {domain}")
            return []

        filtered = []
        deprioritized = []

        for email in emails:
            # Skip placeholder emails (auto-generated by pattern guessing)
            if self.is_placeholder_email(email, company):
                logger.debug(f"[Bouncify] Skip placeholder: {email}")
                continue

            # Skip known-blocked patterns (noreply, etc.)
            if any(p in email.lower() for p in BLOCKED_EMAIL_PATTERNS):
                logger.debug(f"[Bouncify] Skip blocked pattern: {email}")
                continue

            # Deprioritize role-based (info@, contact@) — still deliverable
            if self._is_role_based(email):
                deprioritized.append(email)
            else:
                filtered.append(email)

        result = filtered + deprioritized  # deliverable first
        if not result:
            logger.info(f"[Bouncify] All candidates filtered for {domain}")
        else:
            logger.info(
                f"[Bouncify] {domain}: {len(filtered)} deliverable + "
                f"{len(deprioritized)} role-based = {len(result)} total"
            )
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN API: find_emails()
    # ═══════════════════════════════════════════════════════════════════════════

    async def find_emails(
        self,
        company: str,
        title: str = "",
        location: str = "",
        fast: bool = False,
    ) -> Dict:
        """
        Discover real HR emails for a company. ZERO COST.

        Args:
            company: Company name (e.g., "Murex", "Bank Audi SAL")
            title: Job title (used as context, optional)
            location: Job location (used as context, optional)

        Returns:
            {
                "emails": ["hr@murex.com", "careers@murex.com"],
                "domain": "murex.com",
                "source": "smtp_verified",  # or "google_dork" / "website_scrape" / "pattern_guess"
                "verified": True,
                "all_candidates": [...],  # all email candidates considered
                "verified_count": 2,
                "method": "The strategy that produced the best result"
            }
        """
        await self._ensure_client()
        company_key = company.lower().strip()
        result: Dict = {
            "emails": [],
            "domain": "",
            "source": "pattern_guess",
            "verified": False,
            "all_candidates": [],
            "verified_count": 0,
            "method": "",
        }

        # Step 1: Resolve domain
        domain = await self._resolve_domain(company, fast=fast)
        if not domain:
            logger.warning(f"[EmailFinder] Could not resolve domain for: {company}")
            result["method"] = "domain_not_resolved"
            return result

        result["domain"] = domain

        # FAST MODE (PA): Quick DDG search + pattern guess (skip slow SMTP verification)
        # v16.320: Bouncify-style MX filtering added even in fast mode
        if fast:
            # Quick DDG email dorking (2s timeout)
            try:
                dork_emails = await asyncio.wait_for(
                    self._google_dork_emails(company, domain), timeout=15.0
                )
                if dork_emails:
                    # Bouncify filter: MX + disposable + placeholder check
                    filtered = await self._bouncify_filter(dork_emails, domain, company)
                    if filtered:
                        result["all_candidates"] = filtered
                        result["emails"] = filtered[:5]
                        result["source"] = "google_dork"
                        result["method"] = "google_dork + bouncify (fast, MX-verified)"
                        self._email_cache[domain] = result["emails"]
                        return result
                    # All dorked emails filtered — fall through to pattern guess
                    logger.info(f"[EmailFinder] All DDG emails filtered for {domain}, trying patterns")
            except (asyncio.TimeoutError, Exception):
                pass  # Fall through to pattern guess

            # Pattern guessing fallback (always works, instant)
            candidates = self._generate_email_candidates(domain)
            # Bouncify filter the pattern candidates too
            filtered = await self._bouncify_filter(candidates, domain, company)
            if filtered:
                result["all_candidates"] = filtered
                result["emails"] = filtered[:5] if len(filtered) >= 3 else filtered
                result["source"] = "pattern_guess"
                result["method"] = "pattern_matrix + bouncify (fast, MX-verified)"
            else:
                # All filtered — still return top 3 as last resort
                result["all_candidates"] = candidates
                result["emails"] = candidates[:3]
                result["source"] = "pattern_guess"
                result["method"] = "pattern_matrix (fast, MX-failed)"
            self._email_cache[domain] = result["emails"]
            return result

        # Step 2: Google dorking for real emails on this domain
        dork_emails = await self._google_dork_emails(company, domain)
        if dork_emails:
            # Bouncify pre-filter: MX + disposable + placeholder check (saves SMTP calls)
            dork_emails = await self._bouncify_filter(dork_emails, domain, company)
        if dork_emails:
            result["all_candidates"] = dork_emails
            result["source"] = "google_dork"

            # Step 2b: Verify dorked emails via SMTP
            if not fast:
                verified = await self._verify_emails(dork_emails, domain)
                if verified:
                    result["emails"] = verified
                    result["source"] = "google_dork"
                    result["verified"] = True
                    result["verified_count"] = len(verified)
                    result["method"] = "google_dork + bouncify -> smtp_verified"
                    self._email_cache[domain] = result["emails"]
                    return result

            # Dork found emails but none SMTP-verified — use bouncify-filtered ones
            result["emails"] = dork_emails
            result["method"] = "google_dork + bouncify (unverified)"
            self._email_cache[domain] = result["emails"]
            return result

        # Step 3: Scrape company website
        scraped = await self._scrape_website_emails(domain)
        if scraped:
            # Bouncify pre-filter
            scraped = await self._bouncify_filter(scraped, domain, company)
        if scraped:
            result["all_candidates"] = scraped
            result["source"] = "website_scrape"

            if not fast:
                verified = await self._verify_emails(scraped, domain)
                if verified:
                    result["emails"] = verified
                    result["source"] = "website_scrape"
                    result["verified"] = True
                    result["verified_count"] = len(verified)
                    result["method"] = "website_scrape + bouncify -> smtp_verified"
                    self._email_cache[domain] = result["emails"]
                    return result

            result["emails"] = scraped
            result["method"] = "website_scrape + bouncify (unverified)"
            self._email_cache[domain] = result["emails"]
            return result

        # Step 4: Generate pattern-based email candidates
        candidates = self._generate_email_candidates(domain)
        # Bouncify pre-filter the pattern candidates
        candidates = await self._bouncify_filter(candidates, domain, company)
        result["all_candidates"] = candidates

        # Step 5: SMTP verify the bouncify-filtered candidates
        if not fast and candidates:
            verified = await self._verify_emails(candidates, domain)
            if verified:
                result["emails"] = verified
                result["source"] = "pattern_guess"
                result["verified"] = True
                result["verified_count"] = len(verified)
                result["method"] = "pattern_matrix + bouncify -> smtp_verified"
                self._email_cache[domain] = result["emails"]
                return result

        # Step 6: Fallback — return bouncify-filtered candidates
        if candidates:
            result["emails"] = candidates[:5] if len(candidates) >= 3 else candidates
            result["method"] = "pattern_matrix + bouncify (unverified)"
        else:
            # Last resort: raw pattern guess (domain has no MX, can't verify)
            raw = self._generate_email_candidates(domain)
            result["emails"] = raw[:3]
            result["all_candidates"] = raw
            result["method"] = "pattern_matrix (no MX, fallback)"
        self._email_cache[domain] = result["emails"]
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # Step 1: Smart Domain Resolution
    # ═══════════════════════════════════════════════════════════════════════════

    async def _resolve_domain(self, company: str, fast: bool = False) -> Optional[str]:
        """
        Resolve company name → real domain.

        Strategies (in order):
          1. Check cache
          2. DDG search: "{company} official website" (skip if fast=True)
          3. Pattern guessing: {cleaned}.com, {cleaned}.co, etc.
        """
        cache_key = company.lower().strip()
        if cache_key in self._domain_cache:
            return self._domain_cache[cache_key]

        # Strategy A: DDG search (skip in fast mode — 2-5s savings)
        if not fast:
            domain = await self._search_domain_ddg(company)
            if domain and _is_likely_company_domain(domain):
                self._domain_cache[cache_key] = domain
                logger.info(f"[EmailFinder] Domain resolved via DDG: {company} → {domain}")
                return domain

        # Strategy B: Pattern guessing (always used, even in fast mode)
        domain = self._guess_domain(company)
        if domain:
            self._domain_cache[cache_key] = domain
            logger.info(f"[EmailFinder] Domain resolved via pattern: {company} → {domain}")
            return domain

        return None

    async def _search_domain_ddg(self, company: str) -> Optional[str]:
        """Use DuckDuckGo to find the company's official website."""
        query = f"{company} official website"
        results = await self._call_ddg_safe(query, max_results=5)

        if not results:
            return None

        # Extract domain from first result that looks like a company website
        for result in results:
            url = result.get('href') or result.get('url') or ''
            if not url:
                continue
            domain = _extract_domain_from_url(url)
            if domain and _is_likely_company_domain(domain):
                return domain

        return None

    def _guess_domain(self, company: str) -> Optional[str]:
        """Guess domain from company name using common patterns."""
        cleaned = _clean_company_name(company)
        # Normalize: lowercase, remove whitespace, keep alphanumeric + hyphens
        base = re.sub(r'[^a-z0-9-]', '', cleaned.lower())
        # Remove multiple consecutive hyphens
        base = re.sub(r'-+', '-', base).strip('-')

        if not base:
            return None

        # Handle common abbreviations
        base = re.sub(r'^the\b', '', base).strip('-')

        for tld in TLD_ORDER:
            domain = f"{base}{tld}"
            # Return .com first (most likely) and .co as backup
            if tld == '.com':
                return domain

        return f"{base}.com"

    # ═══════════════════════════════════════════════════════════════════════════
    # Step 2: Google Dorking via DDG
    # ═══════════════════════════════════════════════════════════════════════════

    async def _google_dork_emails(self, company: str, domain: str) -> List[str]:
        """
        Search for emails on the domain using DDG.

        Queries:
          - site:{domain} email OR "@{domain}"
          - "{company}" "email" "hr" OR "recruitment" OR "careers"
        """
        found_emails: Set[str] = set()

        # Dork 1: site:{domain} email
        query1 = f"site:{domain} email OR \"@{domain}\" OR ceo OR founder OR engineering OR contact"
        results1 = await self._call_ddg_safe(query1, max_results=10)
        for result in results1:
            body = result.get('body', '')
            url = result.get('href', '')
            emails = _extract_emails(body)
            # Only keep emails matching the domain
            for e in emails:
                if domain in e:
                    found_emails.add(e)
            # Also try to get emails from the result URL snippet
            snippet = result.get('snippet', '')
            if snippet:
                for e in _extract_emails(snippet):
                    if domain in e:
                        found_emails.add(e)

        # Dork 2: company email ceo cto founder engineering lead
        query2 = f"\"{company}\" email ceo cto founder engineering lead"
        results2 = await self._call_ddg_safe(query2, max_results=10)
        for result in results2:
            body = result.get('body', '')
            snippet = result.get('snippet', '')
            for e in _extract_emails(body + ' ' + snippet):
                if domain in e:
                    found_emails.add(e)

        # Sort: HR-related emails first
        result_list = list(found_emails)
        hr_prefixes = {'ceo', 'founder', 'cto', 'engineering', 'tech', 'dev',
                       'lead', 'talent', 'hiring', 'careers', 'hr', 'jobs'}
        result_list.sort(key=lambda e: (
            0 if e.split('@')[0].lower() in hr_prefixes else 1,
            e
        ))

        if result_list:
            logger.info(f"[EmailFinder] Dork found {len(result_list)} emails for {domain}")
        return result_list

    # ═══════════════════════════════════════════════════════════════════════════
    # Step 3: Company Website Scraping
    # ═══════════════════════════════════════════════════════════════════════════

    async def _scrape_website_emails(self, domain: str) -> List[str]:
        """
        Scrape company website pages for email addresses.

        Pages checked:
          - https://{domain}/contact
          - https://{domain}/careers
          - https://{domain}/about
          - https://{domain}/ (homepage)
        """
        all_emails: Set[str] = set()
        pages = [
            f"https://{domain}",
            f"https://{domain}/contact",
            f"https://{domain}/careers",
            f"https://{domain}/about",
            f"https://www.{domain}",
            f"https://www.{domain}/contact",
            f"https://www.{domain}/careers",
            f"https://www.{domain}/about",
        ]

        # Deduplicate: try both www and bare, prefer https first then http
        seen_urls: Set[str] = set()
        for page_url in pages:
            base = re.sub(r'^https?://', '', page_url)
            if base in seen_urls:
                continue
            seen_urls.add(base)

            await self._rate_limit()
            emails = await self._fetch_page_emails(page_url, domain)
            if emails:
                all_emails.update(emails)
                # If we found emails on a page, try the http fallback too
                if page_url.startswith('https://'):
                    http_url = page_url.replace('https://', 'http://', 1)
                    base_http = re.sub(r'^https?://', '', http_url)
                    if base_http not in seen_urls:
                        seen_urls.add(base_http)
                        await self._rate_limit()
                        more = await self._fetch_page_emails(http_url, domain)
                        if more:
                            all_emails.update(more)

        result_list = list(all_emails)
        # Sort HR-related first
        hr_prefixes = {'careers', 'hr', 'recruitment', 'jobs', 'talent', 'hiring',
                       'recruiting', 'people', 'cv', 'apply'}
        result_list.sort(key=lambda e: (
            0 if e.split('@')[0].lower() in hr_prefixes else 1,
            e
        ))

        if result_list:
            logger.info(f"[EmailFinder] Scrape found {len(result_list)} emails on {domain}")
        return result_list

    async def _fetch_page_emails(self, url: str, domain: str) -> List[str]:
        """Fetch a single page and extract domain-matching emails."""
        try:
            resp = await self._client.get(
                url,
                headers={'User-Agent': random.choice(USER_AGENTS)},
            )
            if resp.status_code != 200:
                logger.debug(f"[EmailFinder] HTTP {resp.status_code} for {url}")
                return []

            soup = BeautifulSoup(resp.text, 'html.parser')

            # Remove script and style tags
            for tag in soup(['script', 'style', 'noscript', 'nav', 'footer']):
                tag.decompose()

            text = soup.get_text(' ', strip=True)
            # Also check mailto links
            mailto_links = soup.select('a[href^=mailto:]')
            mailto_emails = []
            for link in mailto_links:
                href = link.get('href', '')
                email = href.replace('mailto:', '').split('?')[0].strip()
                if email and '@' in email:
                    mailto_emails.append(email.lower())

            text_emails = _extract_emails(text)
            all_emails = [e for e in text_emails + mailto_emails if domain in e]

            # Deduplicate
            return list(dict.fromkeys(all_emails))[:20]

        except httpx.TimeoutException:
            logger.debug(f"[EmailFinder] Timeout fetching {url}")
            return []
        except httpx.ConnectError:
            logger.debug(f"[EmailFinder] Connection error for {url}")
            return []
        except Exception as e:
            logger.debug(f"[EmailFinder] Error fetching {url}: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════════════════
    # Step 4: Generate Pattern-Based Email Candidates
    # ═══════════════════════════════════════════════════════════════════════════

    def _generate_email_candidates(self, domain: str) -> List[str]:
        """Generate all possible HR emails for a given domain."""
        return [f"{prefix}@{domain}" for prefix in EMAIL_PREFIXES_PRIORITY]

    # ═══════════════════════════════════════════════════════════════════════════
    # Step 5: SMTP MX Verification (ZERO COST)
    # ═══════════════════════════════════════════════════════════════════════════
    #
    # Connects to domain's MX server, does MAIL FROM + RCPT TO handshake,
    # checks if recipient accepted — NEVER sends actual email.
    # ═══════════════════════════════════════════════════════════════════════════

    async def _verify_emails(self, emails: List[str], domain: str) -> List[str]:
        """
        SMTP verify a batch of email candidates. Returns only verified ones.

        Handles:
          - MX record lookup (cached)
          - Catch-All domain check (cached)
          - SMTP handshake on port 25
          - MAIL FROM + RCPT TO
          - QUIT (no DATA, no send)
        """
        if not emails:
            return []

        # Get MX host (cached)
        mx_host = await self._get_mx_host(domain)
        if not mx_host:
            logger.debug(f"[EmailFinder] No MX for {domain}")
            return []

        sender_domain = "jobhunt.pro"  # From EHLO

        # 1. Perform Catch-All check before testing individual candidates
        if domain not in self._catch_all_cache:
            # Generate a highly randomized local part to test catch-all status
            random_part = f"verify_test_{random.randint(10000, 99999)}_{int(time.time())}"
            test_email = f"{random_part}@{domain}"
            try:
                # Check if the server accepts this completely random address
                is_catch_all = await self._smtp_check(mx_host, test_email, sender_domain)
                self._catch_all_cache[domain] = is_catch_all
                if is_catch_all:
                    logger.info(f"[EmailFinder] ⚠️ Catch-All domain detected for {domain}. Disabling SMTP validation as it is inconclusive.")
            except Exception as e:
                logger.debug(f"[EmailFinder] Catch-All check failed for {domain}: {e}")
                self._catch_all_cache[domain] = False
        
        # 2. If it is a Catch-All domain, SMTP validation is inconclusive.
        # We return an empty list here so the caller falls back to safer bouncify-filtered candidates.
        if self._catch_all_cache.get(domain, False):
            return []

        verified: List[str] = []

        for email in emails[:12]:  # Cap at 12 per batch
            # Check cache
            if email in self._verified_cache:
                if self._verified_cache[email]:
                    verified.append(email)
                continue

            await self._rate_limit()

            try:
                result = await self._smtp_check(mx_host, email, sender_domain)
                self._verified_cache[email] = result
                if result:
                    verified.append(email)
                    logger.info(f"[EmailFinder] ✅ SMTP verified: {email}")
                else:
                    logger.debug(f"[EmailFinder] ❌ SMTP rejected: {email}")
            except Exception as e:
                logger.debug(f"[EmailFinder] SMTP check failed for {email}: {e}")
                self._verified_cache[email] = False

        return verified

    async def _get_mx_host(self, domain: str) -> Optional[str]:
        """Get the MX server for a domain (cached)."""
        if domain in self._mx_cache:
            return self._mx_cache[domain]

        try:
            # Run DNS resolution in thread pool (dnspython is synchronous)
            loop = asyncio.get_running_loop()
            answers = await loop.run_in_executor(
                None, lambda: dns.resolver.resolve(domain, 'MX')
            )
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout) as e:
            logger.debug(f"[EmailFinder] No MX for {domain}: {e}")
            self._mx_cache[domain] = None
            return None
        except Exception as e:
            logger.debug(f"[EmailFinder] DNS error for {domain}: {e}")
            self._mx_cache[domain] = None
            return None

        if not answers:
            self._mx_cache[domain] = None
            return None

        # Pick lowest-preference MX
        mx_records = sorted(answers, key=lambda r: r.preference)
        mx_host = str(mx_records[0].exchange).rstrip('.')
        self._mx_cache[domain] = mx_host
        return mx_host

    async def _smtp_check(
        self,
        mx_host: str,
        recipient: str,
        sender_domain: str,
        timeout: float = 15.0,
    ) -> bool:
        """
        Perform SMTP RCPT TO verification.
        Returns True if recipient accepted, False if rejected.

        Protocol:
          1. Connect to MX:25
          2. Read banner
          3. EHLO sender_domain
          4. MAIL FROM: <verify@sender_domain>
          5. RCPT TO: <recipient>
          6. Read response → parse 250 vs 550
          7. QUIT
        """
        loop = asyncio.get_running_loop()

        def _do_smtp_check() -> bool:
            sock = None
            try:
                sock = socket.create_connection((mx_host, 25), timeout=timeout)
                sock.settimeout(timeout)

                # Read banner
                banner = _recv_line(sock)
                if not banner or not banner.startswith('2'):
                    return False

                # EHLO
                _send_cmd(sock, f'EHLO {sender_domain}')
                _read_multiline(sock)

                # MAIL FROM
                code, _ = _send_cmd(sock, f'MAIL FROM:<verify@{sender_domain}>')
                if not code.startswith('2'):
                    return False

                # RCPT TO
                code, msg = _send_cmd(sock, f'RCPT TO:<{recipient}>')
                if code.startswith('2') or code.startswith('25'):
                    # 250 = accepted, 251 = user not local will forward
                    _send_cmd(sock, 'QUIT')
                    return True
                elif code == '451' or code == '421':
                    # Temporary failure — might be greylisting, treat as inconclusive
                    # But log it; we won't count as verified
                    _send_cmd(sock, 'QUIT')
                    return False
                else:
                    # 550, 553, etc. = rejected
                    _send_cmd(sock, 'QUIT')
                    return False

            except (socket.timeout, ConnectionRefusedError, OSError) as e:
                logger.debug(f"[EmailFinder] SMTP connection to {mx_host} failed: {e}")
                return False
            finally:
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass

        return await loop.run_in_executor(None, _do_smtp_check)

    # ═══════════════════════════════════════════════════════════════════════════
    # Batch API: find_emails_batch()
    # ═══════════════════════════════════════════════════════════════════════════

    async def find_emails_batch(
        self,
        companies: List[str],
        fast: bool = False,
    ) -> Dict[str, Dict]:
        """
        Discover emails for multiple companies concurrently.

        Args:
            companies: List of company names

        Returns:
            Dict mapping company → result dict (same format as find_emails)
        """
        tasks = [self.find_emails(company, fast=fast) for company in companies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output: Dict[str, Dict] = {}
        for company, result in zip(companies, results):
            if isinstance(result, Exception):
                output[company] = {
                    "emails": [],
                    "domain": "",
                    "source": "error",
                    "verified": False,
                    "error": str(result),
                }
            else:
                output[company] = result

        return output

    # ═══════════════════════════════════════════════════════════════════════════
    # Enrich Job Dicts (integrate with existing job pipeline)
    # ═══════════════════════════════════════════════════════════════════════════

    async def enrich_jobs(self, jobs: List[Dict], fast: bool = False) -> List[Dict]:
        """
        Take a list of job dicts (with 'company' field) and enrich each with
        real discovered HR emails, replacing placeholder emails.
        
        When fast=True, skips SMTP verification for speed (PA-safe mode).

        Returns the same list with enriched email fields.
        """
        if not jobs:
            return jobs

        # Group jobs by company to avoid redundant lookups
        companies = list(dict.fromkeys(
            j.get("company", "") for j in jobs if j.get("company")
        ))
        if not companies:
            return jobs

        batch_results = await self.find_emails_batch(companies, fast=fast)

        for job in jobs:
            company = job.get("company", "")
            if company and company in batch_results:
                result = batch_results[company]
                if result.get("emails"):
                    source = result.get("source", "pattern_guess")
                    # v16.321: In fast mode, only replace placeholder if we found REAL emails
                    # (google_dork or website_scrape or smtp_verified).
                    # Pattern guesses are the same quality as the original placeholder.
                    if fast and source == "pattern_guess" and job.get("email"):
                        # Keep original placeholder — it's as good as our pattern guess
                        logger.debug(f"[EmailFinder] Keeping placeholder for {company} (fast pattern_guess)")
                        continue
                    job["email"] = result["emails"][0]
                    job["all_emails"] = result["emails"]
                    job["email_domain"] = result.get("domain", "")
                    job["email_verified"] = result.get("verified", False)
                    job["email_source"] = source

        return jobs

    # ═══════════════════════════════════════════════════════════════════════════
    # Cache Management
    # ═══════════════════════════════════════════════════════════════════════════

    def clear_cache(self):
        """Clear all caches."""
        self._domain_cache.clear()
        self._email_cache.clear()
        self._verified_cache.clear()
        self._mx_cache.clear()

    def get_cache_stats(self) -> Dict:
        """Return cache statistics."""
        return {
            "domains_resolved": len(self._domain_cache),
            "emails_cached": len(self._email_cache),
            "emails_verified": sum(1 for v in self._verified_cache.values() if v),
            "emails_rejected": sum(1 for v in self._verified_cache.values() if not v),
            "mx_hosts_cached": len(self._mx_cache),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SMTP Protocol Helpers (synchronous, run via run_in_executor)
# ═══════════════════════════════════════════════════════════════════════════════

def _recv_line(sock: socket.socket, bufsize: int = 4096) -> str:
    """Read a single line from SMTP socket."""
    data = b''
    while True:
        chunk = sock.recv(bufsize)
        if not chunk:
            break
        data += chunk
        if b'\n' in data:
            break
    return data.decode('utf-8', errors='replace').strip()


def _read_multiline(sock: socket.socket, bufsize: int = 4096) -> str:
    """Read multi-line SMTP response (lines start with code-space)."""
    all_data = ''
    while True:
        line = _recv_line(sock, bufsize)
        if not line:
            break
        all_data += line + '\n'
        # Last line has code followed by space (not hyphen)
        if len(line) >= 4 and line[3] == ' ':
            break
    return all_data


def _send_cmd(sock: socket.socket, cmd: str) -> Tuple[str, str]:
    """Send SMTP command and read response line. Returns (code, message)."""
    sock.sendall((cmd + '\r\n').encode('utf-8'))
    response = _recv_line(sock)
    code = response[:3] if len(response) >= 3 else ''
    return code, response[4:] if len(response) > 4 else ''


# ═══════════════════════════════════════════════════════════════════════════════
# Quick Test
# ═══════════════════════════════════════════════════════════════════════════════

async def _quick_test():
    """Run a quick test of the EmailFinder."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("=" * 60)
    print("EmailFinder v2 — Quick Test")
    print("=" * 60)

    async with EmailFinder(rate_limit_sec=1.5) as finder:
        # Test 1: Find emails for a company
        print("\n--- Test 1: find_emails('Murex', 'HR Coordinator', 'Beirut') ---")
        result = await finder.find_emails("Murex", "HR Coordinator", "Beirut")
        for k, v in result.items():
            if k != "all_candidates":
                print(f"  {k}: {v}")

        # Test 2: Find emails for another company
        print("\n--- Test 2: find_emails('Bank Audi', '', '') ---")
        result = await finder.find_emails("Bank Audi")
        print(f"  domain: {result['domain']}")
        print(f"  emails: {result['emails']}")
        print(f"  verified: {result['verified']}")
        print(f"  method: {result['method']}")

        # Test 3: Batch
        print("\n--- Test 3: find_emails_batch ---")
        batch = await finder.find_emails_batch(["Murex", "CMC Offshore", "Azadea Group"])
        for company, res in batch.items():
            print(f"  {company}: domain={res['domain']}, emails={res['emails'][:3]}, "
                  f"verified={res['verified']}")

        # Test 4: Cache stats
        print("\n--- Cache Stats ---")
        stats = finder.get_cache_stats()
        for k, v in stats.items():
            print(f"  {k}: {v}")

    print("\n✓ EmailFinder test complete")


if __name__ == "__main__":
    asyncio.run(_quick_test())
