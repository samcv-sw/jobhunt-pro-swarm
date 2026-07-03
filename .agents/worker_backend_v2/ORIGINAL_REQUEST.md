## 2026-07-03T10:34:21Z
You are the Backend Implementation Worker.
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_backend_v2
Your identity is worker_backend_v2.

Your objective is to implement the backend improvements (R1 and R4) according to the strategy:
1. Create `backend/auth.py` to handle JWT-based authentication.
   - Implement `verify_jwt` dependency using `PyJWT` to validate Bearer tokens. If validation fails (invalid, missing, expired), raise `HTTPException(401, detail="...")`.
   - Implement `create_access_token` helper to generate access tokens for testing.
   - Use standard/default secret key (`JWT_SECRET_KEY` from env or a safe fallback like "super-secret-key-jobhunt-pro") and algorithm ("HS256").
2. Update `backend/main.py`:
   - Enforce JWT authentication on all `/api/v1/*` routes (e.g. `/api/v1/scrape`, `/api/v1/generate-cover-letter`, `/api/v1/accounts`) using the `verify_jwt` dependency.
   - Ensure non-API endpoints `/` and `/health` are NOT protected by JWT.
   - Update `CoverLetterRequest` Pydantic model to include an optional field `tone: str = "professional"`.
   - Update the `POST /api/v1/generate-cover-letter` endpoint to return a `StreamingResponse` (with media type `"text/event-stream"`). It should stream the cover letter chunks in real-time as SSE format (`data: {"chunk": token}\n\n`).
3. Refactor `backend/ai_engine.py`:
   - Implement `generate_smart_cover_letter_stream(job_description: str, user_cv: str, tone: str)` as an async generator yielding text chunks wrapped in SSE format (JSON-encoded delta).
   - Use `stream=True` in the Groq chat completions call.
   - Incorporate dynamic tone guidelines using a registry:
     * `"professional"`: polished, formal...
     * `"confident"`: high energy, assertive...
     * `"creative"`: engaging, storytelling...
   - Keep the original `generate_smart_cover_letter` function intact if needed by Celery tasks or other modules.
4. Modify existing test files (`tests/test_backend.py`, `tests/e2e/test_backend.py`, etc.) or their test setups to inject valid Authorization headers for all API requests to prevent them from failing.
5. Create a new test suite `tests/test_backend_secured.py` that comprehensively tests:
   - All `/api/v1/*` routes return 401 if token is missing or invalid.
   - Successful routes with a valid JWT token.
   - `/api/v1/generate-cover-letter` streams response chunks (Server-Sent Events) successfully.
   - Support for professional, confident, and creative tones.
6. Verify your implementation by running the backend tests (e.g. `pytest tests/test_backend_secured.py` and `pytest tests/test_backend.py`). Ensure they compile and pass.

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write a detailed handoff.md report summarizing the changes made, the files created/modified, and the test command/results. Let me know when you are done.
