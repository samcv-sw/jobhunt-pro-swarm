# PROJECT: JobHunt Pro Max Overdrive Optimization

## Architecture
JobHunt Pro is a SaaS platform consisting of:
- **Frontend**: Next.js app in `/frontend` using tailwind and CSS variables, supporting RTL/LTR via Logical CSS and Cairo/Tajawal fonts.
- **Backend**: FastAPI app in `/backend` serving endpoints under `/api/v1/*` and integrated with Celery workers for async background operations.
- **Scraper**: Scraping logic located in `/scrapers/stealth_ingest.py` for bypassing anti-bot measures.
- **CI/CD**: GitHub Actions workflow configuration in `.github/workflows/production.yml`.

## Code Layout
- `backend/main.py`: Main FastAPI entrypoint
- `backend/auth.py`: JWT generation, verification and dependencies
- `backend/tasks.py`: Celery tasks
- `backend/sync_worker.py`: Database synchronization worker
- `scrapers/stealth_ingest.py`: Stealth web scraping
- `frontend/src/app/globals.css`: Tailwind configuration and global styles
- `frontend/src/app/layout.tsx`: Root HTML layout importing Cairo and Tajawal fonts and declaring `dir="auto"`
- `frontend/src/app/page.tsx`: Root page containing forms and input elements
- `.github/workflows/production.yml`: GitHub Actions deployment pipeline

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | R1. Frontend UI/UX & RTL Polish | Ensure all CSS/layouts use logical properties, next/fonts for Cairo/Tajawal, dir="auto" on inputs. | None | PLANNED |
| 2 | R2. Backend Concurrency & Sync | Celery tasks concurrency, asyncpg retry mechanism in sync_worker.py. | None | PLANNED |
| 3 | R3. Scraper Stealth Hardening | Upgrade stealth_ingest.py to bypass anti-bot, use profiles/proxies, return structured data. | None | PLANNED |
| 4 | R4. Security Hardening | JWT verification on `/api/v1/*` endpoints, auth routes, session checks. | None | PLANNED |
| 5 | R5. CI/CD Pipeline & E2E Validation | Setup production.yml workflow, run E2E test suite and pass all tests. | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### Auth API
- `POST /api/v1/auth/token` -> exchange credentials for Bearer token
- `GET /api/v1/auth/verify` -> decode and verify token
- `GET /api/v1/dashboard/layout-config` -> retrieve dashboard layout configuration
- `GET /api/v1/dashboard/metrics` -> retrieve dashboard metrics

### Scraper API
- `POST /api/v1/scraper/start` -> start scraper task
- `GET /api/v1/scraper/status/{task_id}` -> query task status
- `POST /api/v1/scrape` -> trigger scraper queue task

### CI/CD API
- `GET /api/v1/cicd/status` -> retrieve CI/CD pipeline configuration status
- `POST /api/v1/cicd/deploy` -> trigger simulated deployment
