# Pytest Failure Audit Report

## 1. Observation
We ran the full test suite using:
```powershell
$env:PYTHONPATH="."
python -m pytest tests/
```
The run finished with **17 failed, 156 passed** (exit code 1). Below are the direct observations, tracebacks, and source locations:

### Observation A: `test_r1_t1_generate_cover_letter_queued`
- **File & Line**: `tests/e2e/test_r1_cover_letter.py:33`
- **Verbatim Error**:
  ```
  groq.PermissionDeniedError: Error code: 403 - {'error': {'message': 'Access denied. Please check your network settings.'}}
  ```
- **Context**: The test expects `/api/v1/generate-cover-letter` to return a JSON containing `{"status": "queued", "task_id": "mocked-task-r1-t1"}`:
  ```python
  resp = await client.post(
      "/api/v1/generate-cover-letter",
      json={"user_cv": "AI Engineer CV", "job_description": "FastAPI Developer Role"},
      headers=auth_header
  )
  assert resp.status_code == 200
  data = resp.json()
  assert data["status"] == "queued"
  ```

### Observation B: `test_r2_t2_layout_rtl_compliance` and `test_r2_t4_scenario_dashboard_layout_switch`
- **File & Line**: `tests/e2e/test_r2_dashboard.py:110` & `tests/e2e/test_r2_dashboard.py:182`
- **Verbatim Error**:
  ```
  E       assert ('dir="auto"' in '...<html> <body className="..." ...' or "dir={'auto'}" in '...')
  ```
- **Context**: The test asserts that `dir="auto"` or `dir={'auto'}` is declared in layout.tsx. However, `frontend/src/app/layout.tsx` currently contains:
  ```tsx
  <html
    lang="ar"
    dir="rtl"
    className={`${cairo.variable} ${tajawal.variable} h-full antialiased dark`}
  >
  ```

### Observation C: `test_r3_t1_trigger_scrape_queued`
- **File & Line**: `tests/e2e/test_r3_scraper.py:37`
- **Verbatim Error**:
  ```
  E           assert 401 == 200
  E            +  where 401 = <Response [401 Unauthorized]>.status_code
  ```
- **Context**: The test hits `/api/v1/scrape` but does not pass an authentication header, whereas `/api/v1/scrape` is protected by `Depends(verify_jwt)`.

### Observation D: `test_r3_t1_stealth_profiles_configured`
- **File & Line**: `tests/e2e/test_r3_scraper.py:71`
- **Verbatim Error**:
  ```
  E       AssertionError: assert 'chrome120' in [{'headers': {...}, 'id': 'firefox147', 'impersonate': 'firefox147'}]
  ```
- **Context**: The test checks if `"chrome120"` and `"safari15_3"` strings are in `STEALTH_PROFILES`. But `STEALTH_PROFILES` in `scrapers/stealth_ingest.py` is a list of dictionaries with `id` keys containing modern versions (`chrome131`, `chrome146`, `safari18_0`, `safari2601`, `firefox147`).

### Observation E: `test_r3_t1_get_random_proxy_fallback`
- **File & Line**: `tests/e2e/test_r3_scraper.py:76`
- **Verbatim Error**:
  ```
  E       TypeError: get_stabilized_proxy() missing 1 required positional argument: 'session_id'
  ```

### Observation F: `test_r3_t2_parse_job_page_broken_html`
- **File & Line**: `tests/e2e/test_r3_scraper.py:113`
- **Verbatim Error**:
  ```
  E       AssertionError: assert '' == 'Broken Title'
  ```
- **Context**: The helper `_parse_job_page` in `scrapers/stealth_ingest.py` finds the empty `<h1></h1>` tag and assigns `title = ""`, instead of falling back to the `<title>` tag.

### Observation G: `test_r3_t3_integration_scraper_to_database`
- **File & Line**: `tests/e2e/test_r3_scraper.py:146`
- **Verbatim Error**:
  ```
  E           TypeError: test_r3_t3_integration_scraper_to_database.<locals>.mock_process() takes 1 positional argument but 2 were given
  ```

### Observation H: `test_r5_t1_trigger_on_main_branch`
- **File & Line**: `tests/e2e/test_r5_cicd.py:32`
- **Verbatim Error**:
  ```
  E       KeyError: 'on'
  ```
- **Context**: The unquoted `on:` key in `.github/workflows/production.yml` is parsed by PyYAML (YAML 1.1 spec) as the boolean `True`, causing `data["on"]` to raise a `KeyError`.

