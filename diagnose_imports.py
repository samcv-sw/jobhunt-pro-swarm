import sys
import os
import time

print("[DIAG] Starting import diagnosis...", flush=True)

_project_root = os.path.abspath(os.path.dirname(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

os.environ['FORCE_SQLITE'] = '1'
os.environ['SKIP_INSTALL'] = '1'

print("[DIAG] Step 1: Importing config...", flush=True)
import config
print("[DIAG] Step 2: Config imported cleanly. Supabase mode:", config.SUPABASE_MODE, flush=True)

print("[DIAG] Step 3: Importing core shims...", flush=True)
if config.SUPABASE_MODE:
    import core.supabase_rest_shim as sqlite3
else:
    import core.pg_sqlite_shim as sqlite3
print("[DIAG] Step 4: Shim imported cleanly.", flush=True)

print("[DIAG] Step 5: Importing services catalog & fulfillment...", flush=True)
from services.catalog import SERVICE_CATALOG
from services.fulfillment import ServiceFulfillment
print("[DIAG] Step 6: Services imported cleanly.", flush=True)

print("[DIAG] Step 7: Importing catalog auto populator...", flush=True)
from core.catalog_auto_populator import catalog_populator
print("[DIAG] Step 8: Auto populator imported cleanly.", flush=True)

print("[DIAG] Step 9: Importing dashboard router...", flush=True)
from web.routers.dashboard import router as dashboard_router
print("[DIAG] Step 10: Dashboard router imported cleanly.", flush=True)

print("[DIAG] Step 11: Importing full web.app_v2...", flush=True)
from web.app_v2 import app
print("[DIAG] SUCCESS! web.app_v2 imported completely!", flush=True)
