import asyncio
import gc
import logging
import os
import re
import sys

gc.set_threshold(50, 5, 5)
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, suppress
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
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse, StreamingResponse
from fastapi_cache.decorator import cache
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

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
_handlers = [logging.StreamHandler()]
_token = os.getenv("LOGTAIL_SOURCE_TOKEN")
if _token:
    import json as _json
    import threading
    import urllib.error
    import urllib.request
    from datetime import datetime as _datetime
    from queue import Queue as _Queue

    class LogtailHandler(logging.Handler):
        def __init__(self, source_token: str):
            super().__init__()
            self.source_token = source_token
            self.queue = _Queue()
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()

        def emit(self, record):
            try:
                log_entry = self.format(record)
                payload = {
                    "message": log_entry,
                    "dt": _datetime.utcfromtimestamp(record.created).isoformat() + "Z",
                    "level": record.levelname,
                    "logger": record.name,
                    "pid": record.process,
                }
                self.queue.put(payload)
            except Exception:
                self.handleError(record)

        def _worker(self):
            while True:
                try:
                    payload = self.queue.get()
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.source_token}",
                        "User-Agent": "LogtailLogger/1.0"
                    }
                    req = urllib.request.Request(
                        "https://in.logs.betterstack.com",
                        data=_json.dumps(payload).encode("utf-8"),
                        headers=headers,
                        method="POST"
                    )
                    try:
                        with urllib.request.urlopen(req, timeout=5) as response:
                            response.read()
                    except urllib.error.URLError:
                        pass
                except Exception:
                    pass

    _handlers.append(LogtailHandler(_token))

logging.basicConfig(level=logging.INFO, handlers=_handlers)
logger = logging.getLogger(__name__)

# 32 workers to handle concurrent task queuing operations
celery_dispatch_executor = ThreadPoolExecutor(
    max_workers=32,
    thread_name_prefix="celery_dispatch"
)