### Observation I: `TestMaxProfitFeatures` (4 failures)
- **Failing Tests**: `test_database_migrations_app`, `test_get_services_page_app`, `test_purchase_service_success_app`, `test_upload_cv_persistence_app`
- **File & Line**: `tests/test_max_profit_features.py` (lines 331, 392, etc.)
- **Verbatim Error**:
  ```
  E           AttributeError: module 'web' has no attribute 'app'
  ```
- **Context**: The module `web/app.py` has an unused import:
  ```python
  from core.database import Database
  ```
  Since `Database` does not exist in `core/database.py`, importing `web.app` raises an `ImportError`. This causes `patch("web.app...")` to fail with `AttributeError` because the `app` submodule could not be dynamically bound to the `web` namespace.

### Observation J: `test_search_linkedin_xhr`
- **File & Line**: `tests/test_pa_job_scraper.py:130`
- **Verbatim Error**:
  ```
  E       AssertionError: assert 5 == 1
  E        +  where 5 = len([{'company': 'Arsenal Football Club', ...}])
  ```
- **Context**: The test mocks `PAJobScraper._fetch_url`, but `search_linkedin_xhr` constructs a direct `curl_cffi.requests.Session` and performs a live network call, bypassing the mock and returning 5 real UK jobs.

### Observation K: `test_waf_hacker_probe_blocking` and `test_waf_exploit_blocking`
- **File & Line**: `tests/test_security_hardening.py:53` & `tests/test_security_hardening.py:64`
- **Verbatim Error**:
  ```
  E       AssertionError: assert 'Access Denied.' == 'Access Denied (Blackholed).'
  ```
- **Context**: The Aegis middleware in `core/aegis_shield.py` (line 285) returns `"Access Denied."`, but the security hardening tests assert `"Access Denied (Blackholed)."`.

### Observation L: `test_campaign_runner_injects_tenant_smtp_to_user_details`
- **File & Line**: `tests/test_tenant_smtp.py:288`
- **Verbatim Error**:
  ```
  sqlite3.OperationalError: no such table: orders
  ...
  UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f4c2' in position 31: character maps to <undefined>
  ```
- **Context**:
  1. The test database setup `init_db()` in `tests/test_tenant_smtp.py` fails to create the `orders` table.
  2. The exception handler in `core/campaign_runner.py` at line 900 opens `campaign_error.txt` without `encoding="utf-8"`, causing a crash on Windows when the path contains `📂`.

---

## 2. Logic Chain
1. **Mocking vs. Imports**: In `test_r1_t1_generate_cover_letter_queued`, monkeypatching `backend.ai_engine.generate_smart_cover_letter_stream` has no effect on `backend/main.py` since it imports it directly via `from .ai_engine import generate...` at module load time. Therefore, the actual Groq API is called. In addition, the route `/api/v1/generate-cover-letter` was refactored in a previous step to return a `StreamingResponse` rather than queue a Celery task, making the assertion `assert data["status"] == "queued"` incorrect.
2. **Layout Direction**: The Next.js template in `frontend/src/app/layout.tsx` uses `dir="rtl"`. However, the dynamic layout and i18n tests expect the layout file to use `dir="auto"` or `dir={'auto'}` to support multi-language auto-direction.
3. **Endpoint Security**: The endpoint `/api/v1/scrape` in `backend/main.py` utilizes the `verify_jwt` security dependency. Hence, any request without the `Authorization: Bearer <token>` header is rejected with `401 Unauthorized`. The test client in `test_r3_t1_trigger_scrape_queued` misses this header.
4. **Scraper Profiles**: `scrapers/stealth_ingest.py` has been updated with modern browser profiles (`chrome131`, `chrome146`, `safari18_0`, etc.). The test `test_r3_t1_stealth_profiles_configured` searches for outdated strings (`"chrome120"`, `"safari15_3"`) directly in a list of dicts.
5. **Missing Arguments**: `get_stabilized_proxy` (aliased as `get_random_proxy`) requires a `session_id` to pin proxies per scraper session, but is called with no arguments.
6. **Title Selection Robustness**: In `_parse_job_page`, checking `soup.find("h1")` first and immediately calling `get_text()` on it results in an empty string if `<h1></h1>` is present but contains no text. The selector must fall back to other tags if the matched tag is empty.
7. **Mock Argument Mismatch**: `stealth_scrape_jobs` calls `process_single_job(url, session_id)`, but the test mocks it as `mock_process(url)` which accepts only one parameter.
8. **YAML Boolean Interpretation**: The YAML 1.1 specification defines `on` as a boolean keyword equivalent to `true`. PyYAML parses the unquoted key `on:` as the boolean `True`. Consequently, the python dictionary does not contain the key `"on"`, causing a `KeyError`.
9. **Cascading Import Failure**: `web/app.py` has an unused import `from core.database import Database`. Because `Database` was removed from `core/database.py`, importing `web.app` fails. This prevents `unittest.mock.patch` from inspecting `web.app` for patching, resulting in `AttributeError: module 'web' has no attribute 'app'`.
10. **LinkedIn Scraper Direct Connection**: `search_linkedin_xhr` instantiates its own `curl_cffi` session to make direct network requests, bypassing the mock on `_fetch_url`. In code-only mode, this fetches live results from LinkedIn instead of returning the mocked data.
11. **WAF Text Mismatch**: The Aegis middleware in `core/aegis_shield.py` returns `"Access Denied."`, but the test expects `"Access Denied (Blackholed)."`.
12. **Missing Table & Encoding Crash**:
    - The test `test_campaign_runner_injects_tenant_smtp_to_user_details` executes a query joining the `orders` table, but the test setup never created it.
    - When this database error is thrown, the campaign runner logs the traceback to `campaign_error.txt` using the Windows default encoding (`cp1252`), which cannot encode the `📂` emoji present in the workspace directory path.

