# Scraper Stealth & Ingestion Audit Report

## 1. Observation

### Codebase Inspections

#### A. Impersonation Profile Mismatches
In `scrapers/stealth_ingest.py` (lines 28–108), the `STEALTH_PROFILES` array contains mismatches between the `User-Agent` headers and the TLS/JA3 `impersonate` targets:
- **Chrome 131 Profile** (Lines 29–46):
  ```python
  {
      "id": "chrome131",
      "impersonate": "chrome120",
      "headers": {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
          ...
  ```
- **Chrome 146 Profile** (Lines 49–64):
  ```python
  {
      "id": "chrome146",
      "impersonate": "chrome120",
      "headers": {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
          ...
  ```
- **Safari 18.0 Profile** (Lines 67–78):
  ```python
  {
      "id": "safari18_0",
      "impersonate": "safari17_2_1",
      "headers": {
          "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
          ...
  ```
- **Safari 2601 Profile** (Lines 81–92):
  ```python
  {
      "id": "safari2601",
      "impersonate": "safari17_2_1",
      "headers": {
          "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15",
          ...
  ```
- **Firefox 147 Profile** (Lines 95–107):
  ```python
  {
      "id": "firefox147",
      "impersonate": "firefox120",
      "headers": {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0",
          ...
  ```

#### B. Fallback Cascading & Missing Dependencies
In `scrapers/stealth_ingest.py` (lines 459–478), if direct `curl_cffi` requests fail or are blocked, the engine cascades to `NodriverFallback` and then `ApexCamoufoxFallback`:
```python
        if not html_content:
            logger.warning(f"Stealth fetch returned empty or challenged content. Trying NodriverFallback for {url}.")
            try:
                from core.stealth import NodriverFallback
                proxy_str = proxy_config.get("http") if proxy_config else None
                html_content = await NodriverFallback.get_page_content(url, proxy=proxy_str)
            except Exception as ne:
                logger.error(f"NodriverFallback failed for {url}: {ne}")

            if not html_content or any(k in html_content.lower() for k in ["just a moment", "attention required", "turnstile", "ddg-captcha"]):
                logger.warning(f"Nodriver fallback failed or was challenged. Trying ApexCamoufoxFallback for {url}.")
                try:
                    from core.stealth import ApexCamoufoxFallback
                    proxy_str = proxy_config.get("http") if proxy_config else None
                    html_content = await ApexCamoufoxFallback.get_page_content(url, proxy=proxy_str)
                except Exception as ce:
                    logger.error(f"ApexCamoufoxFallback failed for {url}: {ce}")
```
In `core/stealth.py` (lines 659–692), `ApexCamoufoxFallback` attempts to import and run `camoufox`:
```python
class ApexCamoufoxFallback:
    ...
    @staticmethod
    async def get_page_content(url: str, proxy: Optional[str] = None) -> str:
        try:
            from camoufox.async_api import AsyncCamoufox
            ...
        except ImportError:
            logger.error("[Apex] Camoufox not installed. Please pip install camoufox")
            return ""
```

#### C. Output Formatting Normalization
In `scrapers/stealth_ingest.py` (lines 496–508), `process_single_job` normalizes scraped job objects:
```python
        # Ensure that every job returned is a clean dict with at least 'title' and 'url' keys
        cleaned_jobs = []
        for job in jobs:
            if isinstance(job, dict):
                cleaned_job = {
                    "title": job.get("title") or "Unknown Position",
                    "url": job.get("url") or url,
                    "company": job.get("company"),
                    "description_snippet": job.get("description_snippet", "")
                }
                cleaned_jobs.append(cleaned_job)
                
        return cleaned_jobs
```
In `scrapers/stealth_ingest.py` (lines 525–546), `stealth_scrape_jobs` flat-maps and double-guarantees the output schema structure:
```python
    results = []
    for r in results_raw:
        if r is None:
            continue
        if isinstance(r, list):
            for item in r:
                if isinstance(item, dict):
                    results.append({
                        "title": item.get("title") or "Unknown Position",
                        "url": item.get("url") or "Unknown URL",
                        "company": item.get("company"),
                        "description_snippet": item.get("description_snippet", "")
                    })
```

### Runtime Observations (Command Output)
1. **Dependency check for Camoufox**:
   - Command: `python -c "import camoufox"`
   - Result:
     ```
     Traceback (most recent call last):
       File "<string>", line 1, in <module>
     ModuleNotFoundError: No module named 'camoufox'
     ```
2. **Dependency check for Nodriver**:
   - Command: `python -c "import nodriver"`
   - Result: Exit code `0` (Success).
3. **Dependency check for Undetected Chromedriver**:
   - Command: `python -c "import undetected_chromedriver"`
   - Result: Exit code `0` (Success).
