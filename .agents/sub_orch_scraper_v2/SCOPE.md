# Scope: Scraper Stealth Hardening

## Architecture
- `scrapers/stealth_ingest.py` is the main entry point for jobs scraping.
- Uses `curl_cffi` for requests to spoof TLS fingerprints (TLS/JA3 profiles like Chrome, Safari).
- Incorporates residential proxy rotation from the `RESIDENTIAL_PROXIES` environment variable.
- Used by `backend/tasks.py` to ingest jobs asynchronously.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration & Architecture | Investigate `scrapers/stealth_ingest.py` and research best approaches for TLS spoofing, rotating proxies, and bypass mechanisms. | none | DONE |
| 2 | Implementation | Implement advanced bypasses, proxy rotation, and TLS spoofing in `scrapers/stealth_ingest.py`. Implement verification checks for `https://bot.sannysoft.com/`. | M1 | IN_PROGRESS |
| 3 | Review & Challenger Validation | Run static analysis, review code quality, run verification tests, and run stress tests against `bot.sannysoft.com`. | M2 | PLANNED |
| 4 | Forensic Audit | Verify integrity of the solution (no hardcoding, dummy implementations, or cheating). | M3 | PLANNED |

## Interface Contracts
### `scrapers.stealth_ingest` Interface
- `process_single_job(url: str) -> dict | None`
  - Input: `url` (str) - The URL of the job page or target to fetch.
  - Output: `dict` with keys `{"title": str, "url": str, "company": str | None, "description_snippet": str}` or `None` on failure.
- `stealth_scrape_jobs(urls: List[str]) -> List[dict]`
  - Input: `urls` (List[str]) - List of URLs.
  - Output: `List[dict]` of parsed job data.
- Added custom test endpoint support to ensure `https://bot.sannysoft.com/` can be fetched, parsed, and checked for blocks or detection tests.

## Code Layout
- `scrapers/stealth_ingest.py` - Core scraper implementation.
- `tests/` or `scratch/` - Scripts for testing scraper bypass logic and proxy integrity.
