# BRIEFING — 2026-07-12T13:28:00Z

## Mission
Investigate the codebase for browser-based scraping scripts and recommend optimization strategies to block heavy resources (images, fonts, stylesheets, trackers) to minimize RAM and network usage.

## 🔒 My Identity
- Archetype: Teamwork explorer
- Roles: Teamwork explorer, researcher, read-only investigator
- Working directory: C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m4_hf_3
- Original parent: da63cc14-7285-4a19-97cb-7b1eb7a13c9c
- Milestone: Milestone 4: Browser Scraper Performance Optimization

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- CODE_ONLY network mode (no external websites/services)
- Write reports and handoffs only in explorer_m4_hf_3 folder

## Current Parent
- Conversation ID: da63cc14-7285-4a19-97cb-7b1eb7a13c9c
- Updated: 2026-07-12T13:28:00Z

## Investigation State
- **Explored paths**:
  - `scrapers/stealth_ingest.py`
  - `core/stealth.py`
  - `core/zero_cost_stealth_browser.py`
  - `core/ghost_applicant.py`
- **Key findings**:
  - `scrapers/stealth_ingest.py` is the orchestrator script using `curl_cffi` requests and progressive browser fallbacks.
  - Browser-based fallbacks are defined in `core/stealth.py`: `NodriverFallback` (uses Chrome DevTools Protocol client `nodriver`) and `ApexCamoufoxFallback` (uses native antidetect Firefox `camoufox`).
  - There is a secondary `ZeroCostStealthScraper` in `core/zero_cost_stealth_browser.py` using `undetected-chromedriver`.
  - There is a Playwright auto-applicant integration in `core/ghost_applicant.py` (`GhostApplicant`).
  - For `nodriver`, resource blocking is configured via CDP `Network.enable` and `Network.setBlockedURLs` (mapped as `set_blocked_ur_ls`).
  - For `camoufox`/`playwright` and `ghost_applicant` Playwright integration, resource blocking is configured via Playwright `page.route` to abort heavy resources and tracker requests.
  - For `undetected_chromedriver`, resource blocking is configured via Selenium Chrome options preferences and `execute_cdp_cmd` calls.
- **Unexplored areas**: None.

## Key Decisions Made
- Initialized investigation into browser-based scrapers.
- Produced patch file `resource_blocking.patch` containing precise diff implementations for the changes across `core/stealth.py`, `core/zero_cost_stealth_browser.py`, and `core/ghost_applicant.py`.

## Artifact Index
- `resource_blocking.patch` - Patch file outlining implementation changes.
