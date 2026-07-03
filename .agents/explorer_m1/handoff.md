# Diagnostic & Initial Analysis Report — JobHunt Pro

## 1. Observation

### A. Test Execution & Tracebacks
* **Command:** `pytest tests/`
* **Result:** Exit Code 1 (3 Collection Errors)
* **Verbatim Tracebacks:**
  1. `ModuleNotFoundError` during E2E conftest:
     ```
     ERROR collecting tests/e2e
     ...
     tests\e2e\conftest.py:10: in <module>
         from backend.main import app
     E   ModuleNotFoundError: No module named 'backend'
     ```
  2. `ImportError` on backend tests:
     ```
     ERROR collecting tests/test_backend.py
     ...
     E   ImportError: cannot import name 'paramstyle' from 'core.pg_sqlite_shim' (C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\core\pg_sqlite_shim.py)
     ```
  3. `ImportError` on secured backend tests:
     ```
     ERROR collecting tests/test_backend_secured.py
     ...
     E   ImportError: cannot import name 'paramstyle' from 'core.pg_sqlite_shim' (C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\core\pg_sqlite_shim.py)
     ```

### B. Code Style check (Ruff)
* **Command:** `python -m ruff check core/ web/ orchestrator.py config.py`
* **Result:** 547 errors found.
* **Key Verbatim Snippets:**
  * **Module Import Position (E402):**
    ```
    E402 Module level import not at top of file
      --> web\routers\payments.py:15:1
       |
    13 | BOUQUET_PACKAGES_MAP = {b["bouquet"]: b for b in BOUQUET_PACKAGES}
    14 | from payments import get_payment_addresses
    15 | from services.fulfillment import ServiceFulfillment
       | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ```
  * **Bare Excepts (E722):**
    ```
    E722 Do not use bare `except`
      --> web\routers\roast.py:97:17
       |
    95 |                 try:
    96 |                     score = int(score_str)
    97 |                 except:
       |                 ^^^^^^
    98 |                     pass
    ```
  * **Unused/Multiple Imports & Variables (F401, E401, F841):**
    * Unused `sys`, `re` in translation scripts.
    * Multiple statements on one line (E701) in template processing: e.g., `if not f: continue`.

### C. Next.js Build
* **Command:** `npm run build` (inside `frontend/`)
* **Result:** Failed with `exit code 1` due to space/emoji path parsing bug in Windows:
  ```
  Error: Cannot find module 'C:\Users\samde\Desktop\next\dist\bin\next'
  ```
* **Command:** `node node_modules\next\dist\bin\next build` (inside `frontend/`)
* **Result:** Succeeded:
  ```
  ▲ Next.js 16.2.9 (Turbopack)
  ✓ Compiled successfully in 6.8s
  ✓ Generating static pages using 6 workers (5/5) in 1710ms
  ```

### D. Code Quality & Swallowed Exceptions
Based on `BUG_ANALYSIS.md` (which maps core Stack bugs) and manual inspection:
* **`core/campaign_runner.py`**:
  * Line 202: `except Exception as e:` inside `MultiTenantRunner` loading block - logs warning.
  * Line 220: `except Exception as e:` fetching purchased services - logs warning.
  * Line 299: `except Exception as tg_err:` telegram alert - logs debug.
* **`core/email_engine.py`**:
  * `send_email_via_gmail_smtp()` (line 1656 of `BUG_ANALYSIS.md`) returns `(bool, msg_id)`, while other senders return plain `bool`. Truthy tuple checks bypass actual success validation.
  * Event loop leak in `send_sync()` (line 1326): creates `asyncio.new_event_loop()` without calling `.close()`.
  * Hardcoded string boolean `generate_cover_pdf='False'` (line 1001) evaluates as truthy.
* **`core/multi_source_scraper.py`**:
  * Bare excepts/swallowed exceptions on request failures and parsers (e.g. line 212 `except Exception as e:` in `close()`, line 291 in `search()`, line 772, line 785).
* **`core/pa_job_scraper.py`**:
  * Multiple swallowed exception blocks when cache loading/saving fails (lines 229, 253, 311, 404).
* **`core/ai_tailor.py`**:
  * Bare except `except:` at line 906 (swallows exception).
  * Swallowed exceptions during parsing relevance scores.
* **`core/ats_matcher.py`**:
  * Custom `rapidfuzz` fallback implementation (`FakeFuzz`) uses `difflib.SequenceMatcher` when `rapidfuzz` is missing, but doesn't handle all fuzz matching methods natively.
