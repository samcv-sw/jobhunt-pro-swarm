# BRIEFING — 2026-07-12T13:24:00+03:00

## Mission
Implement Cloudflare deployment, GitHub actions keep-alive, Celery memory guard, Neon PgBouncer connection updates, and Free Proxy pool scraper rotation in JobHunt Pro.

## 🔒 My Identity
- Archetype: implementer, qa, specialist
- Roles: implementer, qa, specialist
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_cloud_stealth_reliability
- Original parent: d42acd51-edc2-4ee9-91ee-6661881fc368
- Milestone: Cloud & Stealth Reliability

## 🔒 Key Constraints
- Maximize Autonomy: proceed with implementation without asking user for confirmation.
- Do Not Ask Questions: avoid asking clarifying or design questions.
- Automatic Execution: propose commands and edits directly.
- CSS Logical Properties (if UI edits are made) & Arabic typography constraints.
- No cheating: implementations must be genuine.

## Current Parent
- Conversation ID: d42acd51-edc2-4ee9-91ee-6661881fc368
- Updated: not yet

## Task Summary
- **What to build**: Next.js deployment setup on Cloudflare Pages (worker backend URL, redirects proxy, backend CORS allowed origins), GitHub Actions schedule keep-alive workflow pinger and Neon warmer, Celery worker memory limits, database PgBouncer pooler adapter, and ProxyManager class with scraper, cache, validator, and rotation.
- **Success criteria**:
  - `frontend/public/_worker.js` updated
  - `frontend/public/_redirects` created
  - `backend/main.py` CORS origins updated
  - `.github/workflows/keepalive.yml` created
  - `start_cloud.py` celery memory parameters added
  - `backend/database.py` and `backend/sync_worker.py` pgBouncer handling updated
  - `core/ghost_hunter.py` ProxyManager implemented and integrated
- **Interface contracts**: TBD
- **Code layout**: TBD

## Change Tracker
- **Files modified**:
  - `frontend/public/_worker.js`: updated backend url configuration
  - `frontend/public/_redirects`: created proxy redirection
  - `backend/main.py`: added pages.dev wildcards to origins
  - `.github/workflows/keepalive.yml`: created scheduled workflow
  - `start_cloud.py`: added celery memory recycling parameters
  - `backend/database.py`: added PgBouncer URL formatter and parser
  - `backend/sync_worker.py`: integrated PgBouncer formatter and options
  - `core/ghost_hunter.py`: implemented ProxyManager and duplicate checks
- **Build status**: Pass
- **Pending issues**: None

## Quality Status
- **Build/test result**: Pass
- **Lint status**: 0 violations
- **Tests added/modified**: `tests/test_stealth_reliability.py` added covering connection formatter and ProxyManager

## Loaded Skills
- None

## Key Decisions Made
- Performed duplicate URL validation checks *before* spawning the browser process in GhostHunter to save system memory.
- Added a full PgBouncer URL rewrite formatter utility in `backend/database.py` and reused it in `backend/sync_worker.py` to ensure consistency.

## Artifact Index
- None