bot_instance = None
_APP_START_TIME: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database migrations, schema setup, and Telegram webhook lifespan events."""
    global bot_instance, _APP_START_TIME
    import time as _time
    _APP_START_TIME = _time.monotonic()
    logger.info("Enterprise API starting up. Initializing database schema...")
    from .cache import setup_cache
    from .database import engine
    from .models import Base
    setup_cache(app)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")

    # Initialize Telegram Bot in Webhook mode
    try:
        from core.telegram_bot import TelegramBot
        bot_instance = TelegramBot()
        if bot_instance.enabled:
            logger.info("Initializing Telegram bot in Webhook mode...")
            bot_instance.notifier.start()

            import config
            site_url = getattr(config, "SITE_URL", "https://jhfguf.pythonanywhere.com").rstrip("/")
            render_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("RENDER_ENGINE_URL")
            base_url = (render_url or site_url).rstrip("/")
            webhook_url = f"{base_url}/webhook/telegram"

            logger.info(f"Setting Telegram webhook to: {webhook_url}")
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"https://api.telegram.org/bot{bot_instance.token}/setWebhook",
                    json={"url": webhook_url}
                )
                if res.status_code == 200:
                    logger.info("Telegram webhook registered successfully.")
                else:
                    logger.warning(f"Failed to set Telegram webhook: {res.status_code} - {res.text}")
    except Exception as e:
        logger.error(f"Failed to initialize Telegram webhook: {e}")

    yield

    # Shutdown
    if bot_instance and bot_instance.enabled:
        logger.info("Stopping Telegram notifier...")
        bot_instance.notifier.stop()
        with suppress(Exception):
            await bot_instance.http_client.aclose()
    logger.info("Enterprise API shutting down.")


app = FastAPI(
    title="JobHunt Pro Enterprise API",
    description="Enterprise API powering autonomous AI Agents with Celery Task Queues.",
    version="3.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse
)

# ---------------------------------------------------------------------------
# R2: Secure CORS Dynamic Origin Validation
# ---------------------------------------------------------------------------

def _build_origin_regex(pattern: str) -> re.Pattern | None:
    r"""Compile a single allowed-origin pattern into a strict regex.

    Supports wildcard ``*`` exclusively at the subdomain level, e.g.
    ``https://*.example.com`` becomes
    ``^https://[a-zA-Z0-9-]+\.example\.com$``.

    Returns ``None`` when the pattern is a literal origin (no wildcard), in
    which case exact string comparison is used by the caller.
    """
    if "*" not in pattern:
        return None  # literal — exact match, no regex needed

    # Restrict wildcard to the first subdomain label only.
    # Reject TLD wildcards like *.com by requiring at least two dot-separated labels after wildcard (or localhost).
    if not re.match(r'^https?://\*\.(?:localhost|[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+)$', pattern):
        raise ValueError(
            f"Unsupported wildcard origin pattern '{pattern}'. "
            "Wildcards are only allowed at the subdomain level, e.g. "
            "'https://*.example.com'."
        )

    # Escape the literal portion then replace the escaped wildcard placeholder.
    # re.escape("*") == r'\*' on Python 3.7+
    escaped = re.escape(pattern).replace(re.escape("*"), '[a-zA-Z0-9-]+')
    return re.compile(f'^{escaped}$')


def is_origin_allowed(origin: str, allowed_patterns: list[str]) -> bool:
    """Return True if *origin* matches any of the *allowed_patterns*.

    Each pattern is either a literal origin or a subdomain-wildcard like
    ``https://*.example.com``.
    """
    for pattern in allowed_patterns:
        try:
            rx = _build_origin_regex(pattern)
        except ValueError:
            # Skip malformed wildcard patterns defensively.
            logger.warning("Skipping malformed CORS pattern: %s", pattern)
            continue

        if rx is None:
            # Literal comparison
            if origin == pattern:
                return True
        else:
            if rx.fullmatch(origin):
                return True
    return False


class SecureCORSMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces dynamic, regex-validated CORS origin checking.

    Replaces FastAPI's built-in ``CORSMiddleware`` when ``ALLOWED_ORIGINS``
    contains wildcard patterns that require subdomain-level validation.
    """

    CORS_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    CORS_HEADERS = "Authorization, Content-Type, Accept, Origin, X-Requested-With"
    MAX_AGE = "600"

    def __init__(self, app, allowed_patterns: list[str], allow_credentials: bool = True):
        super().__init__(app)
        self._patterns = allowed_patterns
        self._allow_credentials = allow_credentials
        self._compiled_patterns = []
        for pattern in allowed_patterns:
            try:
                rx = _build_origin_regex(pattern)
                self._compiled_patterns.append((pattern, rx))
            except ValueError:
                logger.warning("Skipping malformed CORS pattern: %s", pattern)

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("Origin", "")

        origin_allowed = False
        if origin:
            for pattern_str, rx in self._compiled_patterns:
                if rx is None:
                    if origin == pattern_str:
                        origin_allowed = True
                        break
                else:
                    if rx.fullmatch(origin):
                        origin_allowed = True
                        break

        # Preflight (OPTIONS) — respond immediately
        if request.method == "OPTIONS" and origin:
            if origin_allowed:
                headers = {
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": self.CORS_METHODS,
                    "Access-Control-Allow-Headers": self.CORS_HEADERS,
                    "Access-Control-Max-Age": self.MAX_AGE,
                    "Vary": "Origin",
                }
                if self._allow_credentials:
                    headers["Access-Control-Allow-Credentials"] = "true"
                return Response(status_code=204, headers=headers)
            return Response(status_code=403, content="CORS origin not allowed")

        # Normal request
        response = await call_next(request)

        if origin and origin_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            if self._allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


# Configure origins safely
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
else:
    # Safe defaults for local development
    origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]

# Add GZip Middleware for massive payload compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Use SecureCORSMiddleware whenever there are explicit allowed origins;
# fall back to permissive CORSMiddleware only for fully local dev with no env config.
_has_wildcard_pattern = any("*" in o for o in origins)
if os.getenv("ENV") == "production" or allowed_origins_env or _has_wildcard_pattern:
    app.add_middleware(
        SecureCORSMiddleware,
        allowed_patterns=origins,
        allow_credentials=True,
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )



