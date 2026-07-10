# Project: JobHunt Pro Optimization and Cloud Deployment

## Architecture
- Backend: FastAPI with SQLite database, with option to dynamically connect to Turso libSQL when `TURSO_DATABASE_URL` is set.
- Frontend: Vue app (served on Cloudflare Pages) and Jinja2 templates served by FastAPI.
- Workers/Scrapers: Python scripts (running on Hugging Face Spaces or Celery).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | RTL & Localization | Audit and optimize Jinja2 templates, Vue components, and CSS files for RTL logical properties, Cairo/Tajawal fonts, line-height 1.7-2.0, no letter-spacing on Arabic, dir="auto" on forms, and directional icon scaling. | None | IN_PROGRESS (Conv: 11f8a568-1521-4095-aef6-8b042319402d) |
| 2 | SQLite to Turso | Configure backend SQLite to dynamically connect to Turso when TURSO_DATABASE_URL is set, add connection pooling, and caching wrappers. | None | PLANNED |
| 3 | Free Cloud Deploy | Create Dockerfiles/configurations for Koyeb (FastAPI backend), Hugging Face Spaces (scrapers/workers), and Cloudflare Pages setup (Vue frontend). | None | PLANNED |
| 4 | E2E & Verification | Run the full unit and E2E test suite (366+ tests) and run verify_integrity.py to ensure zero regressions and perfect execution. | M1, M2, M3 | PLANNED |

## Interface Contracts
### Database Interface
- `core/async_db.py` / `core/database.py` ↔ libSQL / SQLite
- Dynamic fallback: if `TURSO_DATABASE_URL` is set, connect to Turso using libSQL driver (or compatible client), else fallback to standard sqlite3/aiosqlite.
- Caching wrappers and connection pool must be transparent to query callers.

## Code Layout
- `web/templates/` and `web/templates/en/` — Jinja2 templates
- `frontend-vue/` — Vue frontend code
- `core/async_db.py` — Database connection logic
- `config.py` — Global configuration settings
- `koyeb.yaml` / `Dockerfile.koyeb` — Koyeb deployment
- `Dockerfile.huggingface` / `README.md` (metadata) — Hugging Face Space config
- `cloudflare.json` or equivalent Cloudflare Pages configuration
