


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

# ─── AUTOMATED DISK QUOTA SELF-CLEANER ─────────────────────────────────────────
_bloat_files = [
    '/home/JHFGUF/jobhunt/JobHunt_Pro_Full_Chat_Log.html',
    '/home/JHFGUF/jobhunt/JobHunt_Pro_Full_Chat_Log.md',
    '/home/JHFGUF/jobhunt/JobHunt_Pro_Full_Chat_Log.txt',
    '/home/JHFGUF/jobhunt/deploy_bundle.zip',
    '/home/JHFGUF/jobhunt/data/audit_security.db',
    '/home/JHFGUF/jobhunt/data/master_analytics.db',
    '/home/JHFGUF/jobhunt/data/enterprise_b2b.db',
    '/home/JHFGUF/jobhunt/data/saas_metrics.db',
    '/home/JHFGUF/jobhunt/data/test_db.db',
    '/home/JHFGUF/jobhunt/data/gcc_b2b_swarms.db',
    '/home/JHFGUF/jobhunt/data/jobhunt_saas.db',
    '/home/JHFGUF/jobhunt/web/git_pull_log.txt',
    '/home/JHFGUF/jobhunt/web/db_unlock_log.txt',
]
for _bf in _bloat_files:
    if os.path.exists(_bf):
        try: os.remove(_bf)
        except Exception: pass

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
                    
                    try:
                        self.wsgi_app = ASGIMiddleware(app, send_queue_size=20)
                    except TypeError:
                        self.wsgi_app = ASGIMiddleware(app)
                        
                    logger.info("[WSGI] ASGIMiddleware initialized successfully in worker.")

                    # Start continuous background job applier thread on PythonAnywhere
                    def _start_cloud_background_applier():
                        import time
                        import sqlite3
                        import asyncio
                        # Wait 30s after WSGI start so web app responds instantly to user requests without slow_startup_error
                        time.sleep(30)
                        logger.info("[PA WORKER] 🚀 Continuous Background Applier Daemon Started.")
                        while True:
                            try:
                                from web.app_v2 import get_db
                                from core.job_queue import dequeue_task, complete_task
                                from core.campaign_runner import run_campaign

                                task = dequeue_task()
                                if task:
                                    t_type = task.get("task_type")
                                    payload = task.get("payload", {})
                                    if t_type == "run_campaign":
                                        camp_id = payload.get("campaign_id")
                                        if camp_id:
                                            loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(loop)
                                            try:
                                                loop.run_until_complete(run_campaign(camp_id, get_db, None, company_limit=15))
                                            except Exception as camp_err:
                                                logger.error(f"[PA WORKER] Campaign {camp_id} error: {camp_err}")
                                            finally:
                                                loop.close()
                                    complete_task(task["id"], result={"status": "success"})
                                    time.sleep(5)
                                else:
                                    # Fallback: Pick active, running, or pending campaigns from SQLite DB automatically
                                    with get_db() as conn:
                                        active_camps = conn.execute(
                                            "SELECT campaign_id FROM campaigns WHERE status IN ('active', 'running', 'pending') ORDER BY created_at DESC LIMIT 3"
                                        ).fetchall()
                                        for row in active_camps:
                                            c_id = row["campaign_id"] if isinstance(row, (dict, sqlite3.Row)) or hasattr(row, "keys") else row[0]
                                            loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(loop)
                                            try:
                                                loop.run_until_complete(run_campaign(c_id, get_db, None, company_limit=5))
                                            except Exception as camp_err:
                                                logger.error(f"[PA WORKER] Fallback campaign {c_id} error: {camp_err}")
                                            finally:
                                                loop.close()
                                    time.sleep(15)
                            except Exception as e:
                                logger.error(f"[PA WORKER] Applier daemon exception: {e}")
                                time.sleep(30)

                    applier_thread = threading.Thread(target=_start_cloud_background_applier, daemon=True, name="PA_Background_Applier")
                    applier_thread.start()

        return self.wsgi_app(environ, start_response)

application = LazyASGIApp()