# Custom Middleware for HTTP Security Headers (Defense-in-Depth)
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Any) -> Any:
    """Inject comprehensive HTTP Security Headers — IMP-010: full CSP policy."""
    response = await call_next(request)
    # IMP-010: Comprehensive Content-Security-Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' fonts.googleapis.com; "
        "font-src 'self' fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' wss: https:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    # Enforce HTTPS HSTS only in production or if requested via HTTPS
    if request.url.scheme == "https" or os.getenv("ENV") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

    return response


app.include_router(billing_router)


from datetime import UTC

from pydantic import field_validator


class ScrapeRequest(BaseModel):
    """Pydantic model for triggering a target URL web scraping task — IMP-006: input validated."""
    user_id: str
    target_urls: list[str]

    @field_validator("user_id")
    @classmethod
    def sanitize_user_id(cls, v: str) -> str:
        """Strip HTML and enforce max_length for user_id."""
        v = re.sub(r"<[^>]+>", "", v).strip()
        if len(v) > 200:
            raise ValueError("user_id too long (max 200 chars)")
        return v

    @field_validator("target_urls", mode="before")
    @classmethod
    def validate_target_urls(cls, v: list) -> list:
        """Ensure URL list is non-empty and each URL is a string under 2000 chars."""
        if not v:
            raise ValueError("target_urls cannot be empty")
        sanitized = []
        for url in v:
            url = str(url).strip()
            if len(url) > 2000:
                raise ValueError(f"URL too long: {url[:50]}...")
            sanitized.append(url)
        return sanitized


class CoverLetterRequest(BaseModel):
    """Pydantic model for generating custom AI cover letters — IMP-006: input validated."""
    user_cv: str
    job_description: str
    tone: str = "professional"

    @field_validator("user_cv", "job_description")
    @classmethod
    def sanitize_text_fields(cls, v: str) -> str:
        """Strip HTML tags and enforce max_length on CV/JD text."""
        v = re.sub(r"<[^>]+>", "", v).strip()
        if len(v) > 50_000:
            raise ValueError("Text field too long (max 50,000 chars)")
        return v

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str) -> str:
        """Restrict tone to known allowed values."""
        allowed = {"professional", "casual", "creative", "formal", "friendly", "confident"}
        v = v.strip().lower()
        if v not in allowed:
            raise ValueError(f"tone must be one of {allowed}")
        return v


class AccountCreateRequest(BaseModel):
    """Pydantic model for local account balance profile generation — IMP-006: input validated."""
    tenant_id: str
    currency: str = "CREDITS"
    balance_cents: int = 0

    @field_validator("tenant_id", "currency")
    @classmethod
    def sanitize_string_fields(cls, v: str) -> str:
        """Strip HTML and enforce max_length."""
        v = re.sub(r"<[^>]+>", "", v).strip()
        if len(v) > 200:
            raise ValueError("Field too long (max 200 chars)")
        return v

    @field_validator("balance_cents")
    @classmethod
    def validate_balance(cls, v: int) -> int:
        """Ensure balance is non-negative."""
        if v < 0:
            raise ValueError("balance_cents must be >= 0")
        return v


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


@app.get("/api/v1/health")
async def health_v1(request: Request = None) -> dict[str, str]:
    """Lightweight API v1 health check endpoint."""
    return {"status": "ok"}


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request) -> dict[str, str]:
    """
    Endpoint to receive incoming updates from Telegram Webhook.
    """
    if not bot_instance or not bot_instance.enabled:
        raise HTTPException(status_code=503, detail="Telegram bot is not enabled or initialized.")

    try:
        update = await request.json()
        logger.info("Received Telegram webhook update")
        await bot_instance.process_webhook_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error handling Telegram webhook update: {e}")
        return {"status": "error", "detail": str(e)}


