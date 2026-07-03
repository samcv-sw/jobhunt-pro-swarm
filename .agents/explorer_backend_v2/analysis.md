# Backend Exploration and Architecture Report

## Executive Summary
This report analyzes the existing FastAPI backend code (`backend/main.py`, `backend/ai_engine.py`) and details the architecture for two key upcoming refactors:
1. **Non-blocking Streaming Cover Letter Generation** using Groq's LPU streaming interface, with customizable tone-matching capabilities.
2. **Clean JWT-based Authentication Integration** via a unified FastAPI dependency applied across all `/api/v1/*` endpoints.

---

## 1. Codebase Inspection

### 1.1 `backend/main.py`
The backend exposes a FastAPI application with the following key attributes:
- **Endpoints Registered**:
  - `GET /`: Simple welcome message.
  - `GET /health`: Health-check endpoint verifying the FastAPI, Celery, and Redis stack.
  - `POST /api/v1/scrape`: Offloads web-scraping to Celery using `asyncio.to_thread` to prevent event loop blocks.
  - `POST /api/v1/generate-cover-letter`: Offloads AI cover letter generation to Celery using `asyncio.to_thread`.
  - `POST /api/v1/accounts`: Synchronously creates a tenant account in SQLite and logs a sync entry to `SyncOutbox`.
  - `WS /ws/war-room`: Live WebSocket endpoint for real-time bidirection communication.
- **Middleware**: Configured with permissive CORS origins (`*`).
- **Dependencies**: None applied globally or per route yet.

### 1.2 `backend/ai_engine.py`
This module manages AI inference:
- **Client**: Initializes a single instance of `AsyncGroq` using:
  ```python
  client = AsyncGroq(
      api_key=os.environ.get("GROQ_API_KEY", "fallback-key-for-testing"),
  )
  ```
- **Inference Mode**: Synchronous completion using `client.chat.completions.create` with `llama3-70b-8192` model.
- **Response Format**: Enforces `response_format={"type": "json_object"}`. The response is parsed as a JSON object containing `subject` and `body` fields.

---

## 2. Refactoring for Streaming Responses (Server-Sent Events)

To achieve non-blocking, real-time token delivery to the client (yielding a much lower Time-To-First-Token), the endpoint should return a `StreamingResponse` using Server-Sent Events (SSE).

### 2.1 AsyncGroq Streaming Setup
To support streaming, we use `stream=True` in the client call. When streaming is enabled, `client.chat.completions.create` returns an async generator yielding chunks.

### 2.2 Proposed Generator Design (`backend/ai_engine.py`)
Because streaming in strict JSON mode can yield fragments of JSON syntax that are difficult to parse in real-time, it is recommended to stream the response as raw text, or format each chunk into a standardized Server-Sent Event (SSE) payload.

Here is the proposed streaming generator implementation:
```python
import json
from typing import AsyncIterator

async def generate_smart_cover_letter_stream(
    job_description: str, 
    user_cv: str, 
    tone: str = "professional"
) -> AsyncIterator[str]:
    """
    Generates a cover letter in real-time, streaming token chunks to the client.
    """
    tone_instruction = TONE_INSTRUCTIONS.get(tone.lower(), TONE_INSTRUCTIONS["professional"])
    
    system_prompt = f"""
    You are an expert executive recruiter and copywriter.
    Your task is to write a highly persuasive, concise cover letter based on the provided CV and Job Description.
    The tone of the cover letter must be: {tone.upper()}.
    Guidelines for this tone: {tone_instruction}

    First, output a compelling subject line formatted as 'Subject: <Subject Line>' followed by a double newline, then output the cover letter body.
    """
    
    user_prompt = f"""
    Job Description:
    {job_description}
    
    User CV:
    {user_cv}
    """
    
    try:
        # Enable stream=True for token-by-token generation
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama3-70b-8192",
            temperature=0.7,
            max_tokens=1024,
            stream=True
        )
        
        async for chunk in chat_completion:
            token = chunk.choices[0].delta.content
            if token:
                # Format chunk as a standard SSE event containing escaped JSON
                yield f"data: {json.dumps({'chunk': token})}\n\n"
                
    except Exception as e:
        logger.error(f"Streaming inference failure: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
```

---

## 3. Advanced Prompt Context: Tone Matching

To inject user-specific emotional and stylistic directives, we configure specific guidelines per tone. The system prompt dynamically reads these guidelines:

### 3.1 Tone Guidelines Registry
We define a dictionary mapped to supported tones:
```python
TONE_INSTRUCTIONS = {
    "professional": (
        "Maintain a polished, formal, and respectful tone. Focus on structured achievements, "
        "industry standards, and how your skills align with the company's operational excellence."
    ),
    "confident": (
        "Write with high energy, assertiveness, and strong self-assurance. Focus on impact, leadership, "
        "measurable outcomes, and a proactive stance on solving the company's challenges."
    ),
    "creative": (
        "Use engaging, storytelling-driven language. Showcase unique problem-solving perspectives, "
        "passion, and a conversational yet professional style that stands out from standard applications."
    ),
}
```

