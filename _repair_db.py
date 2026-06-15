"""
JobHunt Pro - Database Repair Script
Fixes: missing tables, schema drift, data migration
"""
import sqlite3, os, sys
from pathlib import Path

# Ensure UTF-8 on Windows to prevent console emoji print crashes
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE = Path(r"C:\Users\samde\Desktop\cv sam new ma3 kimi")
DB_V1 = BASE / "jobhunt_saas.db"
DB_V2 = BASE / "jobhunt_saas_v2.db"

print("=" * 60)
print("  JOBHUNT PRO - DATABASE REPAIR v1")
print("=" * 60)

def ensure_dir(f):
    d = os.path.dirname(f)
    if d:
        os.makedirs(d, exist_ok=True)

def safe_conn(path):
    ensure_dir(path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=OFF")
    return conn

def get_tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

def get_columns(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}

# ── 1. Fix v2 database ──────────────────────────────────────────────
print("\n📊 Phase 1: Checking v2 database...")
conn_v2 = safe_conn(str(DB_V2))
tables_v2 = get_tables(conn_v2)
print(f"   Tables in v2: {sorted(tables_v2)}")

# Jobs table definition
JOBS_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id VARCHAR(64) UNIQUE NOT NULL,
    company VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    salary VARCHAR(100),
    url TEXT,
    source VARCHAR(50),
    snippet TEXT,
    status VARCHAR(50) DEFAULT 'new',
    match_score NUMERIC(5,2),
    response_type VARCHAR(50),
    applied_at VARCHAR(50),
    responded_at VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)"""

if "jobs" not in tables_v2:
    print("   ❌ 'jobs' table MISSING in v2 - creating...")
    conn_v2.execute(JOBS_SCHEMA)
    conn_v2.commit()
    print("   ✅ 'jobs' table created successfully!")
else:
    print("   ✅ 'jobs' table already exists")

# Copy jobs from v1 to v2
print("\n📊 Phase 2: Migrating job data from v1 to v2...")
if DB_V1.exists():
    conn_v1 = safe_conn(str(DB_V1))
    tables_v1 = get_tables(conn_v1)
    
    if "jobs" in tables_v1:
        jobs_v1 = conn_v1.execute("SELECT * FROM jobs").fetchall()
        print(f"   Found {len(jobs_v1)} jobs in v1 database")
        
        existing_ids = {r[0] for r in conn_v2.execute("SELECT job_id FROM jobs").fetchall()}
        
        imported = 0
        skipped = 0
        for j in jobs_v1:
            jid = j["job_id"]
            if jid not in existing_ids:
                conn_v2.execute("""
                    INSERT OR IGNORE INTO jobs 
                    (job_id, company, title, email, location, salary, url, source, snippet, 
                     status, match_score, response_type, applied_at, responded_at, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,COALESCE(?,CURRENT_TIMESTAMP),COALESCE(?,CURRENT_TIMESTAMP))
                """, (
                    jid, j["company"], j["title"], j["email"],
                    j["location"], j["salary"], j["url"], j["source"],
                    j["snippet"], j["status"], j["match_score"],
                    j["response_type"], j["applied_at"], j["responded_at"],
                    j["created_at"], j["updated_at"]
                ))
                imported += 1
            else:
                skipped += 1
        
        conn_v2.commit()
        print(f"   ✅ Imported: {imported} new jobs, {skipped} already existed")
        
        # Also migrate applications if table exists
        if "applications" in tables_v1 and "applications" not in tables_v2:
            print("\n📊 Phase 2b: Migrating applications table...")
            apps_v1 = conn_v1.execute("SELECT * FROM applications").fetchall()
            print(f"   Found {len(apps_v1)} applications in v1")
            
            APPL_SCHEMA = """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id VARCHAR(64) NOT NULL,
                company VARCHAR(255) NOT NULL,
                title VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                cover_letter TEXT,
                cv_path TEXT,
                provider VARCHAR(50),
                tracking_id VARCHAR(32),
                status VARCHAR(50) DEFAULT 'applied',
                followup_count INTEGER DEFAULT 0,
                opened BOOLEAN DEFAULT 0,
                clicked BOOLEAN DEFAULT 0,
                responded BOOLEAN DEFAULT 0,
                response_type VARCHAR(50),
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                opened_at DATETIME,
                responded_at DATETIME
            )"""
            conn_v2.execute(APPL_SCHEMA)
            conn_v2.commit()
            imported_apps = 0
            for a in apps_v1:
                conn_v2.execute("""
                    INSERT OR IGNORE INTO applications 
                    (job_id, company, title, email, cover_letter, cv_path, provider,
                     tracking_id, status, followup_count, opened, clicked, responded,
                     response_type, sent_at, opened_at, responded_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    a["job_id"], a["company"], a["title"], a["email"],
                    a["cover_letter"], a["cv_path"], a["provider"],
                    a["tracking_id"], a["status"], a["followup_count"],
                    a["opened"], a["clicked"], a["responded"],
                    a["response_type"], a["sent_at"], a["opened_at"], a["responded_at"]
                ))
                imported_apps += 1
            conn_v2.commit()
            print(f"   ✅ Imported {imported_apps} applications to v2")
        
        conn_v1.close()
    else:
        print("   No 'jobs' table in v1 database")
else:
    print("   v1 database not found at", DB_V1)

# ── 3. Verify ──────────────────────────────────────────────────────
print("\n📊 Phase 3: Verification...")
tables_v2_final = get_tables(conn_v2)
job_count = conn_v2.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
print(f"   Tables in v2: {sorted(tables_v2_final)}")
print(f"   Jobs in v2: {job_count}")
print(f"   'jobs' table exists: {'jobs' in tables_v2_final}")

# Show job status breakdown
statuses = conn_v2.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status").fetchall()
for s in statuses:
    print(f"     - {s['status']}: {s['COUNT(*)']}")

conn_v2.close()
print("\n✅ Database repair complete!")
print("=" * 60)