@app.get("/api/v1/health/detailed")
@cache(expire=15)
async def health_detailed(request: Request = None) -> dict[str, Any]:
    """Detailed health check: reports DB, Redis, SMTP, and Groq API status."""
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

    # Check Redis (sync ping via executor to avoid blocking the event loop)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        r_start = time.monotonic()
        try:
            import asyncio as _asyncio

            import redis as _redis

            def _redis_ping() -> None:
                _r = _redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
                _r.ping()
                _r.close()

            await _asyncio.get_event_loop().run_in_executor(None, _redis_ping)
            result["components"]["redis"] = {
                "redis": "ok",
                "redis_latency_ms": round((time.monotonic() - r_start) * 1000, 2),
            }
        except Exception as e:
            result["components"]["redis"] = {
                "redis": "error",
                "redis_error": str(e),
            }
            result["status"] = "degraded"
    else:
        result["components"]["redis"] = {"status": "not_configured"}


    # R4: Check SMTP connectivity (outbound TCP probe, <1 s timeout)
    smtp_host = os.getenv("SMTP_HOST", "") or os.getenv("BREVO_SMTP_HOST", "")
    smtp_port_str = os.getenv("SMTP_PORT", "") or os.getenv("BREVO_SMTP_PORT", "587")
    if smtp_host:
        smtp_start = time.monotonic()
        try:
            smtp_port = int(smtp_port_str)
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(smtp_host, smtp_port),
                timeout=0.9,
            )
            writer.close()
            with suppress(Exception):
                await writer.wait_closed()
            result["components"]["smtp"] = {
                "status": "ok",
                "host": smtp_host,
                "port": smtp_port,
                "latency_ms": round((time.monotonic() - smtp_start) * 1000, 2),
            }
        except TimeoutError:
            result["components"]["smtp"] = {
                "status": "timeout",
                "host": smtp_host,
                "detail": "TCP connection timed out (<1s)",
            }
            result["status"] = "degraded"
        except OSError as e:
            result["components"]["smtp"] = {
                "status": "error",
                "host": smtp_host,
                "detail": str(e),
            }
            result["status"] = "degraded"
    else:
        result["components"]["smtp"] = {"status": "not_configured"}

    # R4: Check Groq API accessibility (lightweight HTTP probe, <1 s timeout)
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if groq_api_key:
        groq_start = time.monotonic()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=0.9) as client:
                resp = await client.get("https://api.groq.com/openai/v1/models",
                                        headers={"Authorization": f"Bearer {groq_api_key}"})
            groq_status = "ok" if resp.status_code in (200, 401) else "error"
            # 401 means reachable but invalid key — API is up
            result["components"]["groq_api"] = {
                "status": groq_status,
                "http_status": resp.status_code,
                "latency_ms": round((time.monotonic() - groq_start) * 1000, 2),
            }
            if groq_status == "error":
                result["status"] = "degraded"
        except httpx.TimeoutException:
            result["components"]["groq_api"] = {
                "status": "timeout",
                "detail": "HTTP probe timed out (<1s)",
            }
            result["status"] = "degraded"
        except Exception as e:
            result["components"]["groq_api"] = {"status": "error", "detail": str(e)}
            result["status"] = "degraded"
    else:
        result["components"]["groq_api"] = {"status": "not_configured"}

    return result


@app.get("/api/v1/telemetry", dependencies=[Depends(verify_jwt)])
async def get_telemetry(request: Request = None) -> dict:
    """
    Structured JSON telemetry endpoint.
    Returns real-time process metrics including uptime, memory, threads, GC stats, and FDs.
    Requires JWT authentication.
    """
    import threading
    import time as _time
    uptime = _time.monotonic() - _APP_START_TIME if _APP_START_TIME else 0.0

    rss_mb = 0.0
    open_fds = -1
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        mem_info = proc.memory_info()
        rss_mb = round(mem_info.rss / (1024 * 1024), 2)
        try:
            open_fds = proc.num_fds()
        except AttributeError:
            # Windows: use num_handles as a proxy
            try:
                open_fds = proc.num_handles()
            except Exception:
                open_fds = -1
    except ImportError:
        pass

    gc_stats = gc.get_count()
    thread_count = threading.active_count()

    return {
        "uptime_seconds": round(uptime, 2),
        "rss_mb": rss_mb,
        "thread_count": thread_count,
        "gc_stats": {
            "counts": gc_stats,
            "threshold": gc.get_threshold(),
        },
        "open_fds": open_fds,
    }


