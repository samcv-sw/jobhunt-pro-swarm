## 2026-07-05T18:44:13Z

You are the Scraper Stealth Worker.
Your working directory is: `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_scraper_v5_seq_1`

Your task is to implement the proxy routing fixes in the Nodriver and ApexCamoufox browser fallbacks and ensure perfect structured output invariants.

Please execute the following tasks:
1. Apply the changes to `core/stealth.py` as detailed in the Explorer's analysis:
   - For `NodriverFallback.get_page_content`, if the passed `proxy` parameter is missing/None/empty, check if there are valid proxies configured in the `RESIDENTIAL_PROXIES` environment variable. If not, default to the enterprise stub proxy: `http://jobhunt-stub-proxy:8080`.
   - For `ApexCamoufoxFallback.get_page_content`, if the passed `proxy` parameter is missing/None/empty, do the same check and default to `http://jobhunt-stub-proxy:8080` to prevent real IP leakage.
2. Apply the changes to `scrapers/stealth_ingest.py` as detailed in the Explorer's analysis:
   - In the `PROXY_LIST` definition, ensure that if `RESIDENTIAL_PROXIES` is defined but evaluates to empty, `PROXY_LIST` falls back to `["http://jobhunt-stub-proxy:8080"]`.
   - In `get_stabilized_proxy`, ensure it never returns an empty dictionary. Instead, default to the stub proxy (e.g. `http://jobhunt-stub-proxy:8080`) when no proxies are in `PROXY_LIST`.
3. Verify that all scraper code blocks in `scrapers/stealth_ingest.py` return a structured `list[dict]` containing at minimum `title` and `url` keys.
4. Add the two recommended unit tests:
   - In `tests/test_stealth_parser_and_fallbacks.py`, add `test_nodriver_fallback_resolves_default_proxy_when_none`.
   - In `tests/e2e/test_r3_scraper.py`, add `test_get_stabilized_proxy_empty_env_fallback`.
5. Run the test suite:
   ```powershell
   pytest tests/test_stealth_parser_and_fallbacks.py tests/e2e/test_r3_scraper.py
   ```
   Verify that all tests pass.
6. Write a `handoff.md` report in your working directory with the details of the code changes, tests added, and build/test commands and outcomes.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
