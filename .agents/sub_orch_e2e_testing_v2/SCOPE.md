# Scope: E2E Test Suite (Tiers 1-4) Design & Implementation

## Architecture
- **Test Runner**: Pytest framework, invoked using `python -m pytest tests/e2e/`.
- **Target Applications**:
  - FastAPI backend under `backend/main.py` (serving `/api/v1/*` endpoints, AI engine, and Auth).
  - Next.js frontend under `frontend/` (dashboard page, styling rules, Cairo/Tajawal typography, logical properties).
  - Python-based stealth scraper in `scrapers/stealth_ingest.py`.
  - CI/CD workflow in `.github/workflows/production.yml`.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Test Design & Framework Setup | Analyze codebase, design E2E test scripts, configure mock objects/services for Groq streaming and bot-bypasses. | None | IN_PROGRESS |
| 2 | Implementation: Feature & Boundary Tests (Tiers 1-2) | Implement 25 Tier 1 (Feature Coverage) and 25 Tier 2 (Boundary & Corner) test cases. | M1 | PLANNED |
| 3 | Implementation: Integration & Scenario Tests (Tiers 3-4) | Implement 5 Tier 3 (Cross-feature) and 5 Tier 4 (Real-world scenario) test cases. | M2 | PLANNED |
| 4 | Verification & Auditing | Run test suite with pytest, verify 100% pass rate, run reviews and audits to ensure compliance with AGENTS.md rules and no-cheating policy. | M3 | PLANNED |
| 5 | Release | Publish `TEST_READY.md` in the project root and deliver handoff report to parent. | M4 | PLANNED |

## Interface Contracts
- **Test suite path**: `tests/e2e/`
- **Feature list**:
  - R1: AI Cover Letter streaming using Groq & tone matching
  - R2: Next.js dashboard glassmorphism & Arabic dynamic layout rules
  - R3: Stealth scraper bypasses (Cloudflare, proxy rotation, TLS spoofing)
  - R4: JWT Bearer auth on all `/api/v1/*` endpoints
  - R5: GitHub Actions production workflow configuration
