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

from core.security_shield import SecurityShieldMiddleware

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
from backend.routers.waf_honeypot import router as waf_honeypot_router
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

# Add SecurityShieldMiddleware for WAF, Honeypot & Rate Limiting protection
app.add_middleware(SecurityShieldMiddleware)

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

from backend.routers.singularity_suite import router as singularity_suite_router
app.include_router(singularity_suite_router)

from backend.routers.closed_loop_router import router as closed_loop_router
app.include_router(closed_loop_router)


from backend.routers.voice_interview import router as voice_interview_router
from backend.routers.chrome_auto_apply import router as chrome_auto_apply_router
from backend.routers.video_resume_generator import router as video_resume_generator_router
from backend.routers.white_label_portal import router as white_label_portal_router
from backend.routers.predictive_market import router as predictive_market_router
from backend.routers.b2b_recruiter_swarm import router as b2b_recruiter_swarm_router
from backend.routers.live_video_interviewer import router as live_video_interviewer_router
from backend.routers.vision_auto_apply import router as vision_auto_apply_router
from backend.routers.self_healing_engine import router as self_healing_engine_router

# Phase 7: Ultimate Autonomous Scaling Suite
from backend.routers.lead_swarm import router as lead_swarm_router
from backend.routers.self_healing_api import router as self_healing_api_router
from backend.routers.autonomous_billing import router as autonomous_billing_router
from backend.routers.ab_testing_engine import router as ab_testing_engine_router
from backend.routers.edge_mesh_api import router as edge_mesh_api_router
from backend.routers.ai_mock_interview import router as ai_mock_interview_router

app.include_router(voice_interview_router)
app.include_router(chrome_auto_apply_router)
app.include_router(video_resume_generator_router)
app.include_router(white_label_portal_router)
app.include_router(predictive_market_router)
app.include_router(b2b_recruiter_swarm_router)
app.include_router(live_video_interviewer_router)
app.include_router(vision_auto_apply_router)
app.include_router(self_healing_engine_router)
app.include_router(ai_mock_interview_router)

# Phase 7 Registrations
app.include_router(lead_swarm_router)
app.include_router(self_healing_api_router)
app.include_router(autonomous_billing_router)
app.include_router(ab_testing_engine_router)
app.include_router(edge_mesh_api_router)


from backend.routers.crm_pipeline import router as crm_pipeline_router
app.include_router(crm_pipeline_router)

# God-Mode Next-Gen Upgrades
from backend.routers.self_marketing_swarm import router as self_marketing_swarm_router
from backend.routers.ats_reverse_engine import router as ats_reverse_engine_router
from backend.routers.live_interview_coach import router as live_interview_coach_router
from backend.routers.self_healing_telemetry import router as self_healing_telemetry_router
from backend.routers.multi_tenant_portal import router as multi_tenant_portal_router

app.include_router(self_marketing_swarm_router)
app.include_router(ats_reverse_engine_router)
app.include_router(live_interview_coach_router)
app.include_router(self_healing_telemetry_router)
app.include_router(multi_tenant_portal_router)

# Phase 7 Empire Upgrades
from backend.routers.ai_sdr_outreach import router as ai_sdr_outreach_router
from backend.routers.ats_resume_sculptor import router as ats_resume_sculptor_router
from backend.routers.interview_copilot import router as interview_copilot_router
from backend.routers.scraping_swarm import router as scraping_swarm_router
from backend.routers.salary_negotiator import router as salary_negotiator_router, salary_v1_router

app.include_router(ai_sdr_outreach_router)
from backend.routers.job_radar import router as job_radar_router
app.include_router(job_radar_router)
app.include_router(ats_resume_sculptor_router)
app.include_router(interview_copilot_router)
app.include_router(scraping_swarm_router)
app.include_router(salary_negotiator_router)
app.include_router(salary_v1_router)

from web.routers.telegram_push import router as telegram_push_router
app.include_router(telegram_push_router)

# Next-Gen Quantum Suite Router
from backend.routers.quantum_god_suite import router as quantum_god_suite_router
app.include_router(quantum_god_suite_router)


from web.routers.monetization_router import router as monetization_router
app.include_router(monetization_router)

from backend.routers.next_gen_god_suite import router as next_gen_god_suite_router
app.include_router(next_gen_god_suite_router)

