# Project: JobHunt Pro SaaS Improvements

## Architecture
- **Backend**: FastAPI web app (`backend/main.py`), using Uvicorn. Auth via JWT (`backend/auth.py`), AI capabilities via `backend/ai_engine.py` (Groq API).
- **Frontend**: Next.js app inside `frontend/` directory. Dashboard page at `frontend/src/app/dashboard/page.tsx`. Glassmorphism CSS, Arabic fonts (Cairo/Tajawal), CSS Logical Properties, responsive design.
- **Scrapers**: python-based stealth scrapers inside `scrapers/stealth_ingest.py`. TLS spoofing, proxy rotation, bypassing bot detection.
- **Testing**: pytest E2E suite inside `tests/e2e/`. Runs inside GitHub Actions `.github/workflows/production.yml`.

## Milestones
| # | Name | Scope | Dependencies | Status | Conversation ID | Working Directory |
|---|------|-------|-------------|--------|-----------------|-------------------|
| M1 | E2E Testing Track | Design and build E2E test suite (Tiers 1-4), publish `TEST_READY.md` | None | IN_PROGRESS | 855a740f-b778-4a31-a624-5bb01909028b | .agents/sub_orch_e2e_testing_v2 |
| M2a | Backend Implementation | Groq streaming cover letters (R1), JWT Auth on `/api/v1/*` (R4) | None | IN_PROGRESS | 71f9b26d-0d9b-4b92-8951-f23208fbee7e | .agents/sub_orch_backend_v2 |
| M2b | Frontend Implementation | Next.js glassmorphism dashboard (R2) | None | IN_PROGRESS | c3f33a57-b110-4914-b2f0-80e0fe12857b | .agents/sub_orch_frontend_v2 |
| M2c | Scraper Implementation | Stealth scraper bot bypass (R3) | None | IN_PROGRESS | 91a89750-dc39-4cf9-99b5-ef045797079c | .agents/sub_orch_scraper_v2 |
| M3 | Final Verification & Hardening | Pass 100% E2E tests (Tiers 1-4) & Tier 5 Adversarial Hardening | M1, M2a, M2b, M2c | PLANNED | TBD | .agents/sub_orch_final_milestone |

## Interface Contracts
### FastAPI Auth ↔ Client
- Endpoint: `/api/v1/auth/token` (or login) returning JWT.
- Header: `Authorization: Bearer <token>` required for all `/api/v1/*` endpoints.
- Error: 401 Unauthorized for invalid/missing token.

### Groq Streaming ↔ Client
- Endpoint: `/api/v1/ai/generate-cover-letter` (or similar) returning EventStream (Server-Sent Events) chunk-by-chunk.

## Code Layout
- `backend/` - FastAPI backend application files
  - `backend/main.py`
  - `backend/auth.py`
  - `backend/ai_engine.py`
- `frontend/` - Next.js frontend application files
  - `frontend/src/app/dashboard/page.tsx`
- `scrapers/` - Scrapers
  - `scrapers/stealth_ingest.py`
- `tests/` - Tests
  - `tests/e2e/`
- `.github/workflows/production.yml` - CI/CD pipeline configuration
