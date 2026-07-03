# BRIEFING — 2026-07-03T10:35:20Z

## Mission
Investigate options for stealth hardening of `scrapers/stealth_ingest.py` (TLS fingerprinting, proxies, evasion techniques) and design a verification method using `https://bot.sannysoft.com/`.

## 🔒 My Identity
- Archetype: explorer
- Roles: Read-only investigator, analyzer
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1_1
- Original parent: 91a89750-dc39-4cf9-99b5-ef045797079c
- Milestone: Stealth Ingest Hardening and Verification

## 🔒 Key Constraints
- Read-only investigation — do NOT implement changes in project source files
- Adhere to the Handoff Protocol
- Document observations, logic chain, caveats, conclusion, and verification method.

## Current Parent
- Conversation ID: 91a89750-dc39-4cf9-99b5-ef045797079c
- Updated: 2026-07-03T10:35:20Z

## Investigation State
- **Explored paths**:
  - `scrapers/stealth_ingest.py` (core entry point)
  - `core/stealth.py` (global stealth settings and proxy scraping)
  - `core/zero_cost_stealth_browser.py` (undetected-chromedriver implementation)
- **Key findings**:
  - `curl_cffi` (v0.15.0) is installed and successfully evades Cloudflare/sannysoft blocks out of the box when impersonating standard profiles (e.g. Chrome, Firefox, Safari).
  - Sannysoft uses client-side JavaScript execution to check for WebDriver and other bot markers. Because curl_cffi is a non-JS HTTP client, it does not execute these scripts. The static HTML retrieved contains hardcoded "failed" placeholder text, which is normal and expected for any raw HTTP scraper (does not mean curl_cffi is detected).
  - Undetected-chromedriver fails locally due to Chrome version mismatch (browser version 149 vs driver version 150), making raw HTTP client options (`curl_cffi` or `primp`) the most reliable first-line choices.
- **Unexplored areas**: None.

## Key Decisions Made
- Recommended using `curl_cffi` for fast raw HTTP stealth fetch, with organic warmup, custom matching HTTP/2 headers, and proxy fallback to `core/stealth.py`'s harvested pool if `RESIDENTIAL_PROXIES` is not configured.
- Structured proposed code changes in `.agents/explorer_m1_1/proposed_stealth_ingest.py`.

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1_1\ORIGINAL_REQUEST.md — Original request content
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1_1\proposed_stealth_ingest.py — Proposed code updates
