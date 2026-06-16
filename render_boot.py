#!/usr/bin/env python3
"""Render boot: fast startup via gunicorn (faster than uvicorn for import-heavy apps)."""
import os, sys

PORT = os.environ.get("PORT", "10000")

if __name__ == "__main__":
    import multiprocessing
    workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
    
    # Use gunicorn with uvicorn workers for ASGI
    from gunicorn.app.base import BaseApplication
    
    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()
        
        def load_config(self):
            config = {k: v for k, v in self.options.items() if k.isupper()}
            for key, value in config.items():
                if key in self.cfg.settings:
                    self.cfg.set(key.lower(), value)
        
        def load(self):
            return self.application
    
    options = {
        "BIND": f"0.0.0.0:{PORT}",
        "WORKER_CLASS": "uvicorn.workers.UvicornWorker",
        "WORKERS": workers,
        "TIMEOUT": 120,
        "GRACEFUL_TIMEOUT": 30,
        "KEEP_ALIVE": 5,
        "ACCESSLOG": "-",
        "ERRORLOG": "-",
        "CAPTURE_OUTPUT": True,
        "LOG_LEVEL": "info",
    }
    
    print(f"[BOOT] Starting gunicorn on port {PORT} with {workers} workers", flush=True)
    StandaloneApplication("web.app_v2:app", options).run()
