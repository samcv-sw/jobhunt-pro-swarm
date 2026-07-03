# BRIEFING — 2026-07-03T18:51:27Z

## Mission
Modify scrapers/stealth_ingest.py to upgrade anti-bot bypass protections and return structured, parsed data.

## 🔒 My Identity
- Archetype: teamwork_preview_worker_scraper_hardening
- Roles: implementer, qa, specialist
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_worker_scraper_hardening
- Original parent: 91d10ef2-c6c3-4f61-bb63-9c8e72579eeb
- Milestone: Scraper Hardening and E2E Tests Pass

## 🔒 Key Constraints
- Avoid placeholder code.
- CSS Logical Properties (Arabic & RTL Focus) if UI changes (not applicable here, but keep in mind).
- Only modify what is necessary (minimal change principle).
- Write handoff.md with 5-component format when done.
- Communicate with parent agent via send_message using specified format.

## Current Parent
- Conversation ID: 91d10ef2-c6c3-4f61-bb63-9c8e72579eeb
- Updated: not yet

## Task Summary
- **What to build**: Modifying `scrapers/stealth_ingest.py` to:
  1. Fix `STEALTH_PROFILES` with valid targets.
  2. Implement parser helper `_parse_page_content` to parse multi-card or fallback to single job.
  3. Update `process_single_job` to return list of dicts and use progressive fallbacks with `NodriverFallback` and `ApexCamoufoxFallback` on CAPTCHA/CF detection.
  4. Update `stealth_scrape_jobs` to flat-map result lists.
  5. Run tests and verify sannysoft bypass check.
- **Success criteria**: All E2E tests (`test_r3_scraper.py`) and bypass checks pass successfully.
- **Interface contracts**: `scrapers/stealth_ingest.py`
- **Code layout**: Source in `scrapers/`, tests in `tests/`

## Key Decisions Made
- [TBD]

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_worker_scraper_hardening\ORIGINAL_REQUEST.md — Original instructions
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_worker_scraper_hardening\BRIEFING.md — Current status and constraints
