# Web Routers & Frontend Serving Audit Report

## 1. Executive Summary
A comprehensive read-only audit of the FastAPI web routers (`web/routers/*.py`) and frontend serving endpoints (`web/app_v2.py`) has revealed critical structural, configuration, and logical defects. The most severe issues include broken dynamic router loading due to missing database manager instances and incorrect imports, template engine duplication, dead language routing code, database file paths divergence, and lack of integration tests for the web tier.

---

## 2. Evidence Chain & Critical Findings

### Finding A: Missing `db` Instance in `core/database.py` (Broken Routers)
- **Observation**:
  - `web/routers/candidate.py` (line 7), `web/routers/squads.py` (line 8), and `web/routers/webhook_bot.py` (line 8) all import `db` from `core.database` and attempt to acquire connections asynchronously (e.g., `async with db.pool.acquire() as conn:`).
  - Checking `core/database.py` reveals that the `Database` class is defined for backward compatibility, but **no `db` instance is ever instantiated or exported**.
  - `core/async_db.py` contains the modern async database connection pool `async_db` (an instance of `AsyncDatabase`), but this is not mapped or exported under `core.database`.
  - On application startup (`web/app_v2.py`), the dynamic router loading module catches and swallows import/load errors, logging warnings:
    ```
    WARNING:web.app_v2:Failed to dynamically load router candidate: cannot import name 'db' from 'core.database'
    WARNING:web.app_v2:Failed to dynamically load router squads: cannot import name 'db' from 'core.database'
    WARNING:web.app_v2:Failed to dynamically load router webhook_bot: cannot import name 'db' from 'core.database'
    ```
- **Impact**: The candidate profile honeypot, user squads, and social media webhook bot endpoints are completely offline and broken.

### Finding B: Syntax/Import Error in `web/routers/growth_station.py`
- **Observation**:
  - `web/routers/growth_station.py` line 6 contains the import:
    ```python
    from typing import list as List, Optional
    ```
  - Running Python raises `ImportError: cannot import name 'list' from 'typing'` because `list` is a built-in type in Python and cannot be imported from `typing` (the correct capitalized class is `List`).
  - On application startup, the router fails to load:
    ```
    WARNING:web.app_v2:Failed to dynamically load router growth_station: cannot import name 'list' from 'typing'
    ```
- **Impact**: The growth station lead-generation and email outreach automation endpoints are completely offline and broken.

### Finding C: Dead Code Router (`web/routers/en.py`)
- **Observation**:
  - `web/routers/en.py` registers public English routes with the prefix `/en` (e.g., `/en/pricing`, `/en/login`).
  - However, `LanguagePrefixMiddleware` in `web/app_v2.py` (lines 704-707) intercepts all requests starting with `/en` and rewrites the request path by stripping the prefix (e.g., `/en/pricing` becomes `/pricing?lang=en`).
  - This path rewriting happens before FastAPI routing. Therefore, incoming `/en/` requests never match the prefixed routes in `en.py`. Instead, they match the Arabic paths (like `/pricing`) and render English templates automatically using the custom patched `TemplateResponse` from `web/shared.py`.
- **Impact**: The entire `web/routers/en.py` file is redundant dead code that is never matched or executed.

### Finding D: Duplicated Template Engines & Inconsistent Configurations
- **Observation**:
  - `web/shared.py` (line 34) instantiates a `Jinja2Templates` instance and patches `templates.TemplateResponse` to auto-translate and handle language folders (`en/`).
  - `web/app_v2.py` (line 178) instantiates **another** `Jinja2Templates` instance and patches `templates.TemplateResponse` again with a custom handler.
  - `web/routers/candidate.py` (line 11) instantiates a **third** `Jinja2Templates` instance and does not patch it at all.
- **Impact**: Leads to memory bloat, inconsistent translation functions rendering across routes, and templates serving without context variables like `lang` or `dir` depending on which template instance is invoked.

