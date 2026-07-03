# BRIEFING — 2026-07-03T13:34:16+03:00

## Mission
Implement scraper stealth hardening improvements (R3) by incorporating features from proposed_stealth_ingest.py, verifying bot checks, and validating Celery background tasks.

## 🔒 My Identity
- Archetype: Style Refactoring Worker
- Roles: implementer, qa, specialist
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_m2
- Original parent: cc02e1de-bfe2-45dc-88a9-c4e8e06e87e7
- Milestone: Milestone 2
- Archetype (Current): Stealth Scraper Hardening Worker
- Milestone (Current): Milestone 2 (Scraper Stealth Hardening - R3)
- Original Parent (Current): 91a89750-dc39-4cf9-99b5-ef045797079c

## 🔒 Key Constraints
- Avoid placeholder code.
- Use CSS logical properties instead of physical ones (margin-inline-start/end, padding-inline-start/end, inset-inline-start/end, inline-size/block-size, border-inline-start/end, text-align: start/end).
- Define `--text-x-direction` variable for RTL scaling.
- Apply glassmorphism tokens and Arabic typography standards.
- Run `python web/build_rtl_css.py` to compile RTL stylesheets.
- No network access (CODE_ONLY mode).
- [New] Browser profile alignment (TLS fingerprint + HTTP headers).
- [New] Session-pinned proxy rotation (dynamic and static).
- [New] Organic warmup steps (fetching root domain or /robots.txt).
- [New] Concurrency control using asyncio.Semaphore (limit to 3) and random delay (jitter) between hits.
- [New] DO NOT CHEAT: Genuine implementations only, no hardcoded verification results.

## Current Parent
- Conversation ID: 509f40ec-93f3-4ae2-9567-2cde222792e2
- Recipient ID: 91a89750-dc39-4cf9-99b5-ef045797079c (main agent)
- Updated: 2026-07-03T13:34:16+03:00

## Task Summary
- **What to build**: Enhance `scrapers/stealth_ingest.py` with TLS fingerprinting, proxy rotation, warm-ups, semaphore concurrency control, and jitter.
- **Success criteria**: Code successfully merged and verified using bot/sannysoft test code, and Celery scraper task verification.
- **Interface contracts**: Scrapers/StealthIngest API interfaces with existing Celery backend tasks in `backend/tasks.py`.
- **Code layout**: Source in `scrapers/`, Celery in `backend/`.

## Key Decisions Made
- [TBD]

## Artifact Index
- `.agents/worker_m2/ORIGINAL_REQUEST.md` — Original request copy
- `.agents/worker_m2/BRIEFING.md` — Persistent briefing context
- `.agents/worker_m2/progress.md` — Progress tracking

## Change Tracker
- **Files modified**: None yet
- **Build status**: Untested
- **Pending issues**: None

## Quality Status
- **Build/test result**: Untested
- **Lint status**: Untested
- **Tests added/modified**: None

## Loaded Skills
- None
