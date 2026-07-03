# Handoff Report: Scraper Stealth Hardening Exploration

## 1. Observation

### Codebase Analysis
- **Scraper Entry Point**: `scrapers/stealth_ingest.py` is the main script that fetches and parses job descriptions.
  - At line 12, it reads proxies:
    ```python
    PROXY_LIST = os.getenv("RESIDENTIAL_PROXIES", "").split(",")
    ```
  - At line 13, it defines static user-agent/impersonate profiles:
    ```python
    STEALTH_PROFILES = ["chrome110", "chrome116", "chrome120", "safari15_3", "safari15_5"]
    ```
  - At lines 101–112, the `stealth_scrape_jobs` engine executes scraper requests concurrently with `asyncio.gather(*tasks)` without rate limits:
    ```python
    async def stealth_scrape_jobs(urls: List[str]) -> List[dict]:
        tasks = [process_single_job(url) for url in urls]
        results_raw = await asyncio.gather(*tasks)
        ...
    ```
  - At lines 87-89, the `process_single_job` executes a warmup request, but uses random delays after the request without concurrency control:
    ```python
    # 1. Organic warmup — hit root domain first to collect clearance cookies
    await session.get(root_domain, timeout=15)
    await asyncio.sleep(random.uniform(2.0, 5.0))
    ```

### Reference Files
- **`core/stealth.py`**:
  - Implements `StealthScraper` which supports:
    - User-agent database with Search Engine crawlers (Googlebot, Bingbot) and mobile/desktop headers (lines 109–147).
    - WebGL GPU/Vendor spoofing scripts (lines 366–382).
    - Canvas fingerprinting noise injection scripts (lines 344–364).
    - Google Cache Fallback for Cloudflare bypass (lines 458–478).
    - Camoufox integration (`camoufox.async_api.AsyncCamoufox`) simulating human mouse movements using `core/human_mouse` (lines 641–672).
- **`core/zero_cost_stealth_browser.py`**:
  - Implements `ZeroCostStealthScraper` using `undetected_chromedriver` under headless mode (lines 12–60).

### Installed Libraries
- Verification of installed packages using terminal queries:
  - `curl_cffi` version `0.15.0` is installed.
  - `cloudscraper` version `1.2.71` is installed.
  - Verification of `curl_cffi` impersonate capabilities showed:
    - Profiles `'chrome100'`, `'chrome104'`, `'chrome110'`, `'chrome116'`, `'chrome120'`, `'chrome124'`, `'chrome131'`, `'chrome146'`, `'safari15_3'`, `'safari15_5'`, `'safari18_0'`, `'safari2601'`, `'firefox117'`, `'firefox147'`, `'edge99'`, and `'edge101'` are fully supported in this version.
    - Default profiles map to: `DEFAULT_CHROME = "chrome146"`, `DEFAULT_SAFARI = "safari2601"`, `DEFAULT_FIREFOX = "firefox147"`, and `DEFAULT_EDGE = "edge101"`.


## 2. Logic Chain

1. **Alignment of TLS and HTTP Headers**:
   - Modern CDNs (like Cloudflare, Datadome) correlate the TLS fingerprint (JA3/JA4) with the HTTP headers. For example, if a client hello presents a Chrome TLS signature, but the HTTP request headers have a Safari `User-Agent` or omit Chrome-specific client-hints (`Sec-CH-UA`), the request is flagged as a bot and blocked with a 403 or a CAPTCHA challenge.
   - Therefore, we must define structured profiles in `stealth_ingest.py` where each profile matches a specific browser version (e.g. `chrome146` TLS target with matching Chrome 146 headers), instead of selecting profiles and headers completely independently.