* **`orchestrator.py`**:
  * Does not exist at the root level of the project.
  * `BUG_ANALYSIS.md` mentions that it previously started Uvicorn inside `run_full_cycle()`, causing a blocking loop and port conflict crashes, and that `HealingEngine` initialization exceptions were swallowed at line 600.
* **`config.py`**:
  * Globally hijacks `sqlite3` globally:
    ```python
    import core.pg_sqlite_shim as pg_sqlite_shim
    sys.modules['sqlite3'] = pg_sqlite_shim
    ```
    This lacks standard DB API constants (e.g. `paramstyle`, `apilevel`, `threadsafety`), which breaks third-party packages like `aiosqlite`.

### E. Security Audit Mappings
Mapping of `SECURITY_AUDIT_REPORT_2026-06-05.md` items:
* **C-1: Hardcoded Secrets in Setup Scripts**: Replaced with `os.getenv` in `_setup_gh_secrets.py` and `_set_pa_secret.py` (Completed).
* **C-2 & C-3: Plaintext Secrets in `.env`**: Root `.env` contains API keys, Brevo tokens, and 13 Gmail app passwords in plaintext.
* **H-1: Session Secret Invalidation**: `web/app_v2.py` has been updated (lines 68-70) to raise a `RuntimeError` rather than fall back to a random token when `SECRET_KEY` is missing.
* **H-2: Weak CRON_SECRET Bypass**: `web/app_v2.py` at line 10435 allows query parameter `?key=` matching `CRON_SECRET` to bypass all admin restrictions:
  ```python
  key = request.query_params.get("key") or request.headers.get("X-Cron-Secret")
  expected_key = os.getenv("CRON_SECRET", "")
  if expected_key and key == expected_key: return True
  ```
* **M-1: CSRF Protection**: Lacks token-based CSRF protection (cookie-based only).
* **M-4: Stored XSS via File Upload**: `web/app_v2.py` at lines 4912-4914 parses any non-standard file extensions as plain text instead of blocking them:
  ```python
  else:
      # Try to decode as text
      extracted_text = file_bytes.decode('utf-8', errors='replace')
  ```
* **M-5: Unsanitized HTML Emails**: `web/app_v2.py` `email-test` route does not sanitize body strings, allowing HTML injection.

### F. Next.js/FastAPI Stack & Requirements R1-R5
* **R1 (AI Engine):** `backend/ai_engine.py` supports async generation (`generate_smart_cover_letter`) and streaming via SSE with tone guidelines ("professional", "creative", "confident") via `generate_smart_cover_letter_stream`.
* **R2 (Frontend Dashboard):** `frontend/src/app/dashboard/page.tsx` implements a premium glassmorphic dashboard with live stats (total scrapes, success rate, system load), weekly SVG charting, multi-lingual English/Arabic toggle, and fully RTL-compliant CSS logical properties (e.g. `inlineSize`, `blockSize`, `maxInlineSize`).
* **R3 (Stealth Scraper):** `scrapers/stealth_ingest.py` implements Cloudflare/DataDome bypasses via `curl_cffi` browser impersonation, proxy rotations with session pinning, and an automated verification function mapping to `https://bot.sannysoft.com/`.
* **R4 (Security/Auth):** `backend/main.py` applies `Depends(verify_jwt)` on `/api/v1/*` routes. `backend/auth.py` decodes Bearer tokens using `jwt.decode` with HS256 and `JWT_SECRET_KEY`.
* **R5 (Deployment):** `.github/workflows/production.yml` automates E2E execution by running `pytest tests/e2e/ -v` and frontend build `npm run build` on every push. Corresponding tests exist under `tests/e2e/test_r1_cover_letter.py` through `test_r5_cicd.py`.

### G. Duplicate Files & Cleanup Candidates
* **Legacy stacks:**
  * `frontend-vue/` — Old Vue frontend.
  * `backend-node/` — Old Node.js backend.
* **Backup directories:**
  * `web/templates_backup/` — Copy of templates before translation.
  * `data/backups/` & `data/pa_backups/` — Old DB dumps.
