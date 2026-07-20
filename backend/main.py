import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import (
    FastAPI,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from backend.ai_engine import generate_smart_cover_letter_stream  # noqa: F401
from backend.routers.accounts import router as accounts_router
from backend.routers.admin import dlq_requeue  # noqa: F401
from backend.routers.admin import router as admin_router
from backend.routers.agent_swarm import router as agent_swarm_router
from backend.routers.analytics import router as analytics_router
from backend.routers.auto_applier import router as auto_applier_router
from backend.routers.cover_letters import router as cover_letters_router
from backend.routers.edge_cache import router as edge_cache_router
from backend.routers.emails import router as emails_router
from backend.routers.enterprise_portal import router as enterprise_portal_router
from backend.routers.health import health_detailed  # noqa: F401
from backend.routers.health import router as health_router
from backend.routers.hr_outreach import router as hr_outreach_router
from backend.routers.interview_simulator import router as interview_simulator_router
from backend.routers.linkedin_auth import router as linkedin_auth_router
from backend.routers.microsite_generator import router as microsite_generator_router
from backend.routers.onboarding import router as onboarding_router
from backend.routers.portfolio_evaluator import router as portfolio_evaluator_router
from backend.routers.referral import router as referral_router
from backend.routers.salary_negotiator import router as salary_negotiator_router
from backend.routers.scraping import router as scraping_router
from backend.routers.scraping import trigger_scrape  # noqa: F401
from backend.routers.self_healing_agent import router as self_healing_agent_router
from backend.routers.stealth_scraper import router as stealth_scraper_router
from backend.routers.telegram import router as telegram_router
from backend.routers.telegram_app import router as telegram_app_router
from backend.routers.unsubscribe import router as unsubscribe_router
from backend.routers.video_avatar import router as video_avatar_router
from backend.routers.vision_form_filler import router as vision_form_filler_router
from backend.routers.webhooks import (  # noqa: F401
    brevo_bounce_webhook,
    sendgrid_bounce_webhook,
)
from backend.routers.webhooks import router as webhooks_router
from backend.routers.websocket import router as websocket_router
from backend.routers.whatsapp_sync import router as whatsapp_sync_router
from backend.schemas import (  # noqa: F401
    AccountCreateRequest,
    CoverLetterRequest,
    ReferralRequest,
    ScrapeRequest,
)

from .auth import verify_jwt  # noqa: F401
from . import config
from .billing import router as billing_router
from .database import async_session  # noqa: F401
from .limiter import rate_limiter  # noqa: F401

# Sentry error tracking (free tier, optional)
_sentry_dsn = config.SENTRY_DSN
if _sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.1,
            environment=config.ENV,
        )
        logging.getLogger(__name__).info("Sentry error tracking initialized.")
    except ImportError:
        logging.getLogger(__name__).warning("sentry-sdk not installed; skipping Sentry init.")

# Configure logger for Enterprise API
_handlers = [logging.StreamHandler()]
_token = config.LOGTAIL_SOURCE_TOKEN
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
                        "User-Agent": "LogtailLogger/1.0",
                    }
                    req = urllib.request.Request(
                        "https://in.logs.betterstack.com",
                        data=_json.dumps(payload).encode("utf-8"),
                        headers=headers,
                        method="POST",
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

# Dynamically scale workers to handle concurrent task queuing operations
is_pa = bool(config.IS_PYTHONANYWHERE)
max_workers = 4 if is_pa else 32
celery_dispatch_executor = ThreadPoolExecutor(
    max_workers=max_workers, thread_name_prefix="celery_dispatch"
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
    # Use SQLAlchemy's create_engine with the DATABASE_URL from config
    engine = create_engine(config.DATABASE_URL, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")

    # Initialize Telegram Bot in Webhook mode
    try:
        from core.telegram_bot import TelegramBot

        bot_instance = TelegramBot()
        app.state.bot_instance = bot_instance
        if bot_instance.enabled:
            logger.info("Initializing Telegram bot in Webhook mode...")
            bot_instance.notifier.start()

            from . import config

            site_url = getattr(config, "SITE_URL", "https://jhfguf.pythonanywhere.com").rstrip("/")
            render_url = config.RENDER_URL
            base_url = (render_url or site_url).rstrip("/")
            webhook_url = f"{base_url}/webhook/telegram"

            logger.info(f"Setting Telegram webhook to: {webhook_url}")
            import httpx

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"https://api.telegram.org/bot{bot_instance.token}/setWebhook",
                    json={"url": webhook_url},
                )
                if res.status_code == 200:
                    logger.info("Telegram webhook registered successfully.")
                else:
                    logger.warning(
                        f"Failed to set Telegram webhook: {res.status_code} - {res.text}"
                    )
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
    default_response_class=ORJSONResponse,
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
    if not re.match(r"^https?://\*\.(?:localhost|[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+)$", pattern):
        raise ValueError(
            f"Unsupported wildcard origin pattern '{pattern}'. "
            "Wildcards are only allowed at the subdomain level, e.g. "
            "'https://*.example.com'."
        )

    # Escape the literal portion then replace the escaped wildcard placeholder.
    # re.escape("*") == r'\*' on Python 3.7+
    escaped = re.escape(pattern).replace(re.escape("*"), "[a-zA-Z0-9-]+")
    return re.compile(f"^{escaped}$")


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
allowed_origins_env = config.ALLOWED_ORIGINS_ENV
if allowed_origins_env:
    origins = config.ALLOWED_ORIGINS
else:
    # Safe defaults for local development
    origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]

# Add GZip Middleware for massive payload compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Use SecureCORSMiddleware whenever there are explicit allowed origins;
# fall back to permissive CORSMiddleware only for fully local dev with no env config.
_has_wildcard_pattern = any("*" in o for o in origins)
if config.ENV == "production" or allowed_origins_env or _has_wildcard_pattern:
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
        "default-src 'none'; "
        "script-src 'self'; "
        "style-src 'self' fonts.googleapis.com; "
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
    if request.url.scheme == "https" or config.ENV == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )

    return response


app.include_router(billing_router)
app.include_router(accounts_router)
app.include_router(analytics_router)
app.include_router(admin_router)
app.include_router(cover_letters_router)
app.include_router(emails_router)
app.include_router(health_router)
app.include_router(referral_router)
app.include_router(scraping_router)
app.include_router(telegram_router)
app.include_router(linkedin_auth_router)
app.include_router(onboarding_router)
app.include_router(unsubscribe_router)
app.include_router(webhooks_router)
app.include_router(websocket_router)
app.include_router(telegram_app_router)
app.include_router(auto_applier_router)
app.include_router(interview_simulator_router)
app.include_router(hr_outreach_router)
app.include_router(salary_negotiator_router)
app.include_router(whatsapp_sync_router)
app.include_router(enterprise_portal_router)
app.include_router(stealth_scraper_router)
app.include_router(portfolio_evaluator_router)
app.include_router(video_avatar_router)
app.include_router(self_healing_agent_router)
app.include_router(agent_swarm_router)
app.include_router(vision_form_filler_router)
app.include_router(microsite_generator_router)
app.include_router(edge_cache_router)

# Mount Telegram Mini App static files
_tma_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "telegram_miniapp")
if os.path.isdir(_tma_dir):
    app.mount(
        "/telegram-miniapp", StaticFiles(directory=_tma_dir, html=True), name="telegram_miniapp"
    )
