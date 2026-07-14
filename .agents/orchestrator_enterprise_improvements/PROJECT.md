# Scope: Enterprise Improvements Round 3

## Architecture
- FastAPI web server (`backend/main.py`)
- Auth engine (`backend/auth.py`)
- Celery tasks (`backend/tasks.py` / `core/tasks.py`)
- Health check endpoints (`backend/main.py`)
- Ban shield / anti-ban (`core/ban_shield.py`, `core/anti_ban.py`)

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Multi-Key JWT Secret Rotation | Decompose auth, verify token using multiple secrets, add tests | None | DONE |
| 2 | M2: Secure CORS Dynamic Origin Validation | Regexp CORS matching in main.py, add tests | None | IN_PROGRESS (b93dec3c-84c2-4265-9bbe-568f4bd0d16a) |
| 3 | M3: Celery Integration & Task Routing | Verify celery task serialization & routing in tests | None | PLANNED |
| 4 | M4: SMTP & External API Connection Health Monitor | SMTP connection check & Groq check in detailed health, add tests | None | PLANNED |
| 5 | M5: Scraper Daily Cap and BanShield Cooldown | Enforce daily scraping limit in anti_ban/ban_shield, add tests | None | PLANNED |
| 6 | M6: Regression Testing | Final full test pass, verify zero regressions | M1, M2, M3, M4, M5 | PLANNED |

## Interface Contracts
### Auth API
- `backend/auth.py`: `verify_token` or equivalent validates signature against any secret from `JWT_SECRET_KEYS`.
### CORS Middleware
- `backend/main.py`: Origin matching uses regex.
### Detailed Health Check
- `GET /api/v1/health/detailed`: Returns `smtp` and `groq_api` status (boolean/string) in the JSON payload.
### Ban Shield / Anti-Ban
- `can_apply_to_company` / `record_scrape` or equivalent: Throws `DailyLimitExceededException` or returns error when cap reached.
