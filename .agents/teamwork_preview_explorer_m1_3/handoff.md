# Handoff Report — Web Routers Auditor (teamwork_preview_explorer_m1_3)

## 1. Observation
1. **Verbatim import errors** from Python when executing `from core.database import db`:
   ```
   ImportError: cannot import name 'db' from 'core.database' (C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\core\database.py)
   ```
2. **Dynamically registered router load failures** observed in uvicorn startup logs during execution of `python -c "from web.app_v2 import app"`:
   - `WARNING:web.app_v2:Failed to dynamically load router candidate: cannot import name 'db' from 'core.database'`
   - `WARNING:web.app_v2:Failed to dynamically load router squads: cannot import name 'db' from 'core.database'`
   - `WARNING:web.app_v2:Failed to dynamically load router webhook_bot: cannot import name 'db' from 'core.database'`
   - `WARNING:web.app_v2:Failed to dynamically load router growth_station: cannot import name 'list' from 'typing' (C:\Users\samde\AppData\Local\Programs\Python\Python312\Lib\typing.py)`
3. **Typo in `web/routers/growth_station.py` line 6**:
   ```python
   from typing import list as List, Optional
   ```
4. **Different SQLite databases paths**:
   - `backend/database.py` line 78:
     ```python
     LOCAL_DB_URL     = os.getenv("LOCAL_DATABASE_URL", "sqlite+aiosqlite:///./data/jobhunt_local.db")
     ```
   - `web/shared.py` line 57:
     ```python
     db_path = getattr(config, "DB_PATH", None) or str(_BASE_DIR.parent / "data" / "jobhunt_saas_v2.db")
     ```
5. **Jinja2Templates duplicates**:
   - `web/shared.py` line 34: `templates = Jinja2Templates(directory=str(template_dir))`
   - `web/app_v2.py` line 178: `templates = Jinja2Templates(directory=str(template_dir))`
   - `web/routers/candidate.py` line 11: `templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))`
6. **Path rewriting by LanguagePrefixMiddleware in `web/app_v2.py`**:
   - `/en/pricing` gets rewritten to `/pricing` in middleware (line 705), preventing requests from hitting the `/en` prefix router (`web/routers/en.py`).
7. **Test suite run result**:
   - Running `test_env\Scripts\pytest` ran 626 tests successfully, none of which imported `web/app_v2.py` or covered web-tier dynamic router loading.

---

## 2. Logic Chain
1. Since `core/database.py` has no `db` instance definition, importing `db` from `core.database` fails. (Observation 1)
2. Because `web/routers/candidate.py`, `web/routers/squads.py`, and `web/routers/webhook_bot.py` attempt to import `db` from `core.database`, their module imports fail. (Observation 2)
3. Because `web/routers/growth_station.py` attempts to import `list` from `typing`, it fails with `ImportError`. (Observation 2, Observation 3)
4. Because `web/app_v2.py` dynamically loads routers using a try-catch block and logs failures as warnings, the app starts successfully but without candidate, squads, webhook_bot, or growth_station endpoints registered. (Observation 2)
5. Because uvicorn rewrites `/en/*` paths to non-prefixed paths before routing, and the `templates` object automatically serves English files for English requests, `web/routers/en.py` is dead code. (Observation 6)
6. Because `backend/database.py` and `web/shared.py` reference two different local SQLite files, user database updates on the frontend are not reflected in background worker queues or APIs in local development. (Observation 4)
7. Because tests in `pytest` do not cover `web/app_v2.py` or web routers, these import errors and failures were completely missed in the test suite execution. (Observation 7)

---

## 3. Caveats
- No changes to any files were implemented, as the mission is strictly a read-only investigation.
- It is assumed that PostgreSQL connections in production use identical environment values (`DATABASE_URL`), meaning data mismatch issues are isolated to local developer SQLite databases.

---

## 4. Conclusion
The web routers dynamic loading is partially broken, rendering the Candidate Profile Honeypot, Job Squads, Webhook Bot, and Growth Station features completely offline. Additionally, redundant routing (`en.py`), divergent template configurations, database desynchronization in development, and test coverage gaps exist. A systematic correction of the `core/database.py` bridge, typing import, template unification, database path matching, and adding a test suite for `web/app_v2.py` will resolve these issues fully.

---

## 5. Verification Method
1. **To verify the import failures**:
   Run:
   ```bash
   python -c "from web.app_v2 import app"
   ```
   Confirm that the uvicorn warning logs show `Failed to dynamically load router candidate`, `Failed to dynamically load router squads`, `Failed to dynamically load router webhook_bot`, and `Failed to dynamically load router growth_station`.
2. **To verify the fix**:
   Once the recommended code changes are applied:
   - Exposing `db` from `core/database.py` referencing `core.async_db.async_db` and adding `db.disconnect = db.close`.
   - Fixing the typing list import in `growth_station.py`.
   - Re-running the command should show no warnings and all routers loaded.
