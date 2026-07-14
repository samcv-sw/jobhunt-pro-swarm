# JobHunt Pro — Initial Codebase Exploration Report

## Executive Summary
This report documents the initial codebase investigation of the JobHunt Pro platform. We analyzed the backend routes accessing the SQLite database to identify query performance bottlenecks and error handling gaps; evaluated the frontend Next.js landing pages, dashboard, and components for RTL/LTR compatibility, CSS logical properties, and Gulf region typography; and examined the test suite configuration (608 test cases) and OpenAPI contract verification.

---

## 1. Backend SQLite Database Investigation

### 1.1 Database Schema & Connection Strategy
The application uses a **local-first** approach managed in `backend/database.py` and `backend/models.py`. It resolves connection URLs in priority order:
1. **Turso D1 Edge DB** (`TURSO_DATABASE_URL` via `sqlite+aiosqlite` with LibSQL extensions).
2. **PostgreSQL / Neon** (`DATABASE_URL` sync/async formatted with Neon-pooler and PgBouncer compliance).
3. **Local SQLite File** (`LOCAL_DATABASE_URL` defaulting to `./data/jobhunt_local.db`).

The SQLAlchemy Base metadata models defined in `backend/models.py` are:
* **`User`**: Core user accounts containing authentication and profile state.
* **`Account`**: Core tenant balance and currency ledger (Credits).
* **`Transaction`**: Standard financial ledger state tracking (PENDING, COMPLETED, FAILED, REVERSED).
* **`LedgerEntry`**: Double-entry bookkeeping ledger details.
* **`SyncOutbox`** (`ps_crud_outbox`): Local-first outbox sync buffer to stream changes from SQLite to Neon PostgreSQL.
* **`Subscription`**: Customer subscription tiers (Free, Pro, Enterprise).
* **`Usage`**: Scraper/AI limits tracking per tenant per billing period.
* **`CoverLetterToneResult`**: A/B testing records matching job/application feedback.

Additionally, a legacy SQL schema is defined in `infra/init.sql` and utilized in the massive `web/app_v2.py` (which includes dynamically registered routers from `web/routers/`):
* Tables include `users`, `cv_profiles`, `orders`, `campaigns`, `campaign_emails`, `wallet_transactions`, `redeem_codes`, `referrals`, `email_quota`, `daily_logins`, `flash_sales`, `purchased_services`, `manual_emails`, and `suppression_list`.

---

### 1.2 Performance Bottlenecks & Gaps

#### Bottleneck 1: N+1 UPDATE Queries in DLQ Requeue (`backend/main.py`)
* **File Path**: `backend/main.py:664-685`
* **Observation**: In the dead-letter queue (DLQ) requeuer endpoint `dlq_requeue`, the code queries stale outbox IDs and then updates them inside a loop:
  ```python
  stale_ids = [row[0] for row in result.fetchall()]
  if stale_ids:
      for sid in stale_ids:
          await session.execute(
              text("UPDATE sync_outbox SET synced = 0 WHERE id = :sid"),
              {"sid": sid}
          )
      await session.commit()
  ```
* **Performance Impact**: Creates N separate roundtrips to update records individually instead of executing a bulk operation.
* **Recommendation**: Perform a single bulk update:
  ```python
  await session.execute(
      text("UPDATE sync_outbox SET synced = 0 WHERE id IN :sids"),
      {"sids": tuple(stale_ids)}
  )
  ```
  Even better, skip the select entirely and run the update directly:
  ```python
  await session.execute(
      text("UPDATE sync_outbox SET synced = 0 WHERE synced = 0 AND created_at < :cutoff"),
      {"cutoff": cutoff.isoformat()}
  )
  ```

#### Bottleneck 2: Redundant DB Update & Missing Column in DLQ Requeue (`backend/main.py`)
* **File Path**: `backend/main.py:660-686`
* **Observation**: 
  1. The SELECT statement retrieves records where `synced = 0` (`WHERE synced = 0 AND created_at < :cutoff`). The loop then updates them to `synced = 0`. Setting a value that is already `0` to `0` is a logic bug that executes redundant operations without changing state.
  2. The code comment states: `# touch updated_at to signal a fresh attempt`. However, looking at the `SyncOutbox` model in `backend/models.py`, there is **no `updated_at` column** defined. The query only updates `synced = 0`.
* **Impact**: Silent logic bug.
* **Recommendation**: Add an `updated_at` column to `SyncOutbox` or update `created_at = CURRENT_TIMESTAMP` to actually touch the timestamp, or change the logic if the worker marks failed items with a status other than `0`.

#### Bottleneck 3: N+1 Database Session and Commit in Webhooks (`backend/main.py`)
* **File Path**: `backend/main.py:1002-1060` (inside `brevo_bounce_webhook` and `sendgrid_bounce_webhook`)
* **Observation**: In both webhook handlers, incoming email bounce events are iterated in a loop. For each event, a brand-new database session is opened, executed, and committed:
  ```python
  for event in events:
      email = event.get("email")
      if email ...:
          async with async_session() as session:
              await session.execute(
                  _text("UPDATE users SET email_bounced = 1 WHERE email = :email"),
                  {"email": email}
              )
              await session.commit()
  ```
