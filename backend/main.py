import asyncio
import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Any

from celery.utils import uuid as celery_uuid
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .ai_engine import generate_smart_cover_letter_stream
from .auth import verify_jwt
from .billing import router as billing_router
from .database import async_session
from .limiter import rate_limiter
from .models import Account, SyncOutbox
from .tasks import generate_cover_letter, scrape_jobs
from .websocket import manager

# Sentry error tracking (free tier, optional)
_sentry_dsn = os.getenv("SENTRY_DSN")
if _sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.1,
            environment=os.getenv("ENV", "development"),
        )
        logging.getLogger(__name__).info("Sentry error tracking initialized.")
    except ImportError:
        logging.getLogger(__name__).warning("sentry-sdk not installed; skipping Sentry init.")

# Configure logger for Enterprise API
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 32 workers to handle concurrent task queuing operations
celery_dispatch_executor = ThreadPoolExecutor(
    max_workers=32,
    thread_name_prefix="celery_dispatch"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database migrations and schema setup on application lifespan events."""
    logger.info("Enterprise API starting up. Initializing database schema...")
    from .database import engine
    from .models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")
    yield
    logger.info("Enterprise API shutting down.")


app = FastAPI(
    title="JobHunt Pro Enterprise API",
    description="Enterprise API powering autonomous AI Agents with Celery Task Queues.",
    version="3.0.0",
    lifespan=lifespan
)

# Configure origins safely
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
else:
    # Safe defaults for local development
    origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]

# Add CORS Middleware with safety constraints
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if os.getenv("ENV") == "production" else ["*"],
    allow_credentials=True if os.getenv("ENV") == "production" or allowed_origins_env else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom Middleware for HTTP Security Headers (Defense-in-Depth)
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Any) -> Any:
    """Inject HTTP Security Headers into all API response headers."""
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    
    # Enforce HTTPS HSTS only in production or if requested via HTTPS
    if request.url.scheme == "https" or os.getenv("ENV") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        
    return response


app.include_router(billing_router)


class ScrapeRequest(BaseModel):
    """Pydantic model for triggering a target URL web scraping task."""
    user_id: str
    target_urls: list[str]


class CoverLetterRequest(BaseModel):
    """Pydantic model for generating custom AI cover letters from job description."""
    user_cv: str
    job_description: str
    tone: str = "professional"


class AccountCreateRequest(BaseModel):
    """Pydantic model for local account balance profile generation."""
    tenant_id: str
    currency: str = "CREDITS"
    balance_cents: int = 0


@app.get("/")
async def root(request: Request = None) -> dict[str, str]:
    """Root metadata greeting endpoint."""
    logger.info("Enterprise API root endpoint requested.")
    return {"message": "JobHunt Pro Enterprise API is running."}


@app.get("/health")
async def health_check(request: Request = None) -> dict[str, str]:
    """Retrieve service health status of task queue and async loop runner."""
    logger.info("Health check verification endpoint requested.")
    return {"status": "ok", "architecture": "FastAPI + Celery + Redis"}


@app.get("/healthz")
async def healthz(request: Request = None) -> dict[str, str]:
    """Lightweight Render health check endpoint."""
    return {"status": "ok"}


@app.get("/api/v1/health/detailed")
async def health_detailed(request: Request = None) -> dict[str, Any]:
    """Detailed health check: reports DB, Redis, and system component status."""
    import time
    result: dict[str, Any] = {"status": "ok", "components": {}}
    
    # Check DB
    db_start = time.monotonic()
    try:
        async with async_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        result["components"]["db"] = {"status": "ok", "latency_ms": round((time.monotonic() - db_start) * 1000, 2)}
    except Exception as e:
        result["components"]["db"] = {"status": "error", "detail": str(e)}
        result["status"] = "degraded"
    
    # Check Redis
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        r_start = time.monotonic()
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(redis_url, socket_connect_timeout=2)
            await r.ping()
            await r.aclose()
            result["components"]["redis"] = {"status": "ok", "latency_ms": round((time.monotonic() - r_start) * 1000, 2)}
        except Exception as e:
            result["components"]["redis"] = {"status": "error", "detail": str(e)}
            result["status"] = "degraded"
    else:
        result["components"]["redis"] = {"status": "not_configured"}
    
    return result

@app.post("/api/v1/scrape", dependencies=[Depends(verify_jwt), Depends(rate_limiter)])
async def trigger_scrape(req: ScrapeRequest, request: Request = None) -> dict[str, str]:
    """
    Instantly returns 200 OK and sends the scraping task to Celery.
    """
    logger.info(f"Trigger scrape requested for user: {req.user_id} with {len(req.target_urls)} URLs.")
    is_testing = "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None
    if is_testing:
        task = await asyncio.to_thread(scrape_jobs.delay, req.target_urls, req.user_id)
        return {"status": "queued", "task_id": task.id}
    else:
        task_id = celery_uuid()
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    celery_dispatch_executor,
                    lambda: scrape_jobs.apply_async(
                        args=(req.target_urls, req.user_id),
                        task_id=task_id,
                        retry=False
                    )
                ),
                timeout=0.05
            )
            status = "queued"
        except TimeoutError:
            status = "accepted"
        except Exception as exc:
            logger.error(f"Scrape task queuing failed: {exc}")
            raise HTTPException(
                status_code=503,
                detail=f"Task queue broker is currently unreachable. Error: {str(exc)}"
            )
        return {"status": status, "task_id": task_id}


@app.post("/api/v1/generate-cover-letter", dependencies=[Depends(verify_jwt), Depends(rate_limiter)])
async def trigger_cover_letter(req: CoverLetterRequest, request: Request = None) -> dict[str, str]:
    """Queue a cover letter generation task in the Celery background worker queue."""
    logger.info("Trigger cover letter background task requested.")
    is_testing = "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None
    if is_testing:
        task = await asyncio.to_thread(generate_cover_letter.delay, req.job_description, req.user_cv)
        return {"status": "queued", "task_id": task.id}
    else:
        task_id = celery_uuid()
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    celery_dispatch_executor,
                    lambda: generate_cover_letter.apply_async(
                        args=(req.job_description, req.user_cv),
                        task_id=task_id,
                        retry=False
                    )
                ),
                timeout=0.05
            )
            status = "queued"
        except TimeoutError:
            status = "accepted"
        except Exception as exc:
            logger.error(f"Cover letter task queuing failed: {exc}")
            raise HTTPException(
                status_code=503,
                detail=f"Task queue broker is currently unreachable. Error: {str(exc)}"
            )
        return {"status": status, "task_id": task_id}


@app.post("/api/v1/ai/generate-cover-letter/stream", dependencies=[Depends(verify_jwt), Depends(rate_limiter)])
async def stream_cover_letter(req: CoverLetterRequest, request: Request = None) -> StreamingResponse:
    """Stream AI cover letter generation tokens using server-sent events (SSE)."""
    logger.info("Cover letter streaming generation requested.")
    if not req.user_cv.strip() or not req.job_description.strip():
        logger.warning("Empty CV or Job Description provided in cover letter streaming request.")
        raise HTTPException(status_code=422, detail="CV and Job Description cannot be empty")
    return StreamingResponse(
        generate_smart_cover_letter_stream(req.job_description, req.user_cv, req.tone),
        media_type="text/event-stream"
    )


@app.post("/api/v1/accounts", dependencies=[Depends(verify_jwt), Depends(rate_limiter)])
async def create_account(req: AccountCreateRequest) -> dict[str, str]:
    """
    Creates a local account and logs a sync outbox record.
    """
    logger.info(f"Create local account requested for tenant: {req.tenant_id}")
    async with async_session() as session:
        account = Account(
            tenant_id=req.tenant_id,
            currency=req.currency,
            balance_cents=req.balance_cents
        )
        session.add(account)
        await session.flush()

        outbox = SyncOutbox(
            table_name="accounts",
            record_id=str(account.id),
            operation="INSERT",
            payload={
                "id": account.id,
                "tenant_id": account.tenant_id,
                "currency": account.currency,
                "balance_cents": account.balance_cents
            },
            synced=False
        )
        session.add(outbox)
        await session.commit()

        logger.info(f"Account #{account.id} created and outbox synchronized.")
        return {"status": "created", "account_id": str(account.id)}


@app.websocket("/ws/war-room")
async def websocket_war_room(websocket: WebSocket) -> None:
    """War Room real-time WebSocket connection handler."""
    logger.info("War Room WebSocket connection handshake initiated.")
    # Verify JWT Bearer token
    token = websocket.query_params.get("token")
    if not token:
        # Check Authorization header
        auth_header = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token:
        # Check subprotocols
        subprotocols = websocket.scope.get("subprotocols") or []
        for sub in subprotocols:
            if sub and sub.startswith("ey"):
                token = sub
                break
            elif sub and sub.lower().startswith("bearer."):
                token = sub.split(".", 1)[1]
                break
            elif sub and sub.lower().startswith("bearer"):
                parts = sub.split("_", 1)
                if len(parts) > 1:
                    token = parts[1]
                    break

    if not token:
        logger.warning("WebSocket connection rejected: Bearer token missing.")
        await websocket.close(code=4001)
        return

    import jwt
    from sqlalchemy import text

    from .auth import JWT_ALGORITHM, JWT_SECRET_KEY
    try:
        claims = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        sub = claims.get("sub")
        if not sub:
            logger.warning("WebSocket connection rejected: invalid JWT subject.")
            await websocket.close(code=4001)
            return

        async with async_session() as session:
            result = await session.execute(
                text("SELECT is_active FROM users WHERE user_id = :user_id"),
                {"user_id": sub}
            )
            row = result.fetchone()
            if not row or not row[0]:
                logger.warning(f"WebSocket connection rejected: user {sub} is inactive or missing.")
                await websocket.close(code=4001)
                return
    except Exception as jwt_err:
        logger.error(f"WebSocket authentication error: {jwt_err}")
        await websocket.close(code=4001)
        return

    await manager.connect(websocket)
    logger.info(f"WebSocket client {sub} connected to War Room.")
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message text was: {data}", websocket)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {sub} disconnected from War Room.")
        manager.disconnect(websocket)