# Phase 8 Level 100 God-Mode Empire Upgrades
from backend.routers.voice_webrtc import router as voice_webrtc_router
from backend.routers.social_omnipresence import router as social_omnipresence_router
from backend.routers.ml_acceptance import router as ml_acceptance_router
from backend.routers.edge_routing import router as edge_routing_router
from backend.routers.pwa_push import router as pwa_push_router

app.include_router(voice_webrtc_router)
app.include_router(social_omnipresence_router)
app.include_router(ml_acceptance_router)
app.include_router(edge_routing_router)
app.include_router(pwa_push_router)

# Omni-God Master Orchestration Suite
from backend.routers.omni_god_orchestrator import router as omni_god_orchestrator_router
app.include_router(omni_god_orchestrator_router)

# Singularity Empire 4-Pillar Upgrades
from backend.routers.quantum_security_router import router as quantum_security_router
from backend.routers.viral_sdr_router import router as viral_sdr_router
from backend.routers.edge_cache_router import router as edge_cache_router_new
from backend.routers.autopoietic_router import router as autopoietic_router

app.include_router(quantum_security_router)
app.include_router(viral_sdr_router)
app.include_router(edge_cache_router_new)
app.include_router(autopoietic_router)





from backend.routers.god_tier_suite import router as god_tier_suite_router
app.include_router(god_tier_suite_router)

# Next-Gen Level 100 Upgrades
from backend.routers.webgpu_router import router as webgpu_router
from backend.routers.video_avatar_router import router as video_avatar_router
from backend.routers.swarm_mesh_router import router as swarm_mesh_router
from backend.routers.viral_growth_router import router as viral_growth_router
from backend.routers.quantum_oracle_router import router as quantum_oracle_router

app.include_router(webgpu_router)
app.include_router(video_avatar_router)
app.include_router(swarm_mesh_router)
app.include_router(viral_growth_router)
app.include_router(quantum_oracle_router)



from backend.routers.singularity_hyper_router import router as singularity_hyper_router
app.include_router(singularity_hyper_router)

# Galactic Tier Upgrades
from backend.routers.omni_outreach_router import router as omni_outreach_router
from backend.routers.voice_cloning_router import router as voice_cloning_router
from backend.routers.saas_multitenancy_router import router as saas_multitenancy_router
from backend.routers.ats_penetration_router import router as ats_penetration_router
from backend.routers.edge_autodeploy_router import router as edge_autodeploy_router

app.include_router(omni_outreach_router)
app.include_router(voice_cloning_router)
app.include_router(saas_multitenancy_router)
app.include_router(ats_penetration_router)
app.include_router(edge_autodeploy_router)

# Imperial Sovereign Tier Upgrades
from backend.routers.stealth_browser_router import router as stealth_browser_router
from backend.routers.key_vault_router import router as key_vault_router
from backend.routers.live_analytics_router import router as live_analytics_router

app.include_router(stealth_browser_router)
app.include_router(key_vault_router)
app.include_router(live_analytics_router)

# Million-Dollar Unicorn Empire Upgrades
from backend.routers.viral_flywheel_router import router as viral_flywheel_router
from backend.routers.b2b_lead_router import router as b2b_lead_router
from backend.routers.seo_monopoly_router import router as seo_monopoly_router
from backend.routers.revenue_engine_router import router as revenue_engine_router

app.include_router(viral_flywheel_router)
app.include_router(b2b_lead_router)
app.include_router(seo_monopoly_router)
app.include_router(revenue_engine_router)

# Trillion-Dollar Singularity Empire Upgrades
from backend.routers.autopoietic_swarm_router import router as autopoietic_swarm_router
from backend.routers.p2p_fabric_router import router as p2p_fabric_router
from backend.routers.omni_yield_router import router as omni_yield_router
from backend.routers.knowledge_graph_router import router as knowledge_graph_router

app.include_router(autopoietic_swarm_router)
app.include_router(p2p_fabric_router)
app.include_router(omni_yield_router)
app.include_router(knowledge_graph_router)





from backend.websocket_telemetry import telemetry_broadcaster
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await telemetry_broadcaster.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo heartbeat or client commands
    except WebSocketDisconnect:
        telemetry_broadcaster.disconnect(websocket)

# Mount Telegram Mini App static files

_tma_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "telegram_miniapp")
if os.path.isdir(_tma_dir):
    app.mount(
        "/telegram-miniapp", StaticFiles(directory=_tma_dir, html=True), name="telegram_miniapp"
    )