* **Performance Impact**: Instantiates N connection sessions and N separate transaction commits, severely bottlenecking performance under web hook batches.
* **Recommendation**: Bind a single transaction context around the loop:
  ```python
  async with async_session() as session:
      for event in events:
          email = event.get("email")
          if email:
              await session.execute(
                  _text("UPDATE users SET email_bounced = 1 WHERE email = :email"),
                  {"email": email}
              )
      await session.commit()
  ```

#### Bottleneck 4: Unindexed Group-By Query on Users (`backend/main.py`)
* **File Path**: `backend/main.py:1193-1206` (inside `get_referral_analytics`)
* **Observation**: The endpoint executes:
  ```sql
  SELECT referred_by, COUNT(*) as count FROM users WHERE referred_by IS NOT NULL GROUP BY referred_by
  ```
* **Performance Impact**: The `referred_by` column on the `users` table does not have an index (see `backend/models.py`). This query forces a full table scan and database sorting on every request, leading to performance degradation as user counts increase.
* **Recommendation**: Add a database index on the `referred_by` column:
  ```python
  referred_by = Column(String, nullable=True, index=True)
  ```

#### Bottleneck 5: Unindexed Tracking Query on Applications (`backend/main.py`)
* **File Path**: `backend/main.py:1212-1247` (inside `track_email`)
* **Observation**: The signed email tracking pixel handler executes:
  ```sql
  UPDATE applications SET opened = 1, opened_at = CURRENT_TIMESTAMP WHERE tracking_id = :tid
  ```
