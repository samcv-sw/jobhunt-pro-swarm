"""
Force-create a campaign for Rita Cordahi on PA.
"""
import sqlite3, uuid, os
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

def force_rita_campaign():
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    
    # First check Rita's user_id
    rita = conn.execute(
        "SELECT * FROM users WHERE email = 'ritacordahi2@gmail.com'"
    ).fetchone()
    
    if not rita:
        # Find in cv_profiles
        rita_profile = conn.execute(
            "SELECT * FROM cv_profiles WHERE email = 'ritacordahi2@gmail.com'"
        ).fetchone()
        if rita_profile:
            rita = dict(rita_profile)
            rita["user_id"] = rita_profile["user_id"]
        else:
            conn.close()
            return {"error": "Rita not found in users or profiles"}
    
    rita = dict(rita) if not isinstance(rita, dict) else rita
    rita_uid = rita.get("user_id")
    
    # Check profile
    profile = conn.execute(
        "SELECT * FROM cv_profiles WHERE user_id = ?", (rita_uid,)
    ).fetchone()
    profile_id = profile["id"] if profile else None
    
    # Check existing campaigns
    existing = conn.execute(
        "SELECT * FROM campaigns WHERE user_id = ?", (rita_uid,)
    ).fetchall()
    
    if existing:
        # Reset existing to pending
        conn.execute(
            "UPDATE campaigns SET status='pending' WHERE user_id=? AND status='completed'",
            (rita_uid,)
        )
        conn.commit()
        reset_count = len([c for c in existing if c["status"] == "completed"])
        conn.close()
        return {"status": "ok", "message": f"Reset {reset_count} campaigns to pending", "user_id": rita_uid}
    
    # Create new campaign
    campaign_id = f"rita_camp_{uuid.uuid4().hex[:8]}"
    
    # Check campaigns table schema
    try:
        conn.execute("""
            INSERT INTO campaigns (campaign_id, user_id, order_id, profile_id, 
            status, total_companies, sent_count, created_at, bouquets, engine_type)
            VALUES (?, ?, ?, ?, 'pending', 100, 0, CURRENT_TIMESTAMP, 'HR Priority Shield', 'cloud-tick')
        """, (campaign_id, rita_uid, f"rita_order_{uuid.uuid4().hex[:6]}", profile_id))
        conn.commit()
        conn.close()
        return {"status": "ok", "campaign_id": campaign_id, "user_id": rita_uid, "profile_id": profile_id}
    except Exception as e:
        conn.close()
        return {"error": str(e)}

if __name__ == "__main__":
    result = force_rita_campaign()
    print(result)