* **Duplicate files & utility scripts in root:**
  * `do_upload.py` and `do_upload2.py`
  * `get_env.py` and `get_env2.py`
  * `fetch_pa_server_log.py`, `fetch_pa_server_log2.py`, and `fetch_pa_server_log3.py`
  * `fix_shell4.py` and `fix_shell5.py`
  * `bot_watchdog.py.disabled` (old unused bot watcher script)
  * `nodriver_collector.py.bak` (old nodriver backup)
  * `JobHuntPro_Release.zip` (stray archive in root)
  * Stray logs: `always_on_loop.log`, `auto_improve.log`, `bot_watchdog.log`, `bot_watchdog_err.log`, `dashboard.log`, `jobhunt.log`, `sam_max.log`, `tg_bot_output.log`

---

## 2. Logic Chain

1. **ModuleNotFoundError during pytest:**
   * *Observation:* Pytest fails with `ModuleNotFoundError: No module named 'backend'`.
   * *Inference:* The tests are run with the current working directory as root, but `backend/` is not on the python path (`PYTHONPATH`). Setting `PYTHONPATH=.` or `PYTHONPATH=./backend` will allow python to discover it.
2. **ImportError for paramstyle in pytest:**
   * *Observation:* Pytest fails with `ImportError: cannot import name 'paramstyle' from 'core.pg_sqlite_shim'`.
   * *Inference:* `config.py` hijacks standard `sqlite3` globally by replacing it with `core.pg_sqlite_shim` at startup. `aiosqlite` imports PEP 249 constants (like `paramstyle`, `apilevel`, `threadsafety`) from `sqlite3`. Since `pg_sqlite_shim.py` does not define these constants, the import fails. Exposing them in `pg_sqlite_shim.py` will fix the import failure.
3. **Next.js Build Failure:**
   * *Observation:* `npm run build` fails in Windows with `Cannot find module 'C:\Users\samde\Desktop\next\dist\bin\next'`. Direct node call `node node_modules\next\dist\bin\next build` succeeds.
   * *Inference:* This is a classic npm CLI whitespace/emoji escape bug in Windows when resolving binary executables inside paths containing spaces/emojis. Invoking the next compiler directly via `node` bypasses the CLI wrapper, proving the code compiles correctly.
4. **Swallowed Exceptions / Bare Excepts:**
   * *Observation:* Code style check flags 547 issues, and `except:` blocks are found in `ai_tailor.py`, `pg_sqlite_shim.py`, and `telegram_bot.py`.
   * *Inference:* The codebase relies heavily on silencing failures to ensure continuous operation on PythonAnywhere. However, this hides database and parsing errors, making troubleshooting difficult.
5. **Security Vulnerabilities:**
   * *Observation:* `verify_system_key()` falls back to `os.getenv("CRON_SECRET")`. `.svg` and `.html` files uploaded via `/upload-cv` are decoded as text without validation.
   * *Inference:* Anyone obtaining the cron secret can bypass admin validation and run force-resets or create tenants. Storing unvalidated text from file uploads poses stored XSS risks.

---

## 3. Caveats

* **No actual changes made:** In alignment with read-only explorer guidelines, no edits were applied to the main codebase.
* **Environment configurations:** Neon DB connection pooling was not directly verified under peak loads due to Code-Only network restrictions.
* **Ruff count:** Ruff results contain a large number of errors (547) primarily from auto-generated translation scripts and template helpers which may be safe to exclude or delete.

---

## 4. Conclusion

1. **Pytest fixes:**
   * Fix the `pg_sqlite_shim.py` file to export all standard `sqlite3` constants:
     ```python
     paramstyle = "qmark"
     apilevel = "2.0"
     threadsafety = 1
     ```
   * Execute pytest with the python path set: `PYTHONPATH=. pytest tests/`.
2. **Next.js Build:**
   * Document in deployment scripts to use direct node invocation (`node node_modules/next/dist/bin/next build`) to prevent path escaping bugs on Windows systems.
3. **Security Hardening:**
   * Migrate query-string `?key=` bypasses to strong headers or Bearer tokens.
   * Limit file uploads strictly to validated MIME types (`application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`).
4. **Cleanup:**
   * Safely delete Vue/Node.js legacy folders, template backups, and redundant utility scripts from the root directory to reduce clutter.

---

## 5. Verification Method

### Test Command
```powershell
# Run with PYTHONPATH set to local directory
$env:PYTHONPATH="."
pytest tests/
pytest tests/e2e/
```

### Next.js build verification
```powershell
cd frontend
node node_modules\next\dist\bin\next build
```

### Files to inspect for pg_sqlite_shim constants
* Inspect `core/pg_sqlite_shim.py` to verify if standard constants are exposed.