### 3.2 Dynamic Prompt Assembly
When the endpoint is invoked, the `tone` parameter (validated via Pydantic schema) is looked up in the `TONE_INSTRUCTIONS` map. If not found, it defaults to `"professional"`. This instruction is cleanly interpolated into the `system_prompt`.

---

## 4. JWT-Based Authentication Architecture

All `/api/v1/*` endpoints must be secured using JWT tokens. Since `PyJWT` is already installed in the environment (v2.12.1), we can design a clean dependency in a new file `backend/auth.py`.

### 4.1 Dependency File: `backend/auth.py`
```python
import os
import datetime
from typing import Dict, Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Read environment variables with secure defaults
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-fallback-secret-for-local-testing")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

security = HTTPBearer()

async def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to validate the incoming JWT token in the Authorization header.
    Returns the token payload if valid.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_access_token(data: dict, expires_delta: datetime.timedelta = None) -> str:
    """
    Utility helper to generate JWT access tokens (used for local mock testing).
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### 4.2 Secure Routing Integration in `backend/main.py`
To secure all endpoints under `/api/v1/*` without touching non-API routes (like `/health` or web sockets), we should group the endpoints inside a FastAPI `APIRouter` with the authentication dependency pre-configured.

#### Current Code Pattern:
```python
@app.post("/api/v1/scrape")
async def trigger_scrape(...): ...
```

#### Proposed Code Pattern:
```python
from fastapi import APIRouter, Depends
from .auth import verify_jwt

# Create router for all V1 API routes, enforcing JWT auth
api_v1_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(verify_jwt)]
)

@api_v1_router.post("/scrape")
async def trigger_scrape(req: ScrapeRequest, request: Request = None):
    # Endpoint logic remains unchanged
    ...

@api_v1_router.post("/generate-cover-letter")
async def trigger_cover_letter(req: CoverLetterRequest, request: Request = None):
    # Returns StreamingResponse
    ...

@api_v1_router.post("/accounts")
async def create_account(req: AccountCreateRequest):
    ...

# Register the router in the app
app.include_router(api_v1_router)
```

---

## 5. Endpoints Analysis & Verification Strategy

### 5.1 Currently Implemented Endpoints
- `POST /api/v1/scrape`: Enqueues scraping task.
- `POST /api/v1/generate-cover-letter`: Enqueues cover letter generation.
- `POST /api/v1/accounts`: Writes locally and registers database sync.

### 5.2 Verification and Test Strategy
To comprehensively verify the refactored endpoints, the test suite should target:
1. **Authentication Enforcement**:
   - Verify that requests missing or having invalid `Authorization` header receive a `401 Unauthorized` status.
   - Verify that requests with valid tokens pass through successfully.
2. **Streaming Event Validity**:
   - Verify that `/api/v1/generate-cover-letter` returns a `text/event-stream` media type.
   - Mock the `AsyncGroq` client streaming output to yield predictable chunks, asserting that the response streams individual text chunks correctly.
3. **Non-blocking Behavior**:
   - Ensure the event loop remains responsive (measured via latency monitoring tasks) when concurrently processing multiple streaming connections.

#### Mock Testing Design (`tests/test_backend_secured.py` - Draft)
```python
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.auth import create_access_token

@pytest.mark.asyncio
async def test_api_endpoints_enforce_auth():
    """Verify that all api/v1 routes return 401 without token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Scrape
        resp = await client.post("/api/v1/scrape", json={})
        assert resp.status_code == 401
        
        # 2. Generate Cover Letter
        resp = await client.post("/api/v1/generate-cover-letter", json={})
        assert resp.status_code == 401

@pytest.mark.asyncio
async def test_generate_cover_letter_streaming_success(monkeypatch):
    """Verify cover letter endpoint streams chunks with a valid token."""
    # Generate mock token
    token = create_access_token(data={"sub": "test-user"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Mock generator inside ai_engine
    async def mock_stream(*args, **kwargs):
        yield "data: {\"chunk\": \"Hello\"}\n\n"
        yield "data: {\"chunk\": \" World\"}\n\n"

    monkeypatch.setattr("backend.ai_engine.generate_smart_cover_letter_stream", mock_stream)
    
    payload = {
        "user_cv": "Mock CV",
        "job_description": "Mock Job",
        "tone": "confident"
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/generate-cover-letter", 
            json=payload, 
            headers=headers
        )
        
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    
    # Read streamed response content
    chunks = [line async for line in response.aiter_lines()]
    assert "data: {\"chunk\": \"Hello\"}" in chunks
    assert "data: {\"chunk\": \" World\"}" in chunks
```

---

## 6. Python Package Dependencies Verification
From inspecting the active virtual environment:
- `groq` (v0.37.1) is installed.
- `PyJWT` (v2.12.1) is installed.
- `cryptography` (v48.0.0) is installed.
- `joserfc` (v1.7.2) is installed.
- `passlib` is not installed. 

**Recommendation**:
- Use `PyJWT` for decoding and validating JWT tokens in `backend/auth.py`. No additional JWT or cryptography libraries are required.
- `passlib` is not required for this API tier since the backend acts as a consumer/validator of tokens generated elsewhere (or uses standard JWT verification), avoiding direct database password hashing.
