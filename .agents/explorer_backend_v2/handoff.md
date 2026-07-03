# Handoff Report — Backend Explorer & Architect

## 1. Observation
- **Groq Client Initialization**: In `backend/ai_engine.py` (lines 10-12):
  ```python
  client = AsyncGroq(
      api_key=os.environ.get("GROQ_API_KEY", "fallback-key-for-testing"),
  )
  ```
- **Synchronous AI Inference**: In `backend/ai_engine.py` (lines 41-56), the code uses a non-streaming chat completion request:
  ```python
  chat_completion = await client.chat.completions.create(
      messages=[...],
      model="llama3-70b-8192",
      temperature=0.5,
      max_tokens=1024,
      response_format={"type": "json_object"}
  )
  ```
- **Endpoints under `/api/v1/*`**: In `backend/main.py`, the following endpoints are registered directly on the `app` instance:
  - `@app.post("/api/v1/scrape")` (lines 45-51)
  - `@app.post("/api/v1/generate-cover-letter")` (lines 53-59)
  - `@app.post("/api/v1/accounts")` (lines 61-90)
- **Dependency Environment**: Running `pip list` confirmed the presence of:
  - `groq` (0.37.1)
  - `PyJWT` (2.12.1)
  - `cryptography` (48.0.0)
  - `passlib` is NOT installed.
- **Existing Test Suite**: Located at `tests/test_backend.py` and `tests/e2e/test_backend.py`. Running `pytest tests/test_backend.py` resulted in the process hanging on the second test because the Celery task `.delay()` call is not mocked and attempts to connect to Redis.

---

## 2. Logic Chain
1. Since `AsyncGroq` is already initialized as an asynchronous client, we can support non-blocking streaming by modifying `client.chat.completions.create` to include `stream=True`.
2. Because the output needs to be streamed in real-time, `StreamingResponse` from `fastapi.responses` should wrap an async generator function that yields token chunks formatted as Server-Sent Events (SSE).
3. Passing a `tone` parameter (e.g. professional, confident, creative) through the `CoverLetterRequest` schema allows us to dynamically retrieve tone-specific guidelines from a pre-defined map and inject them directly into the system prompt.
4. Using `PyJWT` (which is already installed in the environment), we can build `backend/auth.py` to handle JWT decoding and validation.
5. To secure all `/api/v1/*` endpoints cleanly, we can group them inside a FastAPI `APIRouter(prefix="/api/v1", dependencies=[Depends(verify_jwt)])` and register the router on the main app in `backend/main.py`. This avoids polluting non-API routes or duplicating dependency declarations across individual endpoints.

---

## 3. Caveats
- Direct JSON mode (`response_format={"type": "json_object"}`) on Groq might generate fragments of JSON syntax that are hard to parse on the fly in the frontend. It is assumed the frontend can parse structured lines like `Subject: <Subject>` and `Body: <Body>` or accept standard SSE event payloads (`data: {"chunk": token}`).
- We assume the authentication provider handles signing keys matching `JWT_SECRET_KEY` and the symmetric `HS256` algorithm; if asymmetric keys (e.g., RS256) are used, `PyJWT` supports them but requires configuring the public keys.
- Celery's `generate_cover_letter` task is currently synchronous (`asyncio.run(...)`). If cover letters are generated synchronously inside Celery, streaming is not utilized in the background worker queue. Therefore, the `/api/v1/generate-cover-letter` endpoint must be refactored to handle the streaming generation directly rather than offloading to Celery.

---

## 4. Conclusion
- The backend should be refactored to support non-blocking SSE streaming cover letters with tone matching by replacing the Celery task invocation in `POST /api/v1/generate-cover-letter` with a `StreamingResponse` wrapping `generate_smart_cover_letter_stream`.
- Authentication must be centralized using `PyJWT` in `backend/auth.py` and applied to all `/api/v1/*` routes by refactoring them under a unified `APIRouter`.

---

## 5. Verification Method
1. **Mock Testing**: Create `tests/test_backend_secured.py` (refer to `analysis.md` section 5.2 for design) to test the secured routes and streaming response.
2. **Execution Command**: Run the test suite using:
   ```bash
   pytest tests/test_backend_secured.py
   ```
3. **Manual Verification**: Run uvicorn server locally:
   ```bash
   uvicorn backend.main:app --reload
   ```
   Submit a POST request to `/api/v1/generate-cover-letter` with a valid JWT token in the `Authorization` header and assert that the response starts immediately with `content-type: text/event-stream`.
