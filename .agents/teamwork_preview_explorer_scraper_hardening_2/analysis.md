# Scraper Hardening and Anti-Bot Bypass Analysis

## 1. Executive Summary
This report analyzes `scrapers/stealth_ingest.py` and its corresponding test suite `tests/e2e/test_r3_scraper.py`. It evaluates the current anti-bot bypass mechanisms, identifies major limitations and critical architectural vulnerabilities, and outlines concrete recommendations for upgrading the scraper. The upgrades focus on integrating advanced browser-level fallbacks from `core/stealth.py` (including `NodriverFallback` and `ApexCamoufoxFallback`) and refactoring the parsing pipeline to extract list-of-dicts structured data instead of single-job/raw HTML output.

---

## 2. Codebase Overview and Test Suitability

### A. Analysis of `scrapers/stealth_ingest.py`
`scrapers/stealth_ingest.py` is a Python-based asynchronous scraping engine that uses the `curl_cffi` library to bypass TLS/JA3/JA4 fingerprinting. It contains:
- **`STEALTH_PROFILES`**: Configured headers and impersonation targets.
- **`get_stabilized_proxy`**: Performs session pinning for proxies, which is critical when hitting pages sequentially.
- **`process_single_job`**: Orchestrates requests using a concurrency semaphore, warmups (hitting `robots.txt`/root), and random delays (jitter).
- **`_parse_job_page`**: Extracts basic details (title, company, description, and source URL) from a single job page HTML using `BeautifulSoup`.

### B. Analysis of `tests/e2e/test_r3_scraper.py`
The E2E test suite validates the integration of the scraper with the FastAPI backend, Celery task runners, and core functionality:
- **Mock Router (`conftest.py`)**: Endpoints like `/api/v1/scraper/start` and `/api/v1/scraper/status/{task_id}` are mocked in the E2E test setup to return static responses simulating successful Cloudflare bypasses and TLS fingerprints.
- **Feature Coverage (Tier 1)**: Verifies that `/api/v1/scrape` queues Celery tasks, scraper profiles are loaded, and proxy fallbacks work.
- **Boundary Cases (Tier 2)**: Asserts that empty/broken HTML parsing is handled safely and invalid requests are rejected.
- **Integration & Scenario (Tiers 3 & 4)**: Verifies integration with the local database by mocking the HTTP request layer and testing full state flows (e.g., auth -> start -> status -> metrics).

All 12 tests in `tests/e2e/test_r3_scraper.py` execute and pass successfully.

---

## 3. Current Anti-Bot Bypass Mechanisms & Limitations

The scraper implements several baseline techniques to evade detection, but each has significant limitations when facing advanced protections like Cloudflare, Akamai, or Datadome:

| Mechanism | Current Implementation | Critical Limitations / Vulnerabilities |
| :--- | :--- | :--- |
| **TLS/JA3 Impersonation** | Uses `curl_cffi` to spoof browser TLS handshakes. | Uses "futuristic" or invalid targets like `"chrome146"` or `"safari2601"` which, while allowed by some versions of curl-impersonate, are highly anomalous and easily flagged by WAFs analyzing browser version distribution. |
| **HTTP Headers & Order** | Static header dictionary in `STEALTH_PROFILES`. | Adding or modifying headers via `session.headers.update()` can disrupt natural browser header order. WAFs inspect HTTP/2 frame and header order (JA4+ fingerprinting) and flag mismatches. |
| **IP Rotation / Pinning** | Simple hashing based on `session_id`. Falls back to `X-Forwarded-For` spoofing. | `X-Forwarded-For` header spoofing is useless against modern WAFs (they read the actual TCP packet IP). There is no mechanism to detect dead/banned proxies and auto-rotate. |
| **Warmup Request** | Hits `/robots.txt` or root before the target URL. | Programmatically hitting `/robots.txt` right before a job page is an obvious bot signature. Normal users do not check `robots.txt`. |
| **No JS Execution** | Raw HTTP requests only. | Cannot solve client-side JS challenges (Turnstile, Datadome, hCaptcha). If a challenge is served, the scraper is completely blocked. |
| **Session Isolation** | Creates a new session ID for each URL. | When scraping multiple pages of a single site, using a new session/IP/cookie profile for every request triggers "distributed bot swarm" alerts. Real users reuse sessions and connection keep-alives. |

---

## 4. Upgrading to Advanced Anti-Bot Protections

To bypass modern anti-bot protections, the scraper must be integrated with the advanced layers already present in the codebase (`core/stealth.py`).

