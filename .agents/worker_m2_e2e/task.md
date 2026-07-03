# Fix FastAPI & Next.js Stack E2E Issues (Milestone 2)

## Task Description
Implement the following fixes to resolve the 9 failing E2E tests in `tests/e2e/`:

1. **`backend/main.py`**:
   - Make `/api/v1/generate-cover-letter` trigger the background Celery task `generate_cover_letter.delay(req.job_description, req.user_cv)`:
     ```python
     @app.post("/api/v1/generate-cover-letter", dependencies=[Depends(verify_jwt)])
     async def trigger_cover_letter(req: CoverLetterRequest, request: Request = None):
         task = await asyncio.to_thread(generate_cover_letter.delay, req.job_description, req.user_cv)
         return {"status": "queued", "task_id": task.id}
     ```
   - Add `/api/v1/ai/generate-cover-letter/stream` as a streaming SSE endpoint:
     ```python
     @app.post("/api/v1/ai/generate-cover-letter/stream", dependencies=[Depends(verify_jwt)])
     async def stream_cover_letter(req: CoverLetterRequest, request: Request = None):
         return StreamingResponse(
             generate_smart_cover_letter_stream(req.job_description, req.user_cv, req.tone),
             media_type="text/event-stream"
         )
     ```

2. **`frontend/src/app/layout.tsx`**:
   - Change `dir="rtl"` (line 39) to `dir="auto"`.

3. **`scrapers/stealth_ingest.py`**:
   - Update `get_stabilized_proxy` to make `session_id` parameter optional:
     `def get_stabilized_proxy(session_id: str = "default") -> dict:`
   - Refactor `_parse_job_page` to loop through title selectors and select the first one yielding non-empty text:
     ```python
     title = "Unknown Position"
     for selector_fn in [
         lambda s: s.find("h1"),
         lambda s: s.find(attrs={"class": lambda c: c and "job-title" in c}),
         lambda s: s.find(attrs={"class": lambda c: c and "title" in c}),
         lambda s: s.find("title")
     ]:
         el = selector_fn(soup)
         if el:
             text = el.get_text(strip=True)
             if text:
                 title = text
                 break
     ```

4. **`tests/e2e/test_r3_scraper.py`**:
   - Update `test_r3_t1_trigger_scrape_queued` to use `headers=auth_header` (and pass `auth_header` fixture to the test signature).
   - In `test_r3_t1_stealth_profiles_configured`, extract `id` fields from `STEALTH_PROFILES` and assert for `"chrome131"` and `"safari18_0"`:
     ```python
     profile_ids = [p["id"] for p in STEALTH_PROFILES]
     assert "chrome131" in profile_ids
     assert "safari18_0" in profile_ids
     ```
   - In `test_r3_t3_integration_scraper_to_database`, update `mock_process` to accept `session_id`:
     `async def mock_process(url, session_id=None):`

5. **`.github/workflows/production.yml`**:
   - Quote `on:` as `"on":` on line 3 to prevent PyYAML parsing key error.

6. **Verify E2E Tests**:
   - Run `python -m pytest tests/e2e/` with `PYTHONPATH=.`. All E2E tests should pass.

## Scope Boundaries
- Do not modify any other backend files or test files.
- Focus strictly on these changes.

## Expected Output
- Detailed handoff report in `handoff.md` with verification test logs.
