# Project: JobHunt Pro SaaS - 24/7 Autonomous Empire

## Architecture
JobHunt Pro SaaS is a 100% $0 cloud-native, 24/7 autonomous SaaS platform featuring:
1. **Cloud Architecture & Resilience**:
   - 24/7 continuous operation on $0 free-tier cloud infrastructure (Vercel, Render, Cloudflare, GitHub Actions Cron, Supabase/Neon).
   - `core/pg_sqlite_shim.py` & `core/database.py` with automatic cloud PostgreSQL detection & seamless local SQLite fallback.
   - Keep-alive cron workflows (`.github/workflows/keepalive.yml`) executing sub-5s ticks.
2. **Dual-Channel B2B Lead Gen & Automated Outreach Swarm**:
   - Autonomous lead scraper & enrichment module for corporate hiring managers (`backend/services/lead_scraper.py`, `backend/routers/leads.py`).
   - Multi-step personalized cold email sequence generator & dispatch tracking (`backend/services/cold_email_generator.py`).
   - Multi-channel social media viral growth post generator for LinkedIn, X (Twitter), and Reddit (`backend/services/social_swarm.py`).
3. **Ray Dalio & Paul Graham Elite SaaS Standard**:
   - Real-time lead conversion analytics dashboard in `web/templates/dashboard_analytics.html` & `web/routers/analytics.py`.
   - High-converting onboarding flow with Gulf RTL/LTR dual support (Cairo/Tajawal typography, dynamic CSS logical properties).

## Code Layout
- `backend/main.py`: Main FastAPI server entry point.
- `web/app_v2.py`: Web interface FastAPI application.
- `core/database.py` & `core/pg_sqlite_shim.py`: Database access layer with PostgreSQL/SQLite auto-detection.
- `backend/routers/`: REST API routers (leads, outreach, social_swarm, analytics).
- `web/routers/`: Jinja2 web routers.
- `web/templates/`: Jinja2 templates with Gulf RTL/LTR support.
- `backend/services/`: Core autonomous growth engine and scraping logic.
- `.github/workflows/`: GitHub Actions 24/7 keep-alive and autonomous cloud cron ticks.
- `tests/`: Pytest verification test suite.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | 24/7 Cloud Architecture & Database Resilience | PostgreSQL/Neon auto-detection with SQLite fallback, sub-5s keep-alive cron ticks | None | IN_PROGRESS |
| M2 | B2B Lead Gen & Cold Email Sequence Generator | Lead scraping/enrichment engine, multi-step personalized cold email sequence generator & dispatch tracking | M1 | PLANNED |
| M3 | Multi-Channel Social Growth Swarm | Autonomous social media post generator & automated campaign runner for LinkedIn, X, Reddit | M1 | PLANNED |
| M4 | Elite SaaS Analytics & RTL/LTR Onboarding | Real-time lead conversion dashboard, high-converting onboarding flow with Gulf typography & CSS logical properties | M2, M3 | PLANNED |
| M5 | Final System Verification & Forensic Integrity Audit | Pass 100% of test suite, Challenger verification, Forensic Auditor verification | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### Database Shim Contract (`core/pg_sqlite_shim.py` & `core/database.py`)
- Detects `DATABASE_URL` / `POSTGRES_URL` in environment. If present, connects to PostgreSQL; otherwise falls back to SQLite.
- Auto-translates SQL placeholders `$1, $2` to `?` for SQLite compatibility.

### Lead Scraping & Enrichment (`GET/POST /api/v1/leads/`)
- Returns enriched lead objects (name, company, title, email, LinkedIn URL, status).

### Cold Email Generator (`POST /api/v1/outreach/sequence`)
- Takes lead info & target company details; returns multi-step email templates with personalized touchpoints.

### Social Swarm Generator (`POST /api/v1/social/campaign`)
- Generates tailored posts for LinkedIn, X (Twitter), and Reddit per cloud tick.

### Analytics Endpoint (`GET /api/v1/analytics/conversion`)
- Returns real-time lead conversion metrics, channel breakdown, and pipeline status.
