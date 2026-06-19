"""
JobHunt Pro — Frontend-facing API Routes
Registered by app_v2.py import. Serves the Cloudflare Pages frontend.
Uses ONLY columns that exist on PA's DB schema.
"""
import json
import hashlib
import hmac
import logging
import os
import re
import sqlite3 as sqlite3_module
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

try:
    from core.byo_smtp import encrypt_credentials, decrypt_credentials, test_smtp_connection
except ImportError:
    def encrypt_credentials(e, p): return None
    def decrypt_credentials(t): return None
    def test_smtp_connection(e, p, prov="gmail"): return (False, "BYOSMTP not loaded")

logger = logging.getLogger(__name__)

router = APIRouter()

def init_frontend_tables():
    """Ensure extra tables exist (smtp_configs + user_prefs)."""
    conn = get_db()
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS smtp_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            email TEXT NOT NULL,
            encrypted_token TEXT NOT NULL,
            provider TEXT DEFAULT 'gmail',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS user_prefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            target_roles TEXT DEFAULT '',
            target_locations TEXT DEFAULT '',
            min_salary REAL DEFAULT 1500,
            cv_text TEXT DEFAULT '',
            target_companies TEXT DEFAULT '',
            profile_source TEXT DEFAULT 'frontend',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
    except Exception as e:
        logger.warning(f"[FRONTEND] Init tables: {e}")
    finally:
        conn.close()

_tables_initialized = False

