# Handoff Report: Scraper Stealth & Proxy Hardening Analysis

## 1. Observation
- `core/stealth.py`:
  - `NodriverFallback.get_page_content` receives a `proxy` argument but only appends `--proxy-server` argument to the browser startup if `proxy` is present and evaluates to true:
    ```python
    browser_args = []
    if proxy:
        browser_args.append(f"--proxy-server={proxy}")
    ```
  - `ApexCamoufoxFallback.get_page_content` passes `proxy` directly to `AsyncCamoufox`. If it is `None` or empty, it uses the host's direct network interface, exposing the scraper machine's real IP.
- `scrapers/stealth_ingest.py`:
  - Enforces configuration of `PROXY_LIST` defaulting to stub:
    ```python
    PROXY_LIST = [p.strip() for p in os.getenv("RESIDENTIAL_PROXIES", "http://jobhunt-stub-proxy:8080").split(",") if p.strip()]
    ```
    If `RESIDENTIAL_PROXIES` is set to `""`, this produces `[]` (empty list).
  - In `get_stabilized_proxy(session_id)`:
    ```python
    if not PROXY_LIST:
        return {}
    ```
    An empty dictionary is returned, which causes subsequent steps to extract `proxy_str = None` and bypass proxy routing.
  - Return structure checking of all parsing functions (`_parse_job_page`, `_parse_page_content`, `_parse_html_with_llm`, `process_single_job`, `stealth_scrape_jobs`) confirms that they normalize outputs to clean `list[dict]` containing at minimum `title` and `url` keys.

## 2. Logic Chain
- **Leak Vulnerability**: Missing/empty/None proxies parsed from env vars lead to empty dictionary returns in the scraper.
- **Propagation**: The empty dictionary results in a `None` proxy string passed to fallback systems.
- **Execution Leak**: Fallback mechanisms (Nodriver and Camoufox) accept `None` without checking env variables or default stubs, spawning browser processes with direct, unproxied internet access.
- **Remediation Strategy**: Inject self-healing defaults inside both the scraper's proxy selection and the fallback functions, ensuring `http://jobhunt-stub-proxy:8080` is strictly enforced as the ultimate fallback in all conditions.

## 3. Caveats
- Since this is a read-only investigation, no code modifications have been made directly to any functional code.
- Mocks are used to verify how dependencies like `nodriver` are invoked.

## 4. Conclusion
JobHunt Pro has a high risk of leaking the host's real IP if proxies are misconfigured or environments are left empty. We must implement fallback logic in `core/stealth.py` (resolving the env variable if the passed argument is empty) and harden `PROXY_LIST` parsing in `scrapers/stealth_ingest.py` to always provide a fallback proxy string. All parsed job lists successfully conform to returning structured list of dicts with `title` and `url` keys.

## 5. Verification Method
- Execute tests using pytest:
  ```powershell
  pytest tests/test_stealth_parser_and_fallbacks.py tests/e2e/test_r3_scraper.py
  ```
- To test the fix once implemented, run with cleared environment variable:
  ```powershell
  $env:RESIDENTIAL_PROXIES=""
  pytest tests/test_stealth_parser_and_fallbacks.py
  ```
  Ensure tests assert the default stub proxy `http://jobhunt-stub-proxy:8080` is routed to chrome browser args.
