


import os
import sys
import secrets
import threading

# ─── FORCE SQLITE MODE ON PYTHONANYWHERE ──────────────────────────────────────
os.environ['FORCE_SQLITE'] = '1'

_JWT_KEY = os.environ.get('JWT_SECRET_KEY', '')
if not _JWT_KEY:
    _env_path = '/home/JHFGUF/jobhunt/.env'
    try:
        with open(_env_path) as _ef:
            for _line in _ef:
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _k, _, _v = _line.partition('=')
                    os.environ.setdefault(_k.strip(), _v.strip())
    except Exception:
        pass

# Force SQLite mode
os.environ['FORCE_SQLITE'] = '1'

if not os.environ.get('JWT_SECRET_KEY'):
    os.environ['JWT_SECRET_KEY'] = secrets.token_urlsafe(48)
if not os.environ.get('SECRET_KEY'):
    os.environ['SECRET_KEY'] = secrets.token_urlsafe(64)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [wsgi_pa] %(message)s')
logger = logging.getLogger('wsgi_pa')

PROJECT = '/home/JHFGUF/jobhunt'
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

# Run automatic git pull on reload/startup (Commented out to prevent slow startup error in normal operations)
# try:
#     import subprocess
#     import os
#     lock_file = "/home/JHFGUF/jobhunt/.git/index.lock"
#     if os.path.exists(lock_file):
#         os.remove(lock_file)
#     subprocess.run(["git", "fetch", "--all"], cwd=PROJECT, capture_output=True, timeout=60)
#     res = subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=PROJECT, capture_output=True, text=True, timeout=60)
#     with open("/home/JHFGUF/jobhunt/web/git_pull_log.txt", "w", encoding="utf-8") as f:
#         f.write(f"Return code: {res.returncode}\n")
#         f.write(f"Stdout:\n{res.stdout}\n")
#         f.write(f"Stderr:\n{res.stderr}\n")
# except Exception as e:
#     with open("/home/JHFGUF/jobhunt/web/git_pull_log.txt", "w", encoding="utf-8") as f:
#         f.write(f"Exception: {str(e)}\n")

# ─── PURE PYTHON LAZY WSGI APP LOADER ─────────────────────────────────────────
# This ensures ASGIMiddleware background event loop threads are created inside the
# worker process post-fork, avoiding thread loss deadlocks on PythonAnywhere.
class LazyASGIApp:
    def __init__(self):
        self.wsgi_app = None
        self._lock = threading.Lock()

    def __call__(self, environ, start_response):
        if self.wsgi_app is None:
            with self._lock:
                if self.wsgi_app is None:
                    logger.info(f"[WSGI] First request received in PID {os.getpid()}. Lazily loading app_v2 and ASGIMiddleware...")
                    
                    from web.app_v2 import app
                    from a2wsgi import ASGIMiddleware
                    
                    # Register custom error logging middleware
                    @app.middleware("http")
                    async def log_errors_middleware(request, call_next):
                        try:
                            return await call_next(request)
                        except Exception as e:
                            import traceback
                            with open('/home/JHFGUF/jobhunt/web/db_unlock_log.txt', 'a') as f:
                                f.write(f"MIDDLEWARE ERROR on {request.url.path}: {e}\n{traceback.format_exc()}\n")
                            raise
                    
                    try:
                        self.wsgi_app = ASGIMiddleware(app, send_queue_size=20)
                    except TypeError:
                        self.wsgi_app = ASGIMiddleware(app)
                        
                    logger.info("[WSGI] ASGIMiddleware initialized successfully in worker.")
        return self.wsgi_app(environ, start_response)

application = LazyASGIApp()