def get_db():
    """Get database connection matching app_v2.py."""
    from pathlib import Path
    BASE_DIR = Path(__file__).parent
    db_path = str(BASE_DIR.parent / "jobhunt_saas_v2.db")
    conn = sqlite3_module.connect(db_path)
    conn.row_factory = sqlite3_module.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def ensure_tables():
    """Ensure tables exist. Called lazily on first route hit."""
    global _tables_initialized
    if _tables_initialized:
        return True
    try:
        conn = get_db()
        conn.execute('''CREATE TABLE IF NOT EXISTS smtp_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            email TEXT NOT NULL,
            encrypted_token TEXT NOT NULL,
            provider TEXT DEFAULT 'gmail',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS user_prefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            target_roles TEXT DEFAULT '',
            target_locations TEXT DEFAULT '',
            min_salary REAL DEFAULT 1500,
            cv_text TEXT DEFAULT '',
            target_companies TEXT DEFAULT '',
            profile_source TEXT DEFAULT 'frontend',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
        conn.close()
        _tables_initialized = True
        return True
    except Exception as e:
        logger.warning(f"[FRONTEND] ensure_tables failed: {e}")
        return False


# ── 1. Quick Registration ──

@router.post("/api/register-fast")
async def register_fast(request: Request):
    """Quick reg — uses only columns that exist on PA users table."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    roles = data.get("roles", [])
    locations = data.get("locations", [])
    salary = float(data.get("salary", 1500))

    if not name:
        return JSONResponse({"error": "Name is required"}, status_code=400)
    if not email or "@" not in email:
        return JSONResponse({"error": "Valid email is required"}, status_code=400)

    if isinstance(roles, list):
        roles_str = ", ".join(roles)
    else:
        roles_str = str(roles)
    if isinstance(locations, list):
        locations_str = ", ".join(locations)
    else:
        locations_str = str(locations)

    user_id = hashlib.md5(f"{email}:{datetime.now().timestamp()}".encode()).hexdigest()[:12]
    password_hash = hashlib.sha256(f"auto_{email}_{user_id}".encode()).hexdigest()

    ensure_tables()
    conn = get_db()
    try:
        existing = conn.execute("SELECT user_id, name FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return JSONResponse({
                "ok": True,
                "user_id": existing["user_id"],
                "name": existing["name"],
                "message": "Welcome back!",
                "existing": True,
            })

        # Insert user with ONLY columns that exist on PA
        conn.execute('''
            INSERT INTO users (user_id, email, password_hash, name, phone, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, datetime('now'), 1)
        ''', (user_id, email, password_hash, name, phone))
        conn.commit()

        # Save prefs to user_prefs table
        try:
            conn.execute('''
                INSERT OR REPLACE INTO user_prefs (user_id, target_roles, target_locations, min_salary, profile_source, updated_at)
                VALUES (?, ?, ?, ?, 'frontend', datetime('now'))
            ''', (user_id, roles_str, locations_str, salary))
            conn.commit()
        except Exception:
            pass  # Non-fatal

        return JSONResponse({
            "ok": True,
            "user_id": user_id,
            "name": name,
            "email": email,
            "message": "Account created! Connect your Gmail to start.",
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()


# ── 2. User Lookup ──

@router.get("/api/user/by-email")
async def user_by_email(email: str):
    """Lookup user — uses only PA columns + user_prefs."""
    if not email:
        return JSONResponse({"error": "Email required"}, status_code=400)

    ensure_tables()
    conn = get_db()
    try:
        user = conn.execute('''
            SELECT id, user_id, email, name, phone, created_at, is_active, wallet_balance
            FROM users WHERE email = ?
        ''', (email.strip().lower(),)).fetchone()

        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)

        # Load prefs
        prefs = conn.execute(
            "SELECT target_roles, target_locations, min_salary FROM user_prefs WHERE user_id = ?",
            (user["user_id"],)
        ).fetchone()

        return JSONResponse({
            "id": user["id"],
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "phone": user["phone"] or "",
            "target_roles": prefs["target_roles"] if prefs else "",
            "target_locations": prefs["target_locations"] if prefs else "",
            "min_salary": prefs["min_salary"] if prefs else 0,
            "balance": user["wallet_balance"] or 0,
            "created_at": user["created_at"],
            "is_active": bool(user["is_active"]),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()


# ── 3. User Stats ──

@router.get("/api/user/stats")
async def user_stats(user_id: str = ""):
    """Get user application stats using existing PA tables."""
    if not user_id:
        return JSONResponse({"error": "user_id required"}, status_code=400)

    conn = get_db()
    try:
        # Get sent count from campaigns
        apps_sent = conn.execute(
            "SELECT COALESCE(SUM(sent_count), 0) as c FROM campaigns WHERE user_id = ?", (user_id,)
        ).fetchone()["c"]

        # Also check job_applications
        try:
            ja = conn.execute(
                "SELECT COUNT(*) as c FROM job_applications WHERE applicant_email IN (SELECT email FROM users WHERE user_id = ?)",
                (user_id,)
            ).fetchone()["c"]
            apps_sent = max(apps_sent, ja)
        except Exception:
            pass

        # Interviews via applications table
        interviews = 0
        replies = 0
        try:
            interviews = conn.execute(
                "SELECT COUNT(*) as c FROM applications WHERE email IN (SELECT email FROM users WHERE user_id = ?) AND status LIKE '%interview%'",
                (user_id,)
            ).fetchone()["c"]
            replies = conn.execute(
                "SELECT COUNT(*) as c FROM applications WHERE email IN (SELECT email FROM users WHERE user_id = ?) AND (responded_at IS NOT NULL OR status LIKE '%reply%')",
                (user_id,)
            ).fetchone()["c"]
        except Exception:
            pass

        # Campaign info
        campaign = None
        try:
            c = conn.execute(
                "SELECT id, status FROM campaigns WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
            ).fetchone()
            if c:
                campaign = {"id": c["id"], "status": c["status"]}
        except Exception:
            pass

        return JSONResponse({
            "apps_sent": apps_sent,
            "interviews": interviews,
            "replies": replies,
            "match_rate": round((interviews / max(apps_sent, 1)) * 100, 1),
            "campaign": campaign,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()


# ── 4. SMTP — Test ──

@router.post("/api/byo-smtp/test")
async def byo_smtp_test(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    if not email or not password:
        return JSONResponse({"success": False, "message": "Email and password required"})
    success, message = test_smtp_connection(email, password)
    return JSONResponse({"success": success, "message": message})


# ── 5. SMTP — Save ──

@router.post("/api/byo-smtp/save")
async def byo_smtp_save(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    user_id = data.get("user_id", "").strip()

    if not email or not password:
        return JSONResponse({"error": "Email and password required"}, status_code=400)
    if not user_id:
        return JSONResponse({"error": "user_id required"}, status_code=400)

    token = encrypt_credentials(email, password)
    if not token:
        return JSONResponse({"error": "Encryption failed."}, status_code=500)

    ensure_tables()
    conn = get_db()
    try:
        existing = conn.execute("SELECT id FROM smtp_configs WHERE user_id = ?", (user_id,)).fetchone()
        if existing:
            conn.execute("UPDATE smtp_configs SET email=?, encrypted_token=?, updated_at=datetime('now') WHERE user_id=?",
                         (email, token, user_id))
        else:
            conn.execute("INSERT INTO smtp_configs (user_id, email, encrypted_token, provider, created_at) VALUES (?, ?, ?, 'gmail', datetime('now'))",
                         (user_id, email, token))
        conn.commit()
        return JSONResponse({"ok": True, "message": "SMTP credentials saved."})
    except Exception as e:
        conn.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()


# ── 6. Global Stats ──

@router.get("/api/stats/daily")
async def stats_daily(days: int = 30):
    ensure_tables()
    conn = get_db()
    try:
        try:
            stats = conn.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as apps
                FROM job_applications
                WHERE created_at >= datetime('now', ?)
                GROUP BY DATE(created_at) ORDER BY date DESC
            ''', (f"-{days} days",)).fetchall()
        except Exception:
            stats = []
        return JSONResponse({"stats": [dict(s) for s in stats], "period_days": days})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()


# ── 7. Health ──

@router.get("/api/cloud-health")
async def cloud_health():
    conn = get_db()
    try:
        conn.execute("SELECT 1")
        return JSONResponse({
            "status": "ok", "db": "connected", "api": "v1-frontend",
            "time": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        return JSONResponse({"status": "error", "db": str(e)}, status_code=500)
    finally:
        conn.close()
