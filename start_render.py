"""
JobHunt Pro - Cloud Startup
Supports Render, Koyeb, Railway. Auto-detects PostgreSQL or SQLite.
"""
import os, sys, logging, time
from pathlib import Path

ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

for d in ["data", "logs", "sent_mails", "cache"]:
    (ROOT_DIR / d).mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("cloud")

PORT = int(os.getenv("PORT", "8000"))

# --- Database: Auto-detect PostgreSQL or fallback to SQLite ---
# Priority: POSTGRES_URL > DATABASE_URL (postgres) > SQLite fallback
pg_url = os.getenv("POSTGRES_URL", "") or os.getenv("DATABASE_URL", "")
is_postgres = pg_url.startswith("postgresql") or pg_url.startswith("postgres")

if is_postgres:
    os.environ["DATABASE_URL"] = pg_url
    sync_url = pg_url.replace("+asyncpg://", "://").replace("postgresql+asyncpg://", "postgresql://")
    os.environ["DATABASE_URL_SYNC"] = sync_url
    log.info(f"PostgreSQL mode: {pg_url[:50]}...")
else:
    db_path = str(ROOT_DIR / "data" / "jobhunt_saas_v2.db")
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path}")
    os.environ.setdefault("DATABASE_URL_SYNC", f"sqlite:///{db_path}")
    log.info(f"SQLite mode: {db_path}")

# --- Common env vars ---
os.environ.setdefault("DB_PATH", str(ROOT_DIR / "data" / "sam_max.db"))
os.environ.setdefault("CLOUD_MODE", "true")
os.environ.setdefault("DRY_RUN", "true")
os.environ.setdefault("MAX_WORKERS", "50")
os.environ.setdefault("CV_PATH", "assets/Sam_Salameh_CV.pdf")

log.info(f"PORT={PORT}  DRY_RUN={os.getenv('DRY_RUN')}")

# Import and start
t0 = time.time()
from web.app_v2 import app
log.info(f"App imported in {time.time()-t0:.1f}s")

if __name__ == "__main__":
    import uvicorn
    log.info(f"Starting Multi-Core Server on 0.0.0.0:{PORT} with 4 workers")
    uvicorn.run("web.app_v2:app", host="0.0.0.0", port=PORT, log_level="info", access_log=True, workers=4)
