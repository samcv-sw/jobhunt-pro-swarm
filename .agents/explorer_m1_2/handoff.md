# Handoff Report - Scraper Stealth Hardening Investigation

## 1. Observation

### Existing Codebase Structure
1. **`scrapers/stealth_ingest.py`**:
   - Lines 12-13: Defines proxy list and TLS profiles:
     ```python
     PROXY_LIST = os.getenv("RESIDENTIAL_PROXIES", "").split(",")
     STEALTH_PROFILES = ["chrome110", "chrome116", "chrome120", "safari15_3", "safari15_5"]
     ```
   - Lines 16-20: Implements `get_random_proxy()` returning `{"http": proxy, "https": proxy}` if `PROXY_LIST` contains values.
   - Lines 61-98: Implements `process_single_job(url: str)` using `curl_cffi` async session with a selected profile, random proxy (or fake `x-forwarded-for` header), and organic warmup:
     ```python
     # 1. Organic warmup — hit root domain first to collect clearance cookies
     await session.get(root_domain, timeout=15)
     await asyncio.sleep(random.uniform(2.0, 5.0))

     # 2. Fetch the actual target
     response = await session.get(url, timeout=15)
     ```

2. **`core/stealth.py`**:
   - Lines 27-676: Implements `StealthScraper` which integrates a free public proxy scraper fallback (`api.proxyscrape.com`), various mobile/Googlebot User-Agent generators, custom HTTP headers, canvas/WebGL spoofing JS scripts, and fallback classes:
     - `NodriverFallback`: Uses `nodriver` to retrieve page source.
     - `ApexCamoufoxFallback`: Uses `camoufox` to bypass strong challenges (e.g. Datadome/Cloudflare).
     - Browser Profiles:
       ```python
       _BROWSER_PROFILES = ["chrome131", "chrome130", "chrome129", "safari18_0", "edge99"]
       ```

3. **`core/zero_cost_stealth_browser.py`**:
   - Uses `undetected-chromedriver` to run headless Chrome and scrape.

### Environment Context & Installed Packages
Running `pip list` revealed the following relevant packages:
- `curl_cffi` (v0.15.0) — Primary library for TLS/JA3/HTTP2 impersonation.
- `nodriver` (v0.33.0 / v0.34.0 equivalent) — Installed and functional.
- `undetected-chromedriver` — Installed.
- `beautifulsoup4` (v4.12.2 or similar) — Used for HTML parsing.
- Note: `camoufox` is in `requirements.txt` but not currently installed in the environment (fails with `ModuleNotFoundError`).

### Antibot Testing results (`https://bot.sannysoft.com/`)
1. **Raw HTTP Client blocking**:
   Running a raw urllib GET request fails with `HTTP Error 403: Forbidden`.
2. **`curl_cffi` HTTP performance**:
   Running `requests.get('https://bot.sannysoft.com/', impersonate='chrome110')` returns `200 OK` immediately. However, parsing the static HTML shows that sannysoft uses client-side JavaScript execution to run checks and rewrite the DOM.
3. **`nodriver` Browser Automation performance**:
   Running `nodriver` in headless mode successfully executes JavaScript. Setting a custom non-headless User-Agent string bypasses all of sannysoft's detectors:
   - `user-agent-result`: passed (`Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36`)
   - `webdriver-result`: passed (`missing (passed)`)
   - `advanced-webdriver-result`: passed (`passed`)
   - `chrome-result`: passed (`present (passed)`)
   - `permissions-result`: passed (`prompt`)
   - `plugins-length-result`: passed (`5`)
   - `languages-result`: passed (`en-US,en`)

---

## 2. Logic Chain

1. **Choosing the impersonation engine**:
   - `curl_cffi` successfully gets a `200 OK` from `bot.sannysoft.com` while normal HTTP libraries get `403 Forbidden`. This confirms that TLS fingerprint/JA3 spoofing successfully bypasses basic Cloudflare/header walls.
   - For JavaScript-heavy antibot challenges, static requests are insufficient since tests are executed in-browser. `nodriver` successfully executes JS and tricks sannysoft when configured with a non-headless User-Agent argument.
   - Therefore, a **two-tier scraper engine design** is ideal: Tier 1 (`curl_cffi` for fast, lightweight static page requests) and Tier 2 (`nodriver` fallback for JS-challenge pages).

