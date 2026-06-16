#!/usr/bin/env python3
"""Render boot v3: gunicorn with preload. App loads first, then port opens."""
import os, sys

PORT = int(os.environ.get("PORT", 10000))

# The health server is started by core.swarm_master on HEALTH_PORT (9999)
# We only run gunicorn here - swarm_master runs in background via Dockerfile

# Start gunicorn with preload - app loads before port opens
from gunicorn.app.base import BaseApplication

class App(BaseApplication):
    def __init__(self, app_uri, opts=None):
        self.app_uri = app_uri
        self.opts = opts or {}
        super().__init__()
    def load_config(self):
        for k, v in self.opts.items():
            kl = k.lower().replace("_", "")
            for sk in self.cfg.settings:
                if sk.replace("_", "") == kl:
                    self.cfg.set(sk, v)
                    break
    def load(self):
        # With preload, this runs in master BEFORE binding port
        print("[BOOT] Loading app...", flush=True)
        from web.app_v2 import app
        print(f"[BOOT] App loaded: {len(app.routes)} routes", flush=True)
        return app

opts = {
    "BIND": f"0.0.0.0:{PORT}",
    "WORKER_CLASS": "uvicorn.workers.UvicornWorker",
    "WORKERS": 1,
    "TIMEOUT": 300,
    "GRACEFUL_TIMEOUT": 60,
    "KEEPALIVE": 5,
    "ACCESSLOG": "-",
    "ERRORLOG": "-",
    "CAPTUREOUTPUT": True,
    "LOGLEVEL": "info",
    "PRELOAD": True,  # Key: load app before binding port
}

print(f"[BOOT] Starting gunicorn (preload) on port {PORT}...", flush=True)
App("web.app_v2:app", opts).run()