2. **Proxy Session Pinning**:
   - When a scraper fetches a site protected by Cloudflare, it must perform a warmup step (e.g., fetching the root domain or `/robots.txt`) to acquire security/clearance cookies (like `cf_clearance`). These cookies are cryptographically bound to the client's IP address.
   - If the IP address rotates between the warmup request and the final target request, the clearance cookies will be invalidated, causing the target fetch to fail.
   - Consequently, the scraper must pin the selected proxy (whether picked from a list or managed by a backconnect rotating provider) to the specific session executing the job, ensuring it remains constant for the entire lifetime of that request sequence (warmup + target page).

3. **Concurrency Control and Jitter**:
   - Running all scrape jobs in parallel with `asyncio.gather(*tasks)` creates a spike in requests from the same IP or session, triggering rate limit triggers.
   - Introducing an `asyncio.Semaphore` to cap concurrent tasks and using random delays (jitter) between requests per task will distribute the load organically and emulate human browsing patterns.

4. **Sannysoft Verification and Browser JS Fallbacks**:
   - `bot.sannysoft.com` tests both network level attributes (TLS/headers) and browser level attributes (using JS to verify canvas, WebGL, and `navigator.webdriver`).
   - A pure Python HTTP client like `curl_cffi` can bypass the network/TLS checks, but since it does not run JavaScript, it cannot pass the JS-rendered tests on the page.
   - Thus, the verification suite should support a two-phase check: (1) using `curl_cffi` to verify raw connection/header bypass, and (2) using `nodriver` or `camoufox` to verify JS-level environment stealthiness.


## 3. Caveats

- **CODE_ONLY Network Restrictions**: Due to sandbox network constraints, live verification requests to `https://bot.sannysoft.com/` were not run during investigation. The design and logic have been validated via local library signatures and codebase structure.
- **Proxy Provider Architecture**: The backconnect session-pinning logic (`username-session-ID`) assumes a standard backconnect provider syntax (like Bright Data or Oxylabs). If the user provides static IP lists, the fallback hash-pinning logic will execute instead.
- **Dynamic JS Test Execution**: Pure HTTP scrapers using `curl_cffi` only retrieve the raw HTML and do not run JavaScript. For pages with heavy interactive anti-bot screens (e.g. Turnstile), a browser fallback using `nodriver` or `camoufox` is mandatory.


## 4. Conclusion

The recommended stealth hardening solution consists of:
1. **Target Library**: Leverage `curl_cffi` as the primary scraper request library due to its native JA3 TLS fingerprint impersonation.
2. **Synchronized Profiles**: Maintain a mapping of consistent browser fingerprints (TLS profile + matching Headers + matching User-Agent) to prevent detection due to header-TLS mismatch.
3. **Session-Pinning Proxy Rotation**:
   - Read from `RESIDENTIAL_PROXIES` environment variable.
   - If it is a backconnect proxy, dynamically append a unique session ID (e.g., `-session-<random_id>`) to the proxy username.
   - If it is a list of IPs, pin the index of the selected proxy to the session hash.
4. **Organic Warmup**: Query `/robots.txt` or `/` on the target domain using the same `AsyncSession` to populate cookies prior to target request execution.
5. **Rate Limiting**: Limit concurrency via `asyncio.Semaphore(3)` and introduce jitter (`asyncio.sleep(random.uniform(2.5, 6.0))`).

### Code Deliverables Created in Agent Directory:
- `proposed_stealth_ingest.py`: Clean, fully optimized implementation of the hardened scraper.
- `verify_bot.py`: Diagnostic and verification script to test bypass against `bot.sannysoft.com`.


## 5. Verification Method

To verify the stealth mechanisms, execute the verification script outside of the CODE_ONLY sandbox:

```powershell
# Set test proxy (optional)
$env:TEST_PROXY="http://username:password@gate.proxyprovider.com:8000"

# Execute the verifier
python .agents/explorer_m1_3/verify_bot.py
```

### Invalidation Conditions:
- The verification fails if the script exits with non-zero code or logs `FAILURE`.
- The verification fails if `curl_cffi` is blocked by Cloudflare (HTTP 403 or redirect loop).
- The verification fails if the `navigator.webdriver` check returns `detected` under the browser automation test phase.
