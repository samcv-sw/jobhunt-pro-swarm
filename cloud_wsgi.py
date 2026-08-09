


import os
import sys
import secrets
import threading

# ─── FORCE SQLITE MODE ON PYTHONANYWHERE ──────────────────────────────────────
os.environ['FORCE_SQLITE'] = '1'

# Load .env variables unconditionally for PythonAnywhere environment
_env_paths = [
    '/home/JHFGUF/jobhunt/.env',
    '/home/jhfguf/jobhunt/.env',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),
]
for _env_path in _env_paths:
    if os.path.exists(_env_path):
        try:
            with open(_env_path, encoding='utf-8') as _ef:
                for _line in _ef:
                    _line = _line.strip()
                    if _line and not _line.startswith('#') and '=' in _line:
                        _k, _, _v = _line.partition('=')
                        _k_str = _k.strip()
                        _v_str = _v.strip().strip('"').strip("'")
                        os.environ[_k_str] = _v_str
            break
        except Exception:
            pass

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

# ─── PURE PYTHON WSGI ENGINE ─────────────────────────────────────────

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

                    # Start continuous background job applier thread on PythonAnywhere
                    def _start_cloud_background_applier():
                        import time
                        logger.info("[PA WORKER] 🚀 Continuous Background Applier Daemon Started.")
                        while True:
                            try:
                                from web.app_v2 import get_db
                                from core.job_queue import dequeue_task, complete_task
                                from core.campaign_runner import run_campaign
                                import asyncio

                                task = dequeue_task()
                                if task:
                                    t_type = task.get("task_type")
                                    payload = task.get("payload", {})
                                    if t_type == "run_campaign":
                                        camp_id = payload.get("campaign_id")
                                        if camp_id:
                                            loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(loop)
                                            loop.run_until_complete(run_campaign(camp_id, get_db, None, company_limit=15))
                                            loop.close()
                                    complete_task(task["id"], {"status": "success"})
                                else:
                                    with get_db() as conn:
                                        active_camps = conn.execute("SELECT campaign_id FROM campaigns WHERE status IN ('active', 'running') ORDER BY created_at DESC LIMIT 1").fetchall()
                                        for (c_id,) in active_camps:
                                            loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(loop)
                                            loop.run_until_complete(run_campaign(c_id, get_db, None, company_limit=3))
                                            loop.close()
                            except Exception as e:
                                logger.error(f"[PA WORKER] Applier daemon exception: {e}")

                            time.sleep(30)

                    applier_thread = threading.Thread(target=_start_cloud_background_applier, daemon=True, name="PA_Background_Applier")
                    applier_thread.start()

        return self.wsgi_app(environ, start_response)

application = LazyASGIApp()
