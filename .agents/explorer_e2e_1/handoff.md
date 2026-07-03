# Handoff Report — Explorer 1 E2E Investigation

This report outlines direct observations of the current backend structure, analysis of JWT authentication and Groq streaming requirements, execution of the existing E2E test suite, and E2E test design proposals for R1 and R4.

---

## 1. Observation

### Existing Codebase Structure & Dependencies:
- **Backend Endpoints**: In `backend/main.py`, the FastAPI app defines endpoints `/api/v1/scrape`, `/api/v1/generate-cover-letter`, `/api/v1/accounts`, and `/ws/war-room`. Currently:
  - None of the `/api/v1/*` endpoints reference a dependency or middleware for token validation.
  - There is no authentication module (e.g. `backend/auth.py`) implemented yet.
- **Groq AI Engine**: In `backend/ai_engine.py`, the function `generate_smart_cover_letter` uses `AsyncGroq` client (`from groq import AsyncGroq`) to create chat completions asynchronously without streaming (`chat_completion = await client.chat.completions.create(...)` in line 41).
- **Environment & Library Support**: 
  - Checked `requirements.txt` and `requirements-cloud.txt`.
  - Confirmed via python interpreter check that the PyJWT library (`jwt`) is already installed in the local environment at `C:\Users\samde\AppData\Local\Programs\Python\Python312\Lib\site-packages\jwt\__init__.py`.
  - The `python-jose` library is not installed (import fails with `ModuleNotFoundError`).

### Existing Test Suite Execution:
- Ran the test suite using pytest on the `tests/e2e/` folder.
- **Command Executed**: `python -m pytest tests/e2e/` in root directory.
- **Result**:
  - **17 passed** in 4.47s.
  - Tests run successfully: 6 tests in `test_backend.py`, 4 tests in `test_database.py`, 7 tests in `test_frontend.py`.
  - Current E2E backend tests run unauthenticated requests directly against `/api/v1/scrape`, `/api/v1/generate-cover-letter`, and `/api/v1/accounts`.

---

## 2. Logic Chain

1. **JWT Auth Implementation (R4)**:
   - When the backend implements JWT authorization, all `/api/v1/*` endpoints will require an `Authorization: Bearer <token>` header.
   - If this is enforced, any incoming request without a valid token will receive a `401 Unauthorized` status code.
   - *Direct Impact*: The existing E2E tests in `tests/e2e/test_backend.py` (e.g., `test_backend_scraping_is_non_blocking`, `test_backend_cover_letter_is_non_blocking`, `test_endpoint_validation_errors`, and `test_integration_outbox_flow`) and simple tests in `tests/test_backend.py` will fail immediately because they make anonymous requests to `/api/v1/*`.
   - *Recommendation*: The backend implementation must coordinate with test updates. Either the test helper needs to pre-authenticate and inject a valid bearer token into headers for all test client calls, or a test bypass/bypass-key is configured (though actual JWT verification in tests is preferred).

2. **AI Cover Letter Streaming & Tone Matching (R1)**:
   - The current `/api/v1/generate-cover-letter` endpoint is a POST request that queues a Celery background job and returns `{"status": "queued", "task_id": ...}`.
   - R1 calls for an EventStream response (Server-Sent Events) returning chunk-by-chunk under `/api/v1/ai/generate-cover-letter` (or similar).
   - This requires a `StreamingResponse` from FastAPI, fetching chunks from `AsyncGroq` using `stream=True` in the chat completions call.
   - In E2E tests, the `AsyncGroq` chat completion stream must be mocked to return an async generator that yields chunks sequentially, and the test client must verify headers (`Content-Type: text/event-stream`) and the parsed output chunks.

---

## 3. Caveats

- **External Integrations**: We do not run active external network requests to Groq during pytest execution. All tests must rely on mocking the `AsyncGroq` client response stream.
- **SQLite Database**: The database tests are configured against a local SQLite WAL configuration. When testing Neon PostgreSQL, ensure connection parameters are mocked or managed gracefully (as demonstrated in `test_sync_outbox_connection_error_graceful_handling`).
- **Parallel Execution**: Celery worker integration in tests is mocked (monkeypatching `scrape_jobs.delay` or `generate_cover_letter.delay`) to avoid spinning up external worker and Redis services during pytest.

---

## 4. Conclusion & Test Proposals

### R4 E2E Test Strategy (JWT Auth)
We recommend adding the following tests to verify JWT protection:
1. **Unauthorized requests** to `/api/v1/*` must return `401 Unauthorized`.
2. **Expired/Malformed/Incorrect signature tokens** must return `401 Unauthorized`.
3. **Valid tokens** (signed with the configured `JWT_SECRET`) must permit access and return `200 OK` (or appropriate response).