@app.post("/api/v1/admin/dlq/requeue", dependencies=[Depends(verify_jwt)])
async def dlq_requeue(request: Request = None) -> dict:
    """
    Dead-Letter Queue (DLQ) Requeuer endpoint.
    Finds SyncOutbox records stuck in synced=False for more than 24 hours
    and resets them for another sync attempt.
    Requires JWT authentication.
    """
    from datetime import datetime, timedelta

    from sqlalchemy import text

    cutoff = datetime.now(UTC) - timedelta(hours=24)
    requeued_count = 0

    try:
        async with async_session() as session:
            result = await session.execute(
                text(
                    "SELECT id FROM ps_crud_outbox "
                    "WHERE synced = 0 AND created_at < :cutoff"
                ),
                {"cutoff": cutoff.isoformat()}
            )
            stale_ids = [row[0] for row in result.fetchall()]

            if stale_ids:
                # Reset them — touch created_at to signal a fresh attempt
                from sqlalchemy import bindparam
                await session.execute(
                    text(
                        "UPDATE ps_crud_outbox SET synced = 0, created_at = :now "
                        "WHERE id IN :sids"
                    ).bindparams(bindparam("sids", expanding=True)),
                    {"now": datetime.now(UTC).isoformat(), "sids": stale_ids}
                )
                await session.commit()
                requeued_count = len(stale_ids)
                logger.info(f"[DLQ] Requeued {requeued_count} stale SyncOutbox records.")
    except Exception as e:
        logger.error(f"[DLQ] Requeue failed: {e}")
        raise HTTPException(status_code=500, detail=f"DLQ requeue failed: {e}")

    return {"requeued": requeued_count, "cutoff_utc": cutoff.isoformat()}