---

## 3. Caveats
- No caveats. All 17 failing tests have been audited down to their exact code causes.

---

## 4. Conclusion & Recommendations
We recommend implementing the following targeted modifications in the codebase and test files:

| Target File | Description of Recommended Change | Rationale |
|---|---|---|
| `web/app.py` | Comment out or remove line 32: `from core.database import Database` | Resolves the cascading import error, fixing 4 failures in `test_max_profit_features.py`. |
| `tests/e2e/test_r1_cover_letter.py` | 1. Change the mock target to `"backend.main.generate_smart_cover_letter_stream"`. <br>2. Update `test_r1_t1_generate_cover_letter_queued` to assert a `StreamingResponse` (using `client.stream`) rather than JSON queued status. | Aligns the test with the refactored streaming backend design. |
| `frontend/src/app/layout.tsx` | Change `dir="rtl"` (line 39) to `dir="auto"`. | Fixes layout RTL compliance tests. |
| `tests/e2e/test_r3_scraper.py` | 1. Pass `auth_header` to `test_r3_t1_trigger_scrape_queued` and send `headers=auth_header`. <br>2. Change the profile assertions in `test_r3_t1_stealth_profiles_configured` to check dictionary `id` keys for `"chrome131"` and `"safari18_0"`. <br>3. Pass a session ID to `get_random_proxy("test_session")`. <br>4. Update the local mock `mock_process(url, session_id=None)` in `test_r3_t3_integration_scraper_to_database`. | Aligns E2E tests with endpoint authorization, proxy session requirements, and modern profiles. |
| `scrapers/stealth_ingest.py` | Refactor `_parse_job_page` to loop through title selectors (`h1`, class selectors, `title`) and pick the first element that yields **non-empty** text. | Makes parsing robust against empty `<h1></h1>` tags. |
| `.github/workflows/production.yml` | Change `on:` (line 3) to `"on":` (quoted string). | Prevents PyYAML from parsing `on` as `True`. |
| `core/pa_job_scraper.py` | In `search_linkedin_xhr`, replace the `with httpx_Session(...)` network call with `html_text = self._fetch_url(url)`. | Routes LinkedIn searches through standard proxy channels, allowing clean unit-testing. |
| `core/aegis_shield.py` (or WAF tests) | Change line 285 to return `"Access Denied (Blackholed)."` OR update the test assertions in `tests/test_security_hardening.py` to assert `"Access Denied."`. | Resolves string mismatch in WAF response. |
| `tests/test_tenant_smtp.py` | Create the `orders` table in the `init_db` setup method. | Prevents missing table errors during campaign runner integration tests. |
| `core/campaign_runner.py` | Change line 900 to `with open("campaign_error.txt", "w", encoding="utf-8") as f:`. | Prevents file-writing Unicode encoding crashes on paths with emojis. |

---

## 5. Verification Method
To verify these fixes:
1. Apply the recommended modifications.
2. Run the tests in the workspace directory:
   ```powershell
   $env:PYTHONPATH="."
   python -m pytest tests/
   python -m pytest tests/e2e/
   ```
3. All 173 tests should pass successfully.
