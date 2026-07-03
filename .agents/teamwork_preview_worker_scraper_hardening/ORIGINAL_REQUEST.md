## 2026-07-03T18:51:27Z
You are teamwork_preview_worker_scraper_hardening.
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_worker_scraper_hardening
Your parent conversation ID is: 91d10ef2-c6c3-4f61-bb63-9c8e72579eeb

Your mission is to modify `scrapers/stealth_ingest.py` to upgrade anti-bot bypass protections and return structured, parsed data.

Here is the exact blueprint of the changes to make in `scrapers/stealth_ingest.py`:

1. Fix `STEALTH_PROFILES` with Valid curl_cffi Targets:
Modify `STEALTH_PROFILES` array to map the invalid targets to valid ones:
- `chrome131` -> `impersonate: chrome120`
- `chrome146` -> `impersonate: chrome120`
- `safari18_0` -> `impersonate: safari17_2_1`
- `safari2601` -> `impersonate: safari17_2_1`
- `firefox147` -> `impersonate: firefox120`
Keep the `"id"` value as is (e.g. `"chrome131"`, `"safari18_0"`, `"chrome146"`, etc.) so that the E2E tests checking for these IDs in `STEALTH_PROFILES` still pass!

2. Refactor the parser to support parsing job listing/search results pages (multi-job card containers like `div.job_seen_beacon`, `li.jobs-search-results__list-item`, etc.) and returning a structured list of dicts:
- Add a new helper `_parse_page_content(html: str, source_url: str) -> List[Dict[str, Any]]`.
- It should search for selectors: `div.job_seen_beacon`, `li.jobs-search-results__list-item`, `div.job-card`, `article.job-listing`.
- If cards are found, extract the title, company, description_snippet, and job url for each card.
- If no card is found, fall back to parsing as a single job page using `_parse_job_page(html, source_url)` and return a list containing that single dict.
- If html is empty or parsing fails, return `[]`.
- Ensure `_parse_job_page` is kept as a helper returning a single dict, because the unit tests test it directly.

3. Update `process_single_job(url: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]`:
- Return `List[Dict[str, Any]]` instead of a single dict or None. On failure return `[]`.
- Integrate progressive browser fallbacks using `NodriverFallback` and `ApexCamoufoxFallback` from `core/stealth.py`.
- If Cloudflare turnstile, captcha, or WAF screens are detected in `response.text` (e.g. keywords "just a moment", "attention required", "turnstile", "ddg-captcha"), log a warning and fall back to fetching the page content using `NodriverFallback.get_page_content(url)` or `ApexCamoufoxFallback.get_page_content(url, proxy=...)`.
- Then parse the resulting page using `_parse_page_content(html_content, url)`.

4. Update `stealth_scrape_jobs(urls: List[str]) -> List[dict]`:
- Flat-map all the lists of dicts returned by `process_single_job` into a single list of dicts.
- Return the flattened list.

5. Run E2E tests:
- Execute `python -m pytest tests/e2e/test_r3_scraper.py` and verify that all tests pass.
- Execute `python scrapers/stealth_ingest.py` to verify sannysoft bypass check.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your changes, run the tests, and write your report/handoff to `handoff.md` in your working directory. Send a message to me (Recipient ID: 91d10ef2-c6c3-4f61-bb63-9c8e72579eeb) when you are done.