#### Proposed JWT Test Code Template:
```python
import jwt
import time
import pytest
import httpx
from unittest.mock import MagicMock
from backend.main import app

JWT_SECRET = "change-this-to-random-string"  # Must match configured backend secret for tests

def generate_test_token(username: str, expires_in: int = 3600) -> str:
    payload = {
        "sub": username,
        "exp": int(time.time()) + expires_in
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@pytest.mark.asyncio
async def test_jwt_auth_enforced_under_v1():
    """Verify that accessing endpoints under /api/v1/* without a token yields 401."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Test /api/v1/scrape without headers
        resp = await client.post("/api/v1/scrape", json={"user_id": "test_user", "target_urls": []})
        assert resp.status_code == 401
        
        # Test /api/v1/accounts without headers
        resp = await client.post("/api/v1/accounts", json={"tenant_id": "test_tenant", "balance_cents": 100})
        assert resp.status_code == 401

@pytest.mark.asyncio
async def test_jwt_auth_invalid_tokens():
    """Verify that malformed or expired tokens yield 401."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid / Malformed token
        headers = {"Authorization": "Bearer not-a-valid-token"}
        resp = await client.post("/api/v1/scrape", json={"user_id": "u", "target_urls": []}, headers=headers)
        assert resp.status_code == 401

        # Expired token
        expired_token = generate_test_token("user", expires_in=-10)
        headers = {"Authorization": f"Bearer {expired_token}"}
        resp = await client.post("/api/v1/scrape", json={"user_id": "u", "target_urls": []}, headers=headers)
        assert resp.status_code == 401

@pytest.mark.asyncio
async def test_jwt_auth_success_with_valid_token(monkeypatch):
    """Verify that a valid token allows the request to be processed successfully."""
    from backend.tasks import scrape_jobs
    monkeypatch.setattr(scrape_jobs, "delay", MagicMock(return_value=MagicMock(id="mock-task-id")))
    
    valid_token = generate_test_token("valid_user")
    headers = {"Authorization": f"Bearer {valid_token}"}
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/scrape",
            json={"user_id": "valid_user", "target_urls": ["https://jobs.example.com"]},
            headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"
```

---

### R1 E2E Test Strategy (AI Cover Letter Streaming & Tone Matching)
We recommend adding a test that validates the streaming behavior and the tone parameter injection:
1. **Mock standard AsyncGroq completions** to simulate a stream.
2. **Verify endpoint** `/api/v1/ai/generate-cover-letter` (or the new designated stream endpoint).
3. **Assert response headers** specify `Content-Type: text/event-stream`.
4. **Assert streamed chunks** are delivered correctly and the tone prompt requirements are included in the prompt.

#### Proposed Streaming Test Code Template:
```python
import json
import pytest
import httpx
from unittest.mock import MagicMock
from backend.main import app
from backend import ai_engine

@pytest.mark.asyncio
async def test_cover_letter_streaming_and_tone_matching(monkeypatch):
    """Verify Server-Sent Events (SSE) streaming and tone parameter validation."""
    
    # Mocking standard Groq completion chunk return structure
    class MockChatCompletionChunk:
        def __init__(self, content):
            self.choices = [
                MagicMock(delta=MagicMock(content=content))
            ]

    class MockAsyncIterator:
        def __init__(self, chunks):
            self.chunks = chunks
            self.index = 0
            
        def __aiter__(self):
            return self
            
        async def __anext__(self):
            if self.index >= len(self.chunks):
                raise StopAsyncIteration
            chunk = self.chunks[self.index]
            self.index += 1
            return MockChatCompletionChunk(chunk)

    captured_kwargs = {}
    async def mock_chat_create(*args, **kwargs):
        nonlocal captured_kwargs
        captured_kwargs = kwargs
        # Simulate returning a stream of cover letter content
        return MockAsyncIterator(["Dear ", "Hiring ", "Manager, ", "this ", "letter ", "is ", "professional."])

    # Patch client.chat.completions.create in ai_engine
    monkeypatch.setattr(ai_engine.client.chat.completions, "create", mock_chat_create)

    # Setup valid auth token for request (using the R4 auth standard secret)
    valid_token = generate_test_token("sre_applicant")
    headers = {
        "Authorization": f"Bearer {valid_token}",
        "Content-Type": "application/json"
    }

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/ai/generate-cover-letter",
            json={
                "user_cv": "Experienced Python Backend Engineer.",
                "job_description": "We need a Senior FastAPI Engineer.",
                "tone": "professional"
            },
            headers=headers
        )
        
        # Verify status code & SSE headers
        assert response.status_code == 200
        assert response.headers.get("content-type") == "text/event-stream"
        
        # Verify chunks received are correctly formatted SSE data
        lines = []
        async for line in response.aiter_lines():
            if line.strip():
                lines.append(line.strip())
                
        assert len(lines) > 0
        assert all(line.startswith("data:") for line in lines)
        
        # Verify the custom tone was parsed and injected in system messages
        system_msg = captured_kwargs.get("messages", [])[0]["content"]
        assert "tone" in system_msg.lower() or "professional" in system_msg.lower()
```

---

## 5. Verification Method

To verify the test suite:
1. After the backend agent completes the implementation of R1 and R4, merge the new test cases into the existing E2E testing files (or create `tests/e2e/test_jwt_and_streaming.py`).
2. Run the test command:
   ```powershell
   python -m pytest tests/e2e/
   ```
3. Inspect that the 17 existing tests and all newly added tests pass successfully.
4. **Invalidation condition**: If any E2E tests return `401` when they should return `200` (due to missing token in older tests), or if streaming fails to yield `text/event-stream` chunks, the E2E verification is invalid.