### Proposed Architectural Pipeline:
1. **HTTP/2 & TLS Fingerprint Alignment**: Update the profiles to use realistic, current browser versions (Chrome 120/124, Safari 17/18) and ensure `Sec-CH-UA` headers exactly match the TLS fingerprint version.
2. **Warmup Path Randomization**: Replace the rigid `/robots.txt` call with natural human-like warmups (e.g., random static assets, main search page, or omitting warmup entirely if cookies are not required).
3. **Integration with `core/stealth.py` Fallbacks**:
   - **Tier 1 (HTTP-level)**: Use `curl_cffi` sessions with proper rotation.
   - **Tier 2 (Headless Browser Fallback)**: If a WAF block/challenge is detected (e.g., `cf_clearance` required), fall back to `NodriverFallback` (headless Chrome with automated anti-detection).
   - **Tier 3 (Engine-level Fallback)**: If Nodriver fails, escalate to `ApexCamoufoxFallback` (modified Firefox engine with native WebGL/Canvas spoofing and `HumanMouse` simulation).

---

## 5. Returning Structured Parsed Data (List of Dicts)

Currently, the parser only extracts a single job card. To support search index pages and return structured parsed data (`List[dict]`), we propose refactoring the parsing pipeline:

1. **Dual-Mode Parser (`_parse_page_content`)**:
   - The parser inspects the page using `BeautifulSoup`.
   - It searches for common listing selectors (e.g., `.job-card`, `.job_seen_beacon`, `li.jobs-search-results__list-item`).
   - If cards are found, it loops through them to extract the `'title'`, `'url'`, and `'company'` of every job on the page.
   - If no cards are found, it treats the page as a single detail page and extracts the single job details.
2. **Flattening Aggregation**:
   - `stealth_scrape_jobs` gathers all tasks and flattens the returned lists into a single consolidated `List[dict]`.

---

## 6. Exact Code Changes Needed in `scrapers/stealth_ingest.py`

Here are the concrete code modifications proposed. Do not implement directly, as this is a read-only Explorer report.

### Change 1: Update `STEALTH_PROFILES` with Valid, Stable Targets
Replace the futuristic profiles with stable targets and align their Client Hints (`Sec-CH-UA`):

```python
# Curated browser profiles with aligned TLS targets and HTTP headers
STEALTH_PROFILES = [
    {
        "id": "chrome131",
        "impersonate": "chrome120",  # Map to valid chrome120 TLS fingerprint
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Sec-CH-UA": '"Not A(Brand";v="99", "Google Chrome";v="120", "Chromium";v="120"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive"
        }
    },
    {
        "id": "safari18_0",
        "impersonate": "safari17_2_1",  # Map to valid safari17 TLS fingerprint
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar-XM;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive"
        }
    },
    {
        "id": "firefox133",
        "impersonate": "firefox120",  # Map to valid firefox120 TLS fingerprint
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive"
        }
    }
]
```

### Change 2: Introduce Multi-Job HTML Parser
Add `_parse_page_content` to dynamically handle listing pages and single job pages:

```python
def _parse_page_content(html: str, source_url: str) -> List[Dict[str, Any]]:
    """
    Parses a page HTML and returns a structured list of dicts.
    Can handle both a list page (multi-job) or a job detail page (single-job).
    """
    if not html:
        return []
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # 1. Look for job cards / listing containers
        card_selectors = [
            "div.job_seen_beacon",             # Indeed
            "li.jobs-search-results__list-item", # LinkedIn
            "div.job-card",                    # Generic
            "article.job-listing"              # Generic
        ]
        
        cards = []
        for selector in card_selectors:
            found = soup.select(selector)
            if found:
                cards = found
                break
                
        # If we found list cards, extract details for each card
        if cards:
            parsed_jobs = []
            for card in cards:
                title = "Unknown Position"
                job_url = source_url
                company = None
                
                link_el = card.find("a", href=True)
                if link_el:
                    title = link_el.get_text(strip=True)
                    job_url = urllib.parse.urljoin(source_url, link_el["href"])
                    
                company_el = card.find(attrs={"class": lambda c: c and "company" in str(c).lower()})
                if company_el:
                    company = company_el.get_text(strip=True)
                    
                parsed_jobs.append({
                    "title": title,
                    "url": job_url,
                    "company": company,
                    "description_snippet": card.get_text(separator=" ", strip=True)[:300]
                })
            return parsed_jobs

        # 2. Fallback: Parse as a single job page to ensure backwards compatibility
        single_job = _parse_job_page(html, source_url)
        return [single_job] if single_job else []

    except Exception as e:
        logger.error(f"Error parsing page {source_url}: {e}")
        return []
```