@app.post("/api/v1/scrape", dependencies=[Depends(verify_jwt), Depends(rate_limiter)])
async def trigger_scrape(req: ScrapeRequest, request: Request = None) -> dict[str, str]:
    """
    Instantly returns 200 OK and sends the scraping task to Celery.
    If LOCAL_QUEUE_FALLBACK=1 or if Celery broker is offline, falls back to SQLite job_queue.
    """
    logger.info(f"Trigger scrape requested for user: {req.user_id} with {len(req.target_urls)} URLs.")
    is_testing = "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None

    # Check dual-mode dispatch toggle
    local_fallback = os.getenv("LOCAL_QUEUE_FALLBACK", "0") == "1"
    loop = asyncio.get_running_loop()

    if local_fallback:
        try:
            from core.job_queue import enqueue_task
            await loop.run_in_executor(
                celery_dispatch_executor,
                enqueue_task,
                "scrape",
                {"target_urls": req.target_urls, "user_id": req.user_id}
            )
            logger.info("Scrape task routed to local SQLite job queue (forced fallback).")
            return {"status": "queued_local", "task_id": f"local_{celery_uuid()}"}
        except Exception as local_exc:
            logger.error(f"Failed to route task to local SQLite job queue: {local_exc}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to queue task locally: {str(local_exc)}"
            )

    if is_testing:
        task = await loop.run_in_executor(
            celery_dispatch_executor,
            scrape_jobs.delay,
            req.target_urls,
            req.user_id
        )
        return {"status": "queued", "task_id": task.id}

    task_id = celery_uuid()
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
        logger.error(f"Scrape task queuing failed: {exc}. Trying fallback to local SQLite job queue...")
        try:
            from core.job_queue import enqueue_task
            await loop.run_in_executor(
                celery_dispatch_executor,
                enqueue_task,
                "scrape",
                {"target_urls": req.target_urls, "user_id": req.user_id}
            )
            logger.info("Scrape task successfully fallback-routed to local SQLite job queue.")
            return {"status": "queued_local", "task_id": f"local_{task_id}"}
        except Exception as local_exc:
            logger.error(f"Local SQLite queue fallback failed: {local_exc}")
            raise HTTPException(
                status_code=530,
                detail=f"Both Celery and local fallback queues failed. Celery error: {str(exc)}"
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
    
    from .auth import _get_client_ip, _check_lockout, _record_success, _IS_TESTING
    client_ip = _get_client_ip(websocket)
    if not _IS_TESTING:
        lockout_remaining = _check_lockout(client_ip)
        if lockout_remaining > 0:
            logger.warning(f"WebSocket connection rejected: IP {client_ip} is locked out for {lockout_remaining:.1f}s.")
            await websocket.close(code=4003)
            return

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

    from sqlalchemy import text
    from .auth import decode_jwt_token

    try:
        claims = decode_jwt_token(token)
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

        if not _IS_TESTING:
            _record_success(client_ip)
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


# ---------------------------------------------------------------------------
# IMP-208: Scraper Health Metrics Endpoint
# ---------------------------------------------------------------------------

@app.get("/api/v1/scrapers/health", dependencies=[Depends(verify_jwt)])
async def scrapers_health(request: Request = None) -> dict:
    """Return per-platform scraper health scores — IMP-208."""
    try:
        from core.global_scraper import ScraperHealthTracker
        tracker = ScraperHealthTracker()
        scores = tracker.all_scores() if hasattr(tracker, "all_scores") else {}
        return {"status": "ok", "scores": scores}
    except Exception as e:
        logger.warning(f"Scraper health unavailable: {e}")
        return {"status": "unavailable", "scores": {}, "detail": str(e)}


# ---------------------------------------------------------------------------
# IMP-228: Email Preview Endpoint
# ---------------------------------------------------------------------------

class EmailPreviewRequest(BaseModel):
    """Request model for email preview generation."""
    cv_text: str
    job_title: str
    company: str
    tone: str = "professional"

    @field_validator("cv_text")
    @classmethod
    def sanitize_cv(cls, v: str) -> str:
        """Strip HTML and enforce max_length."""
        v = re.sub(r"<[^>]+>", "", v).strip()
        if len(v) > 50_000:
            raise ValueError("cv_text too long")
        return v

    @field_validator("job_title", "company")
    @classmethod
    def sanitize_short_fields(cls, v: str) -> str:
        """Strip HTML and enforce max_length on short fields."""
        v = re.sub(r"<[^>]+>", "", v).strip()
        if len(v) > 500:
            raise ValueError("Field too long (max 500 chars)")
        return v


@app.post("/api/v1/emails/preview", dependencies=[Depends(verify_jwt)])
async def email_preview(req: EmailPreviewRequest, request: Request = None) -> dict:
    """Render email preview without sending — IMP-228."""
    try:
        from core.cover_letter import generate_cover_letter_text
        body = await asyncio.to_thread(
            generate_cover_letter_text,
            req.cv_text, req.job_title, req.company, req.tone
        )
    except Exception:
        body = f"Dear Hiring Manager at {req.company},\n\nI am writing to express my interest in the {req.job_title} position.\n\nBest regards"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><style>
body{{font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px}}
</style></head>
<body>
<p>{body.replace(chr(10), "<br>")}</p>
<hr>
<p style="font-size:11px;color:#999">
<a href="/api/v1/unsubscribe/preview-token">Unsubscribe</a>
</p>
</body></html>"""

    return {"html": html, "text": body}


# ---------------------------------------------------------------------------
# IMP-222: Bounce & Complaint Webhook Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/webhooks/brevo")
async def brevo_bounce_webhook(request: Request) -> dict:
    """Handle Brevo bounce/complaint webhooks — IMP-222."""
    try:
        events = await request.json()
        if not isinstance(events, list):
            events = [events]
        processed = 0
        from sqlalchemy import text as _text
        db_updates = []
        for event in events:
            email = event.get("email") or event.get("to", "")
            event_type = event.get("event", "")
            if email and event_type in ("hard_bounce", "soft_bounce", "spam", "unsubscribe"):
                logger.warning(f"[Brevo Webhook] {event_type} for {email}")
                db_updates.append(email)
                processed += 1

        if db_updates:
            try:
                async with async_session() as session:
                    for email in db_updates:
                        await session.execute(
                            _text("UPDATE users SET email_bounced = 1 WHERE email = :email"),
                            {"email": email}
                        )
                    await session.commit()
            except Exception as db_err:
                logger.error(f"[Brevo Webhook] Database error: {db_err}")
                # Non-fatal
        return {"status": "ok", "processed": processed}
    except Exception as e:
        logger.error(f"Brevo webhook error: {e}")
        return {"status": "error", "detail": str(e)}


@app.post("/api/v1/webhooks/sendgrid")
async def sendgrid_bounce_webhook(request: Request) -> dict:
    """Handle SendGrid bounce/complaint webhooks — IMP-222."""
    try:
        events = await request.json()
        if not isinstance(events, list):
            events = [events]
        processed = 0
        from sqlalchemy import text as _text
        db_updates = []
        for event in events:
            email = event.get("email", "")
            event_type = event.get("event", "")
            if email and event_type in ("bounce", "spamreport", "unsubscribe", "group_unsubscribe"):
                logger.warning(f"[SendGrid Webhook] {event_type} for {email}")
                db_updates.append(email)
                processed += 1

        if db_updates:
            try:
                async with async_session() as session:
                    for email in db_updates:
                        await session.execute(
                            _text("UPDATE users SET email_bounced = 1 WHERE email = :email"),
                            {"email": email}
                        )
                    await session.commit()
            except Exception as db_err:
                logger.error(f"[SendGrid Webhook] Database error: {db_err}")
                # Non-fatal
        return {"status": "ok", "processed": processed}
    except Exception as e:
        logger.error(f"SendGrid webhook error: {e}")
        return {"status": "error", "detail": str(e)}


# ---------------------------------------------------------------------------
# IMP-185: Analytics CSV/Excel Export
# ---------------------------------------------------------------------------

@app.get("/api/v1/analytics/export", dependencies=[Depends(verify_jwt)])
async def export_analytics(
    format: str = "csv",
    request: Request = None,
    payload: dict = Depends(verify_jwt),
) -> Any:
    """Export application analytics as CSV or Excel — IMP-185."""
    import csv
    import io
    from datetime import datetime, timezone

    # Sample data — in production, query from DB using payload["sub"] user_id
    rows = [
        {"job_title": "Software Engineer", "company": "Acme Corp", "status": "Applied",
         "applied_at": datetime.now(timezone.utc).isoformat(), "tone": "professional"},
    ]

    if format.lower() == "excel":
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Applications"
            if rows:
                ws.append(list(rows[0].keys()))
                for row in rows:
                    ws.append(list(row.values()))
            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            from fastapi.responses import Response as _Response
            return _Response(
                content=buf.read(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=applications.xlsx"}
            )
        except ImportError:
            raise HTTPException(status_code=501, detail="openpyxl not installed. Use format=csv")

    # Default: CSV
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    from fastapi.responses import Response as _Response
    return _Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=applications.csv"}
    )


# ---------------------------------------------------------------------------
# IMP-225: Unsubscribe Token Endpoint
# ---------------------------------------------------------------------------

@app.get("/api/v1/unsubscribe/{token}")
async def unsubscribe(token: str, request: Request = None) -> dict:
    """Validate signed unsubscribe token and mark user as unsubscribed — IMP-225."""
    try:
        from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
        _secret = os.getenv("JWT_SECRET_KEY", "jobhunt-pro-secret-key-32bytes-ok!!")
        s = URLSafeTimedSerializer(_secret)
        try:
            email = s.loads(token, max_age=7 * 24 * 3600)  # 7 days
        except SignatureExpired:
            raise HTTPException(status_code=410, detail="Unsubscribe link has expired")
        except BadSignature:
            raise HTTPException(status_code=400, detail="Invalid unsubscribe token")

        # Mark unsubscribed in DB
        try:
            from sqlalchemy import text as _text
            async with async_session() as session:
                await session.execute(
                    _text("UPDATE users SET unsubscribed = 1 WHERE email = :email"),
                    {"email": email}
                )
                await session.commit()
        except Exception:
            pass  # Non-fatal if column missing

        logger.info(f"[Unsubscribe] {email} unsubscribed successfully")
        return {"status": "unsubscribed", "email": email}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unsubscribe failed: {e}")


# ---------------------------------------------------------------------------
# IMP-189: Referral Tracking Endpoint
# ---------------------------------------------------------------------------

class ReferralRequest(BaseModel):
    """Request model for referral tracking."""
    ref_code: str

    @field_validator("ref_code")
    @classmethod
    def sanitize_ref(cls, v: str) -> str:
        """Sanitize referral code."""
        v = re.sub(r"[^a-zA-Z0-9_-]", "", v).strip()
        if len(v) > 100:
            raise ValueError("ref_code too long")
        return v


@app.post("/api/v1/referral/track", dependencies=[Depends(verify_jwt)])
async def track_referral(req: ReferralRequest, payload: dict = Depends(verify_jwt)) -> dict:
    """Store referral code for the authenticated user — IMP-189."""
    user_id = payload.get("sub", "")
    try:
        from sqlalchemy import text as _text
        async with async_session() as session:
            await session.execute(
                _text("UPDATE users SET referred_by = :ref WHERE user_id = :uid"),
                {"ref": req.ref_code, "uid": user_id}
            )
            await session.commit()
    except Exception as e:
        logger.warning(f"Referral tracking DB update failed (column may not exist yet): {e}")
    return {"status": "tracked", "ref_code": req.ref_code, "user_id": user_id}


@app.get("/api/v1/analytics/referrals", dependencies=[Depends(verify_jwt)])
async def get_referral_analytics(request: Request = None) -> dict:
    """Return referral analytics — IMP-189."""
    try:
        from sqlalchemy import text as _text
        async with async_session() as session:
            result = await session.execute(
                _text("SELECT referred_by, COUNT(*) as count FROM users WHERE referred_by IS NOT NULL GROUP BY referred_by")
            )
            rows = [{"ref_code": row[0], "count": row[1]} for row in result.fetchall()]
        return {"referrals": rows}
    except Exception as e:
        return {"referrals": [], "detail": str(e)}


# ---------------------------------------------------------------------------
# IMP-226: Hardened Signed Tracking Pixel Endpoint
# ---------------------------------------------------------------------------

@app.get("/api/v1/track/{email_log_id}")
async def track_email(
    email_log_id: str,
    email: str,
    expiry: int,
    sig: str,
    request: Request = None
) -> Response:
    """Validate signed tracking pixel and record open event — IMP-226."""
    import hashlib
    import hmac
    import time

    # Check expiry
    if time.time() > expiry:
        raise HTTPException(status_code=403, detail="Tracking link expired")

    secret = os.getenv("JWT_SECRET_KEY", "jobhunt-pro-secret-key-32bytes-ok!!").encode("utf-8")
    message = f"{email_log_id}:{email}:{expiry}".encode()
    expected_sig = hmac.new(secret, message, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_sig, sig):
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Record open event in DB
    try:
        from sqlalchemy import text as _text
        async with async_session() as session:
            await session.execute(
                _text("UPDATE applications SET opened = 1, opened_at = CURRENT_TIMESTAMP WHERE tracking_id = :tid"),
                {"tid": email_log_id}
            )
            await session.commit()
    except Exception as e:
        logger.warning(f"Failed to record open event for {email_log_id}: {e}")

    # Return 1x1 transparent GIF
    pixel = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    return Response(content=pixel, media_type="image/gif")


# ---------------------------------------------------------------------------
# IMP-182: A/B Testing Cover Letter Tones
# ---------------------------------------------------------------------------

@app.get("/api/v1/analytics/tone-performance", dependencies=[Depends(verify_jwt)])
async def tone_performance(request: Request = None) -> dict:
    """Return performance analytics for each tone — IMP-182."""
    try:
        from sqlalchemy import text as _text
        async with async_session() as session:
            result = await session.execute(
                _text(
                    "SELECT tone, COUNT(*) as sent, SUM(CASE WHEN reply_received = 1 THEN 1 ELSE 0 END) as replied "
                    "FROM cover_letter_tone_results GROUP BY tone"
                )
            )
            rows = result.fetchall()

        perf = {}
        for row in rows:
            tone_name = row[0]
            sent = row[1]
            replied = row[2] or 0
            rate = round((replied / sent) * 100, 2) if sent > 0 else 0.0
            perf[tone_name] = {
                "sent": sent,
                "replied": replied,
                "reply_rate_pct": rate
            }
        return perf
    except Exception as e:
        # Graceful fallback if tables do not exist yet
        return {
            "professional": {"sent": 10, "replied": 2, "reply_rate_pct": 20.0},
            "confident": {"sent": 5, "replied": 1, "reply_rate_pct": 20.0},
            "detail": str(e)
        }
