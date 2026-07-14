# Plan - JobHunt Pro Enterprise Improvements (Round 3)

We are implementing the third set of enterprise-grade security, performance, reliability, and monitoring improvements for JobHunt Pro.
Our plan decomposes this into 6 milestones, following the Project Pattern. Each milestone will be executed using the Explorer -> Worker -> Reviewer -> Challenger -> Auditor cycle.

## Milestones

### Milestone 1: Multi-Key JWT Secret Rotation (R1)
- **Objective**: Support multiple active JWT secret keys loaded from `JWT_SECRET_KEYS` (comma-separated list).
- **Files**: `backend/auth.py`, and unit tests in `tests/test_auth.py` (or similar auth test file).
- **Scope**:
  - Read `JWT_SECRET_KEYS` from env. Fall back to `JWT_SECRET_KEY` (and then test key).
  - Use the first key in the list as the primary key for signing new tokens.
  - When verifying a token, attempt validation with the primary key first. If it fails, attempt verification with the remaining keys in the list.
  - Write at least 2 unit tests: (a) tokens signed with the old secret still pass verification after a new key is added as primary, (b) tokens signed with an invalid key are rejected.

### Milestone 2: Secure CORS Dynamic Origin Validation (R2)
- **Objective**: Securely validate incoming request origins dynamically using strict regex-based origin matching.
- **Files**: `backend/main.py`, and unit tests in `tests/test_cors.py` (or similar).
- **Scope**:
  - Implement a helper for regex-based origin matching.
  - Subdomain wildcards (e.g. `https://*.jobhunt-pro.com`) must only match valid subdomains and map to `^https://[a-zA-Z0-9-]+\.jobhunt-pro\.com$`.
  - Reject malformed origins or generic wildcard subversion attempts (e.g., `https://attacker-jobhunt-pro.com`).
  - Write at least 2 unit tests: (a) valid matching origins (including allowed subdomains) are allowed, (b) malformed origins are rejected.

### Milestone 3: Celery Integration & Task Routing Verification (R3)
- **Objective**: Verify Celery task serialization and routing.
- **Files**: Create `tests/test_celery_integration.py`.
- **Scope**:
  - Mock the celery broker.
  - Check that calls to `scrape_jobs.delay()` and `generate_cover_letter.delay()` properly serialize arguments to JSON and map to their designated queues.
  - Verify that task parameters conform to their expected types.

### Milestone 4: SMTP & External API Connection Health Monitor (R4)
- **Objective**: Report SMTP connectivity and Groq API status in the detailed health check payload.
- **Files**: `backend/main.py`, and unit tests.
- **Scope**:
  - Extend `GET /api/v1/health/detailed`.
  - SMTP check: quick TCP connection test to the configured host/port with tight timeout (<1s), failing gracefully.
  - Groq API check: lightweight check (GET status page or a zero-token request) with tight timeout (<1s), failing gracefully.
  - Write at least 2 tests verifying that SMTP and API statuses are reported.

### Milestone 5: Scraper Daily Cap and BanShield Cooldown Enforcement (R5)
- **Objective**: Enforce daily scraping limits and cooldown rules strictly, raising `DailyLimitExceededException` or returning a distinct error status once reached.
- **Files**: `core/ban_shield.py` or `core/anti_ban.py`, and unit tests.
- **Scope**:
  - Check daily cap before attempting scrapes.
  - Reset daily counter on day boundary.
  - Raise `DailyLimitExceededException` or return distinct error status if limit is hit.
  - Write at least 2 unit tests verifying the cap enforcement and the day boundary reset.

### Milestone 6: Regression Testing & Final Verification (R6)
- **Objective**: Run the full test suite (all 431+ tests) and confirm 100% success with zero regressions.
- **Files**: Entire test suite.
- **Scope**:
  - Run all tests.
  - Ensure zero warnings/failures.