### Finding E: Database Layer Bifurcation & State Desynchronization
- **Observation**:
  - **Backend API (`backend/database.py`)** uses SQLAlchemy `AsyncSessionLocal` pointing to `sqlite+aiosqlite:///./data/jobhunt_local.db` in SQLite mode.
  - **Web App (`web/shared.py`)** uses a custom synchronous SQLite connection pointing to `data/jobhunt_saas_v2.db`.
- **Impact**: During local development, the backend and web apps write to and read from completely different SQLite database files. Actions performed on the web UI (like signing up) are invisible to backend worker queues and APIs, resulting in broken local testing.

### Finding F: Zero Test Coverage for Web App & Routers
- **Observation**:
  - Run logs for the 626 test cases in the `pytest` test suite show that the tests only cover the Next.js frontend code (CSS/JSX rules) and the backend REST API (`backend/main.py`).
  - The web application entrypoint (`web/app_v2.py`) and the `web/routers/` are never imported or ran in tests. This explains why the 626 tests passed with 100% success despite 4 web routers failing to import on server startup.

---

## 3. Todos, Placeholders, & Mocks Audit

| File | Line | Content / Context | Action Required |
|---|---|---|---|
| `web/app_v2.py` | 5051 | `"""Placeholder Premium page for Email Test."""` | Implement actual premium validation page or redirect to checkout. |
| `web/app_v2.py` | 6407 | `6. Education placeholder` | Replace with actual educational parsing schema/model logic. |
| `web/app_v2.py` | 9093 | `opened = sent_status.get("opened", sent_status.get("sent", 0) // 3)  # ~33% open rate placeholder` | Remove hardcoded mock rate and fetch real campaign email opens. |
| `web/routers/admin.py` | 491 | `Contains {empty_links} empty placeholder link (#)` | Good diagnostic scan but templates should have real relative links. |
| `web/routers/b2b_api.py` | 26-46 | Mock aggregated insights (e.g. "AI Prompt Engineer") | Replace with real aggregate query grouping by `jobs.title` and `jobs.created_at`. |

---

## 4. Proposed Optimization & Cleanup Strategy

### Phase 1: Fix Core Import & Startup Blocks
1. **Fix `core/database.py`**:
   Expose `db` by pointing to `async_db` from `core.async_db` and aliasing `disconnect` to `close` for compatibility with the main uvicorn app lifespan shutdown:
   ```python
   # Add to core/database.py (backward compatibility bridge)
   from core.async_db import async_db as db
   # Bridge uvicorn lifespan disconnect call
   db.disconnect = db.close
   ```
2. **Fix `growth_station.py`**:
   Correct the typing import:
   ```python
   # web/routers/growth_station.py line 6
   from typing import List, Optional  # Changed lowercase list to uppercase List
   ```

### Phase 2: Consolidate Template Engine and Remove Dead Code
1. **Consolidate Jinja2 Templates**:
   Remove `templates = Jinja2Templates(...)` instantiations from `web/app_v2.py` and `web/routers/candidate.py`. All routers and entrypoints must import the single source of truth:
   ```python
   from web.shared import templates, render_template
   ```
2. **Delete Dead Router**:
   Delete `web/routers/en.py` from the directory, as language translation and template selection is already handled globally by `LanguagePrefixMiddleware` and `web/shared.py`'s template patcher.

### Phase 3: Unify Database Layer Configuration
1. **Unify SQLite Path**:
   Align the SQLite file names so that both the backend database configuration (`backend/database.py`) and web app configuration (`web/shared.py` / `config.py`) read from the same SQLite file path (e.g., `data/jobhunt_saas_v2.db`) for consistent local development and debugging.

### Phase 4: Refactor App Monolith `/user-dashboard`
1. **Extract `/user-dashboard`**:
   Move the massive `/user-dashboard` route handler and its background process triggers from `web/app_v2.py` to `web/routers/dashboard.py`. Point uvicorn/fastapi directly to the dashboard router and remove uvicorn background execution from the main file, reducing the file footprint of `web/app_v2.py` by over 1,500 lines.

### Phase 5: Add Web Integration Tests
1. **Add `tests/test_web_app.py`**:
   Add a pytest client that loads `web.app_v2:app` and hits key frontend/serving routes, ensuring that router failures are caught immediately by CI/CD instead of failing silently.
