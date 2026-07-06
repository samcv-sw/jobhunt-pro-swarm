# BRIEFING — 2026-07-06T13:34:00+03:00

## Mission
Perform a page-by-page audit of target templates and any existing audit reports.

## 🔒 My Identity
- Archetype: explorer
- Roles: Teamwork explorer
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_3
- Original parent: 7a4bf194-0a9b-4a62-9eb6-35e05c0ec597
- Milestone: Milestone 1

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Inspect local templates, views, configs and audit files (e.g. live_site.html, qa_report_round4.json)
- Avoid making any changes to the code

## Current Parent
- Conversation ID: 7a4bf194-0a9b-4a62-9eb6-35e05c0ec597
- Updated: 2026-07-06T13:15:31+03:00

## Investigation State
- **Explored paths**: web/app_v2.py, web/app.py, web/routers/auth.py, web/routers/public.py, web/routers/dashboard.py, web/templates/en/*.html, qa_report_round4.json, necrotic_audit.json, live_site.html
- **Key findings**: Missing GET/POST `/login` routes in app_v2.py, missing `/new-campaign` route, lack of `/en/` route prefix handling, Javascript HTML entity textContent bugs, placeholder social links.
- **Unexplored areas**: None.

## Key Decisions Made
- Audited the routes programmatically via Python introspection scripts to bypass local packaging and import differences.
- Converted UTF-16LE `live_site.html` to UTF-8 to audit its tags and verify elements programmatically.

## Artifact Index
- ORIGINAL_REQUEST.md — Original request details
- progress.md — Task progress tracking
- BRIEFING.md — Persistent briefing state
- list_routes.py — Python script to dump active FastAPI routes
- find_route_definitions.py — Python script to trace target route files and lines
- find_all_target_routes.py — Python script to recursively trace route functions
- audit_live_site.py — Python script to parse and audit live_site.html
