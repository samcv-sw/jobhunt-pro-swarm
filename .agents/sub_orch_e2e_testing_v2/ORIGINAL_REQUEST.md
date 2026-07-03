# Original User Request

## 2026-07-03T13:30:18Z

You are the E2E Testing Track Orchestrator for the JobHunt Pro SaaS platform improvements campaign.
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_e2e_testing_v2
Your objective is to design, implement, and verify a comprehensive, opaque-box E2E test suite (Tiers 1-4) reflecting the follow-up requirements from the 2026-07-03T10:28:14Z update.

The specific feature requirements to test are:
1. AI Engine Cover Letter generation streaming using Groq LPU and tone matching context (R1).
2. Frontend Next.js dashboard `/dashboard` rendering live statistics, historical scrapes, and user analytics with modern glassmorphism design (R2).
3. Scraper Stealth Hardening in `scrapers/stealth_ingest.py` (Cloudflare/DataDome bypasses, rotating proxies, TLS fingerprinting) (R3).
4. FastAPI JWT-based auth on `/api/v1/*` endpoints (Authorization Bearer token) (R4).
5. CI/CD pipeline verification: GitHub Actions workflow in `.github/workflows/production.yml` runs the tests on push.

Verify all rules from AGENTS.md are followed (CSS Logical Properties, Arabic typography - Cairo/Tajawal fonts >= 16px, line-height 1.8, RTL/LTR dynamic switches, dir="auto" on forms).

Follow the Project Sub-orchestrator workflow pattern:
1. Create SCOPE.md in your working directory.
2. Decompose and plan the E2E test suite milestones.
3. Spawn workers/reviewers/challengers/auditors to implement the tests.
4. Verify that the test suite runs successfully with `python -m pytest tests/e2e/`.
5. Publish TEST_READY.md in the project root with the test runner command, execution summary, and a feature coverage checklist once tests are verified and passing.
6. Write handoff.md and notify your parent (dae71ec6-fc34-4d15-b3ed-62633bd5ec7b) using send_message.

DO NOT CHEAT. All implementations and tests must be genuine.