### Change 3: Refactor `process_single_job` to Integrate `core/stealth.py` Fallbacks
Modify `process_single_job` to catch Cloudflare challenges and invoke the browser automation layers:

```python
async def process_single_job(url: str, session_id: Optional[str] = None) -> List[dict]:
    """
    Fetches a single job URL with stealth session isolation and parses it.
    Returns a list of structured job dicts or empty list on failure.
    Uses Concurrency Semaphore and fallbacks to Nodriver/Camoufox on WAF block.
    """
    if not HAS_CFFI:
        logger.warning("curl_cffi not installed! Bypasses might fail.")
        return []

    # Import advanced fallbacks from core/stealth.py
    from core.stealth import NodriverFallback, ApexCamoufoxFallback

    if not session_id:
        session_id = f"sess_{random.randint(100000, 999999)}"

    async with CONCURRENCY_SEMAPHORE:
        profile = random.choice(STEALTH_PROFILES)
        proxy_config = get_stabilized_proxy(session_id)
        
        headers = dict(profile["headers"])
        if not proxy_config:
            headers["X-Forwarded-For"] = (
                f"{random.randint(1,255)}.{random.randint(1,255)}"
                f".{random.randint(1,255)}.{random.randint(1,255)}"
            )

        cookies = {
            "_ga": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}",
            "_gid": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}"
        }

        async with requests.AsyncSession(
            impersonate=profile["impersonate"],
            proxies=proxy_config,
            headers=headers,
            cookies=cookies,
        ) as session:
            parsed_uri = urllib.parse.urlparse(url)
            root_domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}/"

            try:
                # 1. Natural Warmup URL (avoid robots.txt signature unless needed)
                warmup_url = root_domain if "sannysoft" in root_domain else root_domain
                logger.info(f"Warmup: hitting {warmup_url} with profile {profile['id']}")
                await session.get(warmup_url, timeout=15)
                
                await asyncio.sleep(random.uniform(2.5, 6.0))

                # 2. Target Fetch
                session.headers.update({"Referer": root_domain})
                logger.info(f"Stealth fetching target: {url}")
                response = await session.get(url, timeout=20)
                
                html_content = response.text
                
                # Check for Cloudflare/WAF block in response HTML
                if response.status_code in [403, 503] or any(
                    term in html_content.lower() for term in ["just a moment", "attention required", "turnstile", "ddg-captcha"]
                ):
                    logger.warning("Anti-bot protection detected. Escalating to Headless Browser fallback...")
                    # Try Nodriver first
                    html_content = await NodriverFallback.get_page_content(url)
                    
                    # If Nodriver fails, escalate to Camoufox
                    if not html_content:
                        logger.warning("Nodriver fallback failed. Escalating to ApexCamoufox...")
                        html_content = await ApexCamoufoxFallback.get_page_content(url, proxy=proxy_config.get("http"))
                
                if not html_content:
                    logger.error(f"Failed to retrieve page source for {url}")
                    return []

                return _parse_page_content(html_content, url)

            except Exception as e:
                logger.error(f"Failed to stealth-fetch {url}: {e}")
                return []
```

### Change 4: Update `stealth_scrape_jobs` to Flatten and Aggregate
```python
async def stealth_scrape_jobs(urls: List[str]) -> List[dict]:
    """
    Main stealth scraping engine.
    Applies concurrency control and session pinning.
    Returns a consolidated list of structured job dicts.
    """
    tasks = []
    for url in urls:
        session_id = f"job_sess_{random.randint(100000, 999999)}"
        tasks.append(process_single_job(url, session_id))

    results_raw = await asyncio.gather(*tasks)

    # Flatten nested lists
    results = []
    for job_list in results_raw:
        if job_list:
            results.extend(job_list)

    logger.info(f"Stealth scrape complete: {len(results)} items parsed successfully.")
    return results
```

---

## 7. Verification Method
To verify these modifications:
1. Run the test command:
   ```bash
   python -m pytest tests/e2e/test_r3_scraper.py
   ```
   Ensure that existing integration, configuration, and unit tests continue to pass.
2. Run the verification script:
   ```bash
   python scrapers/stealth_ingest.py
   ```
   Confirm that the `verify_sannysoft_bypass` function executes successfully and clears the Cloudflare/antibot checks on `bot.sannysoft.com`.
