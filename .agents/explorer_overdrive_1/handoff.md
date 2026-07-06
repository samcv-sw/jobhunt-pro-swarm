# Explorer Investigation Report

## 1. Observation
When invoking the E2E test suite using raw `pytest tests/e2e/` from the root directory `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`, the command fails during test collection with the following error:
```
ImportError while loading conftest 'C:\Users\samde\Desktop\\U0001f4c2 Folders & Projects\cv sam new ma3 kimi\tests\e2e\conftest.py'.
tests\e2e\conftest.py:10: in <module>
    from backend.main import app
E   ModuleNotFoundError: No module named 'backend'
```
However, running the command as `python -m pytest tests/e2e/` or setting `PYTHONPATH=.` yields:
```
============================ 77 passed in 3.23s ==============================
```
Additionally, running the full test suite via `python -m pytest tests/` compiles and runs successfully:
```
============================ 152 passed in 10.36s =============================
```

The files relevant to requirements **R1-R5** show the following configurations:
*   **R1: Frontend Polish**
    *   `frontend/src/app/globals.css`: Contains CSS logical properties exclusively. Defines `--font-arabic`, base font size `16px`, and line-height `1.8`. Includes `.dir-icon { transform: scaleX(var(--text-x-direction)); }` for RTL mirroring.
    *   `frontend/src/app/layout.tsx`: Configures `Cairo` and `Tajawal` fonts, and wraps layout with `dir="auto"` on the root `<html>` tag.
    *   `frontend/src/app/page.tsx`: Uses glassmorphic design and specifies `dir="auto"` on all inputs (`tenant-name-input`, `smtp-email-input`, `smtp-pass-input`).
*   **R2: Backend Concurrency & Database Sync**
    *   `backend/sync_worker.py`: Monitors the outbox table and replicates SQLite mutations to PostgreSQL. Catches connection errors gracefully with `except asyncpg.PostgresConnectionError as e:` and standard `Exception`, retrying after 30 seconds.
    *   `backend/main.py`: Dispatches heavy Celery tasks off-thread using `asyncio.to_thread` (e.g. `await asyncio.to_thread(scrape_jobs.delay, ...)`), keeping the ASGI event loop unblocked (<30ms loop delay).
    *   `backend/tasks.py` & `backend/celery_app.py`: Handle Celery task queues, task routing, and native exponential backoff + retries.
*   **R3: Scraper Stealth Hardening**
    *   `scrapers/stealth_ingest.py`: Utilizes `curl_cffi` for TLS fingerprinting / impersonation, with progressive fallback layers to `NodriverFallback` and `ApexCamoufoxFallback` on bot challenges. Returns a structured `list[dict]` containing at minimum `title` and `url`.
*   **R4: Security Hardening**
    *   `backend/auth.py` & `backend/main.py`: All `/api/v1/*` endpoints are protected by JWT Bearer token authentication via the `Depends(verify_jwt)` dependency.
*   **R5: E2E Test Suite Validation**
    *   `.github/workflows/production.yml`: The CI/CD pipeline runs Python 3.12 for backend tests (`python -m pytest tests/e2e/ -v`) and Node.js 20 for the Next.js frontend build (`npm run build`).

## 2. Logic Chain
1. Calling raw `pytest tests/e2e/` fails because Python's module search path does not include the project root. This results in the `ModuleNotFoundError` for `backend` when `tests/e2e/conftest.py` is loaded.
2. When executing via `python -m pytest tests/e2e/` or prefixing with `PYTHONPATH=.`, Python automatically includes the current working directory in the search path.
3. The 17 original E2E tests (spread across `test_database.py` [4 tests], `test_e2e_backend.py` [6 tests], and `test_frontend.py` [7 tests]) and the 60 new E2E tests (totaling 77 tests) are fully compliant and pass.
4. Hence, to enable developers to execute direct `pytest` commands without python `-m` or manual path exports, we need to declare the project root as a path source for the test environment.

## 3. Caveats
*   No codebase source files were modified, in line with the read-only constraint.
*   Assumes a local environment setup where dependencies (like `jwt`, `asyncpg`, etc.) are installed.

## 4. Conclusion
*   All 77 E2E tests (including the 17 core tests) pass successfully under correct path execution.
*   The failures are purely import-path configuration issues related to the execution environment.
*   **Proposals**:
    1.  Add `pythonpath = .` under the `[pytest]` header of `pytest.ini`.
    2.  Alternatively, append the root directory to `sys.path` in `tests/e2e/conftest.py` prior to the backend imports:
        ```python
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        ```

## 5. Verification Method
*   Run the E2E tests:
    ```powershell
    python -m pytest tests/e2e/
    ```
*   Verify that `frontend/src/app/globals.css` strictly uses CSS Logical Properties (returns zero matches for physical property search).
*   Verify that `frontend/src/app/page.tsx` has `dir="auto"` on all input fields.
