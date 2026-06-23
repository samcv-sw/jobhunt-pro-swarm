"""
Force reset ALL completed campaigns to pending for both tenants.
"""
import sqlite3, os
from pathlib import Path

def _get_db_path():
    db_path = os.getenv("DB_PATH", "jobhunt_saas_v2.db")
    base = Path(__file__).resolve().parent.parent
    full = str(base / db_path)
    if not os.path.exists(full):
        alt = str(base / "jobhunt_saas_v2.db")
        if os.path.exists(alt):
            return alt
    return full

def force_reset_all_campaigns():
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path, timeout=30)
    try:
        result = conn.execute(
            "UPDATE campaigns SET status='pending' WHERE status='completed'"
        )
        conn.commit()
        count = result.rowcount
        conn.close()
        return {"status": "ok", "reset_count": count}
    except Exception as e:
        conn.close()
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    print(force_reset_all_campaigns())
