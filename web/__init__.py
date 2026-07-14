"""
web/__init__.py - Application Factory
Extracted from app_v2.py (Phase 1 Refactor)
"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

import config

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    from web.shared import static_dir
    app = FastAPI(
        title="JobHunt Pro - Maximum Power",
        version=getattr(config, "VERSION", "1.0"),
        docs_url=None, redoc_url=None, openapi_url=None
    )

    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="jhfguf.pythonanywhere.com")

    try:
        from core.aegis_shield import AegisShieldMiddleware
        app.add_middleware(AegisShieldMiddleware)
        from core.localization import LanguageMiddleware
        app.add_middleware(LanguageMiddleware)
    except Exception as e:
        logger.error(f"Failed to load Aegis/Lang: {e}")

    try:
        from core.iron_cloak import IronCloakMiddleware
        app.add_middleware(IronCloakMiddleware)
    except Exception as e:
        logger.error(f"Failed to load IronCloak: {e}")

    try:
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    except Exception as e:
        logger.warning(f"Static mount failed: {e}")

    # Register Routers
    routers = [
        ("web.routers.auth", "router"),
        ("web.routers.dashboard", "router"),
        ("web.routers.public", "router"),
        ("web.routers.admin", "router"),
        ("web.routers.payments", "router"),
        ("web.routers.jobs", "router"),
        ("web.routers.employers", "router"),
        ("web.routers.campaigns", "router"),
        ("web.routers.system", "router"),
    ]

    import importlib
    for module_path, router_attr in routers:
        try:
            mod = importlib.import_module(module_path)
            r = getattr(mod, router_attr)
            app.include_router(r)
            logger.info(f"Registered {module_path}")
        except Exception as e:
            logger.error(f"Failed to register {module_path}: {e}")

    return app
