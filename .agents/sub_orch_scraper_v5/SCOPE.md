# Scope: Scraper Stealth Hardening (R3)

## Architecture
- Scraper script located in `scrapers/stealth_ingest.py`

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | Anti-bot Bypass Upgrade | Upgrade anti-bot bypass mechanism in `stealth_ingest.py` | None | PLANNED |
| 2 | Structured Output parsing | Parse scraper outputs to return `list[dict]` (with `title`, `url`) | M1 | PLANNED |
| 3 | Verification & E2E scraper tests | Run scraper tests to ensure correctness | M2 | PLANNED |

## Interface Contracts
- `stealth_ingest.py` returns `list[dict]` where each dict has at least `title` and `url` keys.
