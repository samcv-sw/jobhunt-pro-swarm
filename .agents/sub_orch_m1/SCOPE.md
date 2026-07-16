# Scope: E2E Testing Track Setup (Milestone 1)

## Architecture
- Existing test structure: tests/ directory contains 608 pytest cases.
- We need to categorize them, verify execution, ensure they pass, and document the architecture/runner.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Scan and Map Tests | Run Explorer to scan tests, map 608 pytest cases to Tiers 1-4, document runner and commands | None | DONE |
| 2 | Execute and Fix Suite | Run Worker to run the test suite, resolve any failing/flaky tests, verify all 608 cases pass | M1 | DONE |
| 3 | Document Test Infra | Generate TEST_INFRA.md and TEST_READY.md at project root | M1, M2 | DONE |
| 4 | Final Handoff | Generate handoff.md and send final notification to parent | M1, M2, M3 | DONE |

## Interface Contracts
- None.
