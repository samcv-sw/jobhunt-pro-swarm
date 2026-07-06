# Project: JobHunt Pro Live Audits and Fixes

## Architecture
- Existing web application.
- Target website: https://jhfguf.pythonanywhere.com/
- Main codebase in standard directories (templates/, static/, views/ etc.).
- Testing framework: pytest (253 tests).

## Milestones
| # | Name | Scope | Dependencies | Status | Conversation ID |
|---|------|-------|-------------|--------|-----------------|
| 1 | Live Page Audit | Crawl/Fetch all 18 live pages, identify broken links, buttons, content, etc. | none | IN_PROGRESS | 496e9711, b33ac7a9, aedd0d12 |
| 2 | Fix Non-Functional Buttons | Fix R2 (ابدأ مجاناً, pricing plan buttons, form submit, '#' placeholders) | M1 | PLANNED | |
| 3 | Fix Content Issues | Fix R3 (truncated text, empty FAQ answers, contact form submit, no placeholders) | M1 | PLANNED | |
| 4 | Fix Navigation Consistency | Fix R4 (nav/footer on every page, active link highlight, mobile menu, language switcher) | M2, M3 | PLANNED | |
| 5 | Verify & Test Suite | Run tests (Zero Regression) and Forensic Auditor checks | M4 | PLANNED | |

## Interface Contracts
- Changes must not break existing backend logic.
- Front-end rules must strictly follow AGENTS.md (Arabic layout, CSS logical properties, Cairo/Tajawal font style rules).