* **Performance Impact**: The `applications` table does not have a database index on `tracking_id` (only a composite index on `opened, responded, status` is present in `001_performance_indices.sql`). Every tracking pixel request causes a full table scan of applications.
* **Recommendation**: Create an index specifically on the `tracking_id` column of the `applications` table:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_applications_tracking_id ON applications(tracking_id);
  ```

#### Bottleneck 6: Sequential Queries in Legacy Dashboard Router (`web/routers/dashboard.py`)
* **File Path**: `web/routers/dashboard.py:31-34`
* **Observation**: The dashboard endpoint queries multiple statistics sequentially using separate query calls:
  ```python
  row1 = conn.execute("SELECT COALESCE(SUM(sent_count), 0) FROM campaigns WHERE user_id = ?", (user_id,)).fetchone()
  row2 = conn.execute("SELECT COUNT(*) FROM campaigns WHERE user_id = ? AND status = 'running'", (user_id,)).fetchone()
  row3 = conn.execute("SELECT COUNT(*) FROM campaigns WHERE user_id = ? AND status = 'completed'", (user_id,)).fetchone()
  row4 = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
  ```
* **Performance Impact**: Sequential query latency over SQLite connections, creating blocking overhead.
* **Recommendation**: Combine statistical queries using conditional aggregation:
  ```sql
  SELECT 
      COALESCE(SUM(sent_count), 0) AS total_sent,
      SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) AS running_count,
      SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_count
  FROM campaigns WHERE user_id = ?
  ```

---

## 2. Frontend Layout & Styling Investigation

### 2.1 Frontend Structures
The principal frontend dashboard is a Next.js (TypeScript, React, App Router) application located in `frontend/src`. A secondary single-page React client is in `dashboard/` (Vite, React, TS), a legacy Vue application is in `frontend-vue/` (Vite, Vue), and static HTML pages are in `static_webapp/`. 

Inside `frontend/src`:
* **`app/layout.tsx`**: Standard layout importing Google Fonts Cairo (`--font-cairo`) and Tajawal (`--font-tajawal`), initializing the localization wrapper `LocaleProvider`, implementing dark mode resolution script (prevents flash), and registering the PWA service worker `sw.js`.
* **`app/page.tsx`**: Main Landing/Home Page. Simulates sharding hashing algorithms, browser WebAssembly SQLite, and custom SMTP validation, with integrated status telemetry.
* **`app/dashboard/page.tsx`**: Main App Dashboard. Displays scrape records, live metrics, a custom SVG area chart, and and dynamic Arabic translation widgets.

---

### 2.2 Translation & Bi-lingual RTL/LTR Layout System
* **Locale Provider**: Managed in `frontend/src/app/locale-context.tsx`. It provides the `useLocale()` hook.
* **Synchronization**: On toggle, the provider syncs:
  1. `document.documentElement.lang` to `ar` or `en`.
  2. `document.documentElement.dir` to `rtl` or `ltr`.
  3. Updates the custom CSS property `--text-x-direction` to `-1` (for `ar`) or `1` (for `en`).
* **Text Selection**: Components pull translation keys from local translation dictionaries `t` using `isArabic ? arabic_val : english_val`.
* **RTL Mirroring**: Interactive layouts dynamically adjust using `dir={isArabic ? "rtl" : "ltr"}`. Arrows and directional icons utilize:
  ```css
  .dir-icon {
    display: inline-block;
    transform: scaleX(var(--text-x-direction));
  }
  ```
  This automatically mirrors icons on language change without breaking logical UI layout structure.

---

### 2.3 CSS Logical Properties usage
The layout styles defined in `globals.css` and applied inline in the components strictly conform to **CSS Logical Properties** to ensure LTR/RTL safety:
* **Block Dimensions**: Uses `min-block-size: 100vh` and `block-size` instead of `height` (`width` mapped to `inline-size`).
* **Paddings & Margins**: Uses logical padding/margin directions:
  * `padding-block: 0.6rem; padding-inline: 1.25rem;` in `.btn-gold`.
  * `padding-block: 0.6rem; padding-inline: 1rem;` in `.input-field`.
  * `padding-block: 0.75rem; padding-inline: 1rem;` in `.stat-card`.
* **Centering and Spacing**: Uses logical directions: `margin-inline-start`, `margin-inline-end`, `margin-block-start`, and `margin-block-end` instead of physical `left` or `right`.

---

### 2.4 Typography Details
* **Fonts**: Placed in `globals.css`:
  ```css
  --font-arabic: var(--font-cairo), var(--font-tajawal), 'IBM Plex Arabic', sans-serif;
  body {
    font-family: var(--font-arabic);
  }
  ```
* **Base Metrics**: Base font size `--font-size-base` is `16px` with a line-height `--line-height-base` of `1.8`.
* **RTL Letter-Spacing Neutralization**: In RTL layout, standard English letter-spacing renders Arabic text unreadable. The framework explicitly neutralizes this:
  ```css
  [dir="rtl"], [dir="rtl"] *, [lang="ar"], [lang="ar"] * {
    letter-spacing: normal !important;
  }
  ```
* **Arabic Legibility Rule**: Sub-16px font sizes in Arabic are difficult to read due to script details. The CSS overrides all small text sizes in RTL mode:
  ```css
  [dir="rtl"] .text-sm, [dir="rtl"] .text-xs, [dir="rtl"] .text-\[10px\] {
    font-size: 16px !important;
  }
  ```
  This guarantees that all text components maintain a minimum size of `16px` in Arabic mode, ensuring legibility.

---

## 3. Test Suite & OpenAPI Schema Verification

### 3.1 Test Suite Configuration
* **Discovery Config**: Configured in `pytest.ini` and `pyproject.toml`. It defines:
  ```ini
  testpaths = tests
  python_files = test_*.py
  pythonpath = .
  ```
* **Database Isolation**: The `tests/conftest.py` file sets up a temporary local SQLite database (`./data/jobhunt_test.db`), runs schemas on initialization (`Base.metadata.create_all`), and deletes the file at session cleanup. It clears `TURSO_DATABASE_URL` so that tests run completely in isolation without hitting D1 cloud databases.
* **Rate Limit Bypass**: `conftest.py` defines `reset_rate_limiter_global` which automatically resets the API rate limiter and increases the limit (`rate_limiter.requests_limit = 100000`) for non-rate-limit tests, preventing cross-test IP lockouts.
* **E2E Mock Router**: In `tests/e2e/conftest.py`, a mock router overrides FastAPI's `app.routes` using a pytest fixture `use_mocked_routes` for testing `/auth/token`, `/ai/generate-cover-letter/stream`, `/dashboard/metrics`, `/scraper/start`, `/scraper/status/{task_id}`, and `/cicd/deploy`.

---

### 3.2 Running & Verifying Tests
To run and verify the 608 test cases:
1. Ensure the default python environment is loaded (packages including `pytest` 9.0.3 and `pytest-asyncio` 1.3.0 are installed).
2. Run test collection to verify the count of tests:
   ```bash
   pytest --collect-only
   ```
   *Expected Output*: `608 tests collected`
3. Execute the full test suite:
   ```bash
   pytest
   ```
4. Run only fast unit tests:
   ```bash
   pytest -m "unit"
   ```

---

### 3.3 OpenAPI Schema Verification
The OpenAPI contract schema is validated via `tests/test_api_contract.py`.
* **Methodology**: It spins up a `TestClient` using the FastAPI `app` from `web.app_v2` and gets the schema object by calling `app.openapi()`.
* **Assertions**:
  1. Checks for standard keys: `"openapi"`, `"info"`, `"paths"`, and `"components"`.
  2. Asserts the presence of key endpoints: `"/upload-cv"`, `"/api/v2/cloud-tick/status"`, and `"/api/v1/login"`.
  3. Verifies that the openapi version starts with `"3."` (i.e. OpenAPI 3.x specification).
