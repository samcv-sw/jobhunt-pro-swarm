# JobHunt Pro — Initial Scraper & Test Suite Investigation

This report presents findings from an audit of JobHunt Pro's current job scraping implementations (`core/multi_source_scraper.py`, `core/bayt_scraper.py`, `core/wuzzuf_scraper.py`, and the `GulftalentScraper` in `core/multi_platform_apply.py`), baseline test suite execution, and recommended architecture for implementing R1 (enhanced scrapers with mock failover and stealth features) and R2 (database persistence and deduplication).

---

## 1. Baseline Test Suite Execution
The backend test suite was run inside the root directory to establish functional stability.

- **Command Used**: `uv run pytest`
- **Total Tests Collected**: 653
- **Total Tests Passed**: 653
- **Pass Rate**: 100%
- **Total Duration**: 158.58 seconds
- **Verification of Pass Status**:
  The entire suite compiled and ran cleanly. Key tests validated include `test_job_deduplication.py`, `test_scam_detector.py`, `test_scam_detector_extended.py`, `test_stealth_reliability.py`, and `test_stealth_parser_and_fallbacks.py`. All completed without failures or timeouts.

---

## 2. Investigation of Existing Scrapers

We audited the existing scraper implementations in the codebase to understand HTTP request routing and BeautifulSoup extraction selectors.

### A. `core/multi_source_scraper.py`
This module acts as a base for multi-source scraping.
- **HTTP Request Method**:
  - Uses `BaseScraper` class, which initializes `self._session` via `stealth.get_sync_client(timeout=timeout)`.
  - Natively routes through rotating proxies fetched from Proxyscrape or custom environment variables.
  - Implements exponential backoff on retry (delay logic on 429/503 statuses) and UA/platform rotation.
  - Re-tries 403 blocks with mobile user agents and mobile flags (`Sec-Ch-Ua-Mobile: ?1`).
- **Parser Extraction Logic**:
  - **`BaytScraper`**:
    - URL Formulated: `https://www.bayt.com/en/international/jobs/?q={q}&location={loc_q}`
    - Job Card Selectors: `li.has-pointer-d`, `div.job-card`, `article.is-available`, or `div.card`.
    - Title Selector: `h2.jb-title`, `h2`, `a.job-title`, or `a[href*="/en/international/jobs/"]`.
    - Company Selector: `span.jb-company`, `span.company`, `b.company-name`, or `a[href*="/en/company/"]`.
    - Location Selector: `span.jb-location` or `span.location`.
    - Job URL: `a[href*="/en/international/jobs/"]`.
    - Description/Snippet Selector: `p.jb-desc` or `div.job-description`.
  - **`WuzzufScraper`**:
    - URL Formulated: `https://wuzzuf.net/search/jobs/?q={q}&location={location_q}`
    - Job Card Selectors: `div.css-1gq4cwl`, `div.job-card`, `div.card`, `a.css-1w3khdb`, or `div.job`.
    - Title Selector: `h2.css-m604qf`, `h2`, `a[href*="/jobs/"]`, or `a.job-title`.
    - Company Selector: `a.css-17s97q8`, `span.company`, or `div.company`.
    - Location Selector: `span.css-5wys0k`, `span.location`, or `div.location`.
    - Job URL: `a[href*="/jobs/"]`.
    - Description/Snippet: Not extracted (defaults to `"wuzzuf: {title} at {company}"`).

### B. `core/bayt_scraper.py`
A standalone scraper optimized for Cloudflare bypassing on Bayt.com.
- **HTTP Request Method**:
  - Uses `cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})` to bypass Cloudflare.
  - Submits GET requests synchronously via the executor loop.
- **Parser Extraction Logic**:
  - Job Card Selectors: `li.has-pointer-d`, fallback `[class*='job-card']`, `li[class*='job']`, or parents of `h2 a[href*='/jobs/']`.
  - Title & URL Selector: `h2 a`, `a[href*='/jobs/']`, or `a`.
  - Company & Location Selector: Extracted from wrapper `div.job-company-location-wrapper`, `[class*='company']`, `[class*='location']`. Parses all stripped text pieces: first node is treated as company name, remaining nodes are joined as the location.
  - Description/Snippet: Not extracted.

### C. `core/wuzzuf_scraper.py`
A standalone scraper optimized for Wuzzuf.net.
- **HTTP Request Method**:
  - Employs `cloudscraper.create_scraper` with desktop chrome parameters.
  - Submits GET requests synchronously.
- **Parser Extraction Logic**:
  - Job Card Selectors: `div.css-ghe2tq.e1v1l3u10`, `div.css-ghe2tq`, `[class*='e1v1l3u10']`, `div[class*='job-card']`, or `div[class*='JobCard']`.
  - Title Selector: `h2 a[href*='/jobs/p/']`, `h2 a[href*='/jobs/']`, `a[href*='/en/jobs/']`, or `a[href*='/jobs/p/']`.
  - Company Selector: Resolves using `a[href*='/jobs/careers/']`.
  - Location Selector: Parses `span.css-16x61xq` or matches classes containing `16x61xq` / `eoyjyou0`.
  - Description/Snippet: Not extracted.