2. **Refining proxy rotation**:
   - Active residential proxies are necessary to avoid IP rate-limiting. A robust parser should split `RESIDENTIAL_PROXIES` environment variables on commas, strip whitespaces, and validate formatting.
   - If `RESIDENTIAL_PROXIES` is empty, the system should fall back to standard headers and optional public Elite proxy feeds (similar to `core/stealth.py`).

3. **Advanced HTTP/2 Header design**:
   - Browsers send structured HTTP/2 headers. Adding `:authority`, `:method`, `:path`, and `:scheme` order controls, and modern client hints (`sec-ch-ua`, `sec-ch-ua-mobile`, `sec-ch-ua-platform`), is critical to align the HTTP/2 frame fingerprint with the TLS profile.

---

## 3. Caveats

- `camoufox` is listed in the requirements but missing from the current virtualenv. Thus, any fallback implementation should prioritize `nodriver` or `undetected-chromedriver` over `camoufox` unless it is explicitly installed during deployment.
- Proxy validation relies on the quality of the commercial proxies provided in the `RESIDENTIAL_PROXIES` environment variable. If they are slow, the scraping request timeout of 15 seconds might need to be adjusted.

---

## 4. Conclusion

We recommend hardening `scrapers/stealth_ingest.py` with the following design:

### Recommended Libraries & TLS Impersonation Profiles
- **Primary Library**: `curl_cffi` (AsyncSession).
- **Fallback Browser Library**: `nodriver` (directly communicates via CDP, avoiding Selenium's webdriver trace).
- **TLS/JA3 profiles**: Rotate between latest Chrome and Safari profiles (`chrome120`, `chrome131`, `safari18_0`).

### Design of Advanced Bypass Mechanisms
1. **Dynamic Headers & Client Hints**: Match headers to the selected `impersonate` profile. If `chrome120` is used, send Chrome headers like `sec-ch-ua: "Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"`.
2. **Warmup Sequences**: Request the root domain of the target website first to capture validation cookies (e.g. `cf_clearance`, `__cfuid`), sleep randomly, and then request the target URL.
3. **User Agent Alignment**: Ensure the request headers' User-Agent matches the TLS profile being simulated (i.e. don't send a Safari user-agent with a Chrome JA3 fingerprint).
4. **Decoy Requests & Jitter**: Interleave scraping requests with requests to common sites like `google.com` or `bing.com` to make the access patterns appear organic.

### Proxy Rotation Strategy
- **Parsing**: Split `RESIDENTIAL_PROXIES` by comma, strip whitespace, and filter out empty strings.
- **Stateful selection**: Maintain a list of proxies in memory. Randomly select one per session.
- **Failover / Error handling**: If a proxy throws a connection/proxy error, catch it, black-list the proxy for a short period, and retry the request using a different proxy.
- **No-Proxy fallback**: If `RESIDENTIAL_PROXIES` is missing, generate rotating fake headers (like `X-Forwarded-For` pointing to random residential subnets) to mimic proxy hops, or fetch public elite proxies.

---

## 5. Verification Method

To verify the stealth mechanisms, create a test script `scratch/verify_stealth.py` that executes:
1. **HTTP-level check**: Use `curl_cffi` to GET `https://bot.sannysoft.com/` and confirm that it receives a `200 OK` response status (verifying TLS bypass).
2. **Browser-level checks**: Use `nodriver` to fetch `https://bot.sannysoft.com/`, sleep 5 seconds for execution, parse the resulting HTML with `BeautifulSoup`, and assert that the elements with IDs `user-agent-result`, `webdriver-result`, `chrome-result`, and `advanced-webdriver-result` all contain the class `passed`.

### Test Commands
Run the verification script:
```powershell
python scratch/test_sannysoft_nodriver.py
```
Expected output:
```text
=== RESULTS ===
ID: user-agent-result | Class: ['result', 'passed'] | Text: ...
ID: webdriver-result | Class: ['result', 'passed'] | Text: missing (passed)
ID: advanced-webdriver-result | Class: ['result', 'passed'] | Text: passed
ID: chrome-result | Class: ['result', 'passed'] | Text: present (passed)
...
```