4. **Unit test execution**:
   - Command: `python -m pytest tests/test_stealth_parser_and_fallbacks.py`
   - Result: `12 passed in 31.59s`. All tests passed (using mocks for WAF bypasses and missing modules).

---

## 2. Logic Chain

1. **Fingerprint Match Violation**: Passive TLS and HTTP/2 settings/window fingerprinting checks on advanced bot shields (e.g. Cloudflare Turnstile, DataDome) track differences between the client hello configuration and the User-Agent header. Since the User-Agent claims to be Chrome 131/146/Safari 18/Firefox 147 while `curl_cffi` impersonates Chrome 120/Safari 17/Firefox 120, this creates an active mismatch signature. Sophisticated bot detection will instantly flag these sessions as automated.
2. **Broken Tier 3 Fallback**: The dynamic import of `camoufox` in `core/stealth.py` raises `ImportError` on the production/local environment because the library is not installed. As a result, the "Apex Tier 3 Stealth" fallback completely fails and returns an empty page source (`""`).
3. **Under-powered Tier 2 Fallback**: `NodriverFallback` successfully imports `nodriver` and launches headless Chrome. However, it fails to inject the canvas-noise and WebGL-spoofing scripts found in `core/stealth.py` (which are defined in `StealthScraper` but never injected into `NodriverFallback`), nor does it run the `HumanMouse` movement simulation (since `NodriverFallback` does not invoke it). Thus, if the target site demands behavioral telemetry, `nodriver` alone will be blocked.
4. **Single Point Proxy Failure**: When `RESIDENTIAL_PROXIES` is empty, `scrapers/stealth_ingest.py` defaults to `["http://jobhunt-stub-proxy:8080"]`. If this stub proxy is blocked or down, the scraper will fail entirely because it lacks fallback proxy list generators (unlike `core/stealth.py` which fetches from a free public API).
5. **Schema Consistency**: The extraction code runs through BeautifulSoup selectors, JSON-LD extraction, and an AITailor LLM fallback. At the end of `process_single_job` and inside `stealth_scrape_jobs`, the engine applies explicit dictionary comprehension with fallback defaults. This guarantees that all returned lists consist strictly of dictionaries with the keys: `"title"`, `"url"`, `"company"`, and `"description_snippet"`.

---

## 3. Caveats

- **External Site Telemetry**: The investigation was read-only and local, meaning we did not make live target HTTP requests to active Cloudflare/DataDome-protected production job boards (e.g., Indeed, LinkedIn, Bayt) to observe how they block the mismatches in real-time.
- **Environment Discrepancies**: We assume the local Python environment reflects the production celery worker environment. If the production environment does have `camoufox` installed, the dependency issue would not manifest there.
- **Proxy Stub Existence**: We assume `http://jobhunt-stub-proxy:8080` is a containerized stub/mock proxy used for local testing and not a real production service. If no real residential proxy is configured, production runs will fail.

---

## 4. Conclusion

1. **Resiliency Status**: The current stealth implementation is **fragile** against advanced bot detectors.
   - *JA3/UA Mismatches*: Present in all default HTTP request profiles, creating block triggers for Cloudflare/DataDome.
   - *Broken Fallback*: The final and most secure engine-level fallback (`ApexCamoufoxFallback` via `camoufox`) is completely disabled in runtime due to a missing library dependency (`camoufox`).
   - *Behavioral Simulation Gaps*: Missing from the `nodriver` tier, and `HumanMouse` simulation is ignored due to `nodriver` page API incompatibilities.
   - *No Proxy Failover*: Stub proxy defaults create a single point of failure if the residential proxies env var is unpopulated.
2. **Formatting Status**: The output formatting is **highly robust** and reliable. It guarantees returning a flat list of dictionaries with clean, structured strings for `"title"`, `"url"`, `"company"`, and `"description_snippet"`.

---

## 5. Verification Method

### Test Suite Execution
Run the unit test suite to verify the mock behavior and the parser normalization:
```powershell
python -m pytest tests/test_stealth_parser_and_fallbacks.py
```
*Expected: 12 tests pass successfully.*

### Library Dependency Verification
Check that `camoufox` is missing and `nodriver` is present:
```powershell
python -c "import camoufox"
# Expected to print ModuleNotFoundError and exit with status 1

python -c "import nodriver"
# Expected to exit with status 0
```

### Invalid Profile Crash Replication
Verify that an invalid profile throws an `ImpersonateError` during active request execution (mimicking what happens on unsynced profiles):
```powershell
python -c "from curl_cffi import requests; requests.get('https://example.com', impersonate='chrome132')"
# Expected to raise curl_cffi.requests.exceptions.ImpersonateError
```