### D. `core/multi_platform_apply.py` (GulftalentScraper)
A GCC-focused scraper defined inside the apply module.
- **HTTP Request Method**:
  - Uses `stealth.get_async_client(timeout=25.0)` supporting TLS / HTTP2 spoofing via `curl_cffi` and proxy routing.
- **Parser Extraction Logic**:
  - Job Card Selectors: `div.module.job`, `div[class*='job']:not([class*='header'])`, `li[class*='job']`, `div.search-result`, or `div[data-job-id]`.
  - Title Selector: `h2 a`, `a[class*='title']`, `h3 a`.
  - Company Selector: `span[class*='company']`, `.company`, `a[class*='company']`.
  - Location Selector: `span[class*='location']`, `.location`, `span[class*='loc']`.
  - Description/Snippet: Not extracted.

---

## 3. Recommended Implementation Strategy for R1

R1 requires parsing Wuzzuf, Bayt, and GulfTalent with Job Title, Company Name, Job URL, Location, and Description; stealth client features; and mock failover data.

### A. Parser Standardisation & Description Scraping
1. **Consolidated Interface**: Introduce `GulfTalentScraper` to the central `core/multi_source_scraper.py` class list alongside `BaytScraper` and `WuzzufScraper`.
2. **Scraping Descriptions**:
   - **Bayt**: Continue using `p.jb-desc` or `div.job-description` from listing cards.
   - **Wuzzuf**: Extract description snippets from listing cards using classes `p.css-1n9z78s` or similar short description wrappers. If not present in listings, execute secondary details-page request via `StealthClient` targeting `div.css-1u17s97` or description fields.
   - **GulfTalent**: Extract the description snippet using `div[class*='description']`, `div.job-description`, or `div.module-body`.

### B. Stealth Client Standardisation
- **Eliminate `cloudscraper`**: Deprecate raw `cloudscraper` calls which bypass TLS blocks using outdated Node-like scripts. Standardise on `core/stealth_http.py`'s `StealthClient` (sync) and `AsyncStealthClient` (async).
- **TLS Fingerprinting**: Always use `curl_cffi` sessions with rotated browser impersonations (`chrome120`, `safari17_2_1`, `firefox120`).
- **Proxy Pinning**: Integrate `get_stabilized_proxy` or `_get_proxy` to route requests through rotating residential and datacenter proxies dynamically.
- **Anti-Ban Fallbacks**: When encountering a 403 or 429 block, enforce the multi-tier UA strategy: Desktop -> Mobile -> Googlebot -> Google Cache.

### C. Mock Failover Data System
To maintain 100% uptime in CODE_ONLY network mode or under aggressive blocking:
- Create a mock repository containing realistic MENA job details.
- Structured data templates matching searched `query` and `location` keys.
- **Failover Trigger**: Wrap the GET requests in try-catch blocks. If they fail (timeout, connection error, HTTP 403/429, or Cloudflare challenge HTML detected), log the warning and return structured mock data dynamically populated with local companies (e.g. "Aramco" for Saudi Arabia, "Emaar" for UAE) and relevant salaries.

---

## 4. Recommended Implementation Strategy for R2

R2 requires database persistence and text-normalization deduplication.

### A. Database Persistence
- **Execution Interface**: Standardise writing scraped jobs using SQLAlchemy async sessions (`get_session()` in `core/database.py`) or raw database connectors in transaction-safe context blocks.
- **Target Schema**: Persist fields into the SQLite `jobs` table:
  ```sql
  INSERT INTO jobs (job_id, company, title, location, url, description, source, status, user_id)
  VALUES (?, ?, ?, ?, ?, ?, ?, 'new', ?)
  ```
- **Job ID Generation**: Standardise `job_id` generation using a unique 12-character MD5 hash of:
  `hashlib.md5(f"{title.lower().strip()}:{company.lower().strip()}:{url}".encode()).hexdigest()[:12]`
  This acts as the primary key constraint to prevent exact-duplicate database insertions.

### B. Text-Normalization Deduplication
To prevent cross-platform duplication (e.g., same job posted on both Bayt and Wuzzuf with different URLs):
1. **Normalization Routine**: Enforce the `_norm()` helper in `core/scam_detector.py`'s `is_duplicate_job`:
   - Force lowercase and strip whitespace: `s.lower().strip()`.
   - Strip all punctuation and special characters: `re.sub(r"[^a-z0-9\s]", "", s)`.
   - Collapse multiple whitespaces: `re.sub(r"\s+", " ", s)`.
2. **Deduplication Logic Flow**:
   - **In-Memory Buffer**: Keep a set of normalized keys `normalized_title::normalized_company` during a scraping run.
   - **Database Check**: Before saving a job card:
     - Compute its normalized key.
     - Search the database for any job matching:
       ```sql
       SELECT id FROM jobs WHERE LOWER(title) = ? AND LOWER(company) = ?
       ```
       (Applying the same normalization to parameters).
     - If a matching job exists in the DB, discard the scraped card. If it does not exist, insert it.
