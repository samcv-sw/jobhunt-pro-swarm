# Scope: Milestone 5: Testing, Audits & Verification

## Architecture
- Implementation of comprehensive E2E tests, bot tests, load testing, mutation testing, API contract tests, and running the full verification suite.

## Work Items
1. **IMP-095**: Email dispatch E2E tests (aiosmtpd mock SMTP to test send_application_email Celery task).
2. **IMP-097**: Telegram bot command tests (Unit test each bot command handler in isolation).
3. **IMP-099**: Locust load tests (100 concurrent users on /api/v1/jobs/scrape).
4. **IMP-100**: Mutation testing with mutmut (mutmut run on core/scam_detector.py to find weak assertions).
5. **IMP-102**: API contract tests via Schemathesis (schemathesis run against OpenAPI spec in CI).

## Interface Contracts
- Tests must pass cleanly with zero failures.
- No regressions.
