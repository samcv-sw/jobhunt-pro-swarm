# BRIEFING — 2026-07-05T20:01:01+03:00

## Mission
Fix remaining styling physical gradient values and Arabic readability issues (font-sizes and line-heights) in the legacy templates stylesheet files (under web/static/css/).

## 🔒 My Identity
- Archetype: implementer, qa, specialist
- Roles: implementer, qa, specialist
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_milestone4_style\
- Original parent: 668507ba-574e-4afb-ade7-e2da04b80ceb
- Milestone: Milestone 4 (Styling Hardening)

## 🔒 Key Constraints
- CODE_ONLY network mode: no external HTTP/curl/wget/etc.
- Use only local workspace folders.
- Follow Rule 1 / Rule 2 prompt protections.
- Swapping 'to right' with 'to left' (and vice versa) inside linear-gradient values.
- Post-process regex translation step to scale up font sizes below 14px to 14px (or 0.85rem to 0.875rem, etc.).
- Post-process regex translation step to scale up unitless line-height values below 1.6 to 1.6.
- Run verify_styles.py and ensure violations reduce to 0.
- Run frontend E2E tests and ensure they pass.

## Current Parent
- Conversation ID: 668507ba-574e-4afb-ade7-e2da04b80ceb
- Updated: not yet

## Task Summary
- **What to build**: Refactoring of web/build_rtl_css.py and regeneration of all RTL css files to fix gradients and typography readability.
- **Success criteria**: All styling violations in target files reduced to 0 in verify_styles.py; pytest tests/e2e/test_frontend.py passes.
- **Interface contracts**: legacy templates stylesheet files under web/static/css/
- **Code layout**: web/static/css/

## Key Decisions Made
- [TBD]

## Change Tracker
- **Files modified**: None yet
- **Build status**: Unknown
- **Pending issues**: None

## Quality Status
- **Build/test result**: Unknown
- **Lint status**: Unknown
- **Tests added/modified**: None

## Loaded Skills
None

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_milestone4_style\BRIEFING.md — Briefing file
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_milestone4_style\progress.md — Progress tracker
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_milestone4_style\handoff.md — Handoff report
