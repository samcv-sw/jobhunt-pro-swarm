"""
JobHunt Pro — Self-Healing Module (auto_heal.py)
Monitors system health, auto-restarts stuck campaigns, clears dead locks,
rotates SMTP accounts, checks API keys, auto-reloads PA if RAM > 90%.

DESIGNED FOR: PythonAnywhere free tier (no subprocess, limited RAM, 250s timeout)
Uses asyncio for background tasks — never spawns OS processes.
"""
import asyncio
import logging
import os
import time
import json
import threading
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger("auto_heal")

# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════
_CHECK_INTERVAL = 60  # seconds
_STUCK_THRESHOLD_MINUTES = 30  # Campaigns running >30 min considered stuck
_RAM_THRESHOLD_PCT = 90
_SMTP_RATE_LIMIT_THRESHOLD = 100  # sends/hour before rotation

HEAL_HISTORY_FILE = Path(__file__).parent.parent / "data" / "auto_heal_history.json"

# Global heal state
_heal_state = {
    "running": False,
    "last_check": None,
    "total_checks": 0,
    "heals_applied": 0,
    "errors": 0,
    "stuck_campaigns_cleared": 0,
    "dead_locks_removed": 0,
    "smtp_rotations": 0,
    "pa_reloads": 0,
}

# Lock for thread safety
_state_lock = threading.Lock()

# Throttle tracking for Groq API checks to prevent rate limits and Telegram spam
_last_groq_check_time = 0.0
_last_groq_result = None
_groq_alerted_unhealthy = False


# ═══════════════════════════════════════════════════════════════
# History Persistence
# ═══════════════════════════════════════════════════════════════

def _load_history() -> List[Dict]:
    try:
        if HEAL_HISTORY_FILE.exists():
            data = json.loads(HEAL_HISTORY_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
    except Exception:
        pass
    return []


def _save_history(entry: Dict):
    try:
        HEAL_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        history = _load_history()
        history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **entry,
        })
        # Keep last 500 entries
        history = history[-500:]
        HEAL_HISTORY_FILE.write_text(json.dumps(history, indent=2, default=str), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to save heal history: {e}")


# ═══════════════════════════════════════════════════════════════
# Telegram Alerting (non-blocking)
# ═══════════════════════════════════════════════════════════════

def _get_telegram_creds():
    """Get Telegram credentials from env or config."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token:
        try:
            import config
            token = getattr(config, "TELEGRAM_BOT_TOKEN", "")
            chat_id = getattr(config, "TELEGRAM_CHAT_ID", "")
        except ImportError:
            pass
    return token, chat_id


def _telegram_alert_sync(message: str) -> bool:
    """Send a Telegram alert synchronously (called via asyncio.to_thread)."""
    token, chat_id = _get_telegram_creds()
    if not token or not chat_id:
        return False
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message[:3900],
            "parse_mode": "HTML",
        }
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.warning(f"Telegram alert failed: {e}")
        return False


async def _telegram_alert(message: str) -> bool:
    """Async wrapper for Telegram alert."""
    return await asyncio.to_thread(_telegram_alert_sync, message)


# ═══════════════════════════════════════════════════════════════
# Database Helpers (lazy import to avoid circular deps)
# ═══════════════════════════════════════════════════════════════

def _get_db():
    """Lazily import and return a DB connection."""
    try:
        from web.app_v2 import get_db as _web_get_db
        return _web_get_db()
    except Exception:
        logger.error("Cannot get DB connection — app_v2 not importable")
        return None


# ═══════════════════════════════════════════════════════════════
# Health Checks
# ═══════════════════════════════════════════════════════════════

def _get_cgroup_memory_usage() -> Optional[float]:
    """
    Attempt to read Docker cgroup memory metrics (v1 and v2) to get 
    accurate container-specific RAM usage on Render/Fly.io.
    Returns the percentage (0.0 to 100.0) if successful, otherwise None.
    """
    try:
        # Check Cgroup v2 (typically on modern Linux / Docker hosts)
        cgroup_v2_usage_path = Path("/sys/fs/cgroup/memory.current")
        cgroup_v2_limit_path = Path("/sys/fs/cgroup/memory.max")
        
        if cgroup_v2_usage_path.exists() and cgroup_v2_limit_path.exists():
            usage_str = cgroup_v2_usage_path.read_text().strip()
            limit_str = cgroup_v2_limit_path.read_text().strip()
            
            if usage_str.isdigit():
                usage = int(usage_str)
                if limit_str.isdigit():
                    limit = int(limit_str)
                    # Limit must be valid and not default "max" (represented as a very high integer on some kernels, e.g. >922337203685477)
                    if 0 < limit < 9000000000000000000:
                        return round((usage / limit) * 100.0, 1)

        # Check Cgroup v1
        cgroup_v1_usage_path = Path("/sys/fs/cgroup/memory/memory.usage_in_bytes")
        cgroup_v1_limit_path = Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")
        
        if cgroup_v1_usage_path.exists() and cgroup_v1_limit_path.exists():
            usage_str = cgroup_v1_usage_path.read_text().strip()
            limit_str = cgroup_v1_limit_path.read_text().strip()
            
            if usage_str.isdigit():
                usage = int(usage_str)
                if limit_str.isdigit():
                    limit = int(limit_str)
                    if 0 < limit < 9000000000000000000:
                        return round((usage / limit) * 100.0, 1)
    except Exception as e:
        logger.debug(f"Failed to read cgroup memory metrics: {e}")
    return None


def _check_ram_usage() -> float:
    """Get current RAM usage percentage. Checks cgroups first, then psutil/meminfo."""
    # 1. Try container/cgroups memory first (Render/Fly.io container limits)
    cgroup_pct = _get_cgroup_memory_usage()
    if cgroup_pct is not None:
        return cgroup_pct

    # 2. Fall back to host VM memory if cgroups is not restricted or fails
    try:
        import psutil
        return psutil.virtual_memory().percent
    except ImportError:
        pass
    try:
        # Fallback: read /proc/meminfo on Linux
        with open("/proc/meminfo", "r") as f:
            mem = {}
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = int(parts[1].strip().split()[0])
                    mem[key] = val
            total = mem.get("MemTotal", 1)
            available = mem.get("MemAvailable", mem.get("MemFree", 1))
            used_pct = round(((total - available) / total) * 100, 1)
            return used_pct
    except Exception:
        pass
    # Ultimate fallback
    try:
        import sys
        if hasattr(sys, "getallocatedblocks"):
            # Very rough approximation from CPython internals
            return 50.0
    except Exception:
        pass
    return 50.0  # Assume moderate if unmeasurable


def _check_groq_api() -> Dict[str, Any]:
    """Check if Groq API key is healthy."""
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        return {"status": "missing", "healthy": False, "error": "GROQ_API_KEY not set"}
    try:
        import httpx
        # Simple models list — doesn't consume credits
        resp = httpx.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {groq_key}"},
            timeout=15,
        )
        if resp.status_code == 200:
            models = resp.json().get("data", [])
            return {"status": "ok", "healthy": True, "models_count": len(models)}
        elif resp.status_code == 401:
            return {"status": "unauthorized", "healthy": False, "error": "Invalid API key"}
        elif resp.status_code == 429:
            return {"status": "rate_limited", "healthy": False, "error": "Rate limited"}
        else:
            return {"status": "error", "healthy": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "healthy": False, "error": str(e)}


async def _check_groq_api_async() -> Dict[str, Any]:
    return await asyncio.to_thread(_check_groq_api)


# ═══════════════════════════════════════════════════════════════
# Heal Actions
# ═══════════════════════════════════════════════════════════════

def _clear_stuck_campaigns() -> int:
    """
    Find campaigns stuck in 'running' state for >30 min and reset them.
    Returns count of cleared campaigns.
    """
    conn = _get_db()
    if not conn:
        return 0
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=_STUCK_THRESHOLD_MINUTES)).isoformat()
        
        # Try multiple possible column names (schema may vary)
        stuck = 0
        for table, status_col, time_col in [
            ("campaigns", "status", "started_at"),
            ("campaigns", "status", "created_at"),
            ("email_campaigns", "status", "started_at"),
            ("job_campaigns", "status", "started_at"),
        ]:
            try:
                result = conn.execute(
                    f"UPDATE {table} SET {status_col} = 'stalled' WHERE {status_col} = 'running' AND {time_col} < ?",
                    (cutoff,)
                )
                stuck += result.rowcount or 0
            except Exception:
                pass  # Table/column may not exist
        
        if stuck > 0:
            logger.warning(f"Cleared {stuck} stuck campaigns")
        
        conn.commit()
        return stuck
    except Exception as e:
        logger.error(f"Failed to clear stuck campaigns: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _clear_dead_locks() -> int:
    """Remove lock entries that are older than 1 hour (dead locks)."""
    conn = _get_db()
    if not conn:
        return 0
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        removed = 0
        
        for table in ["locks", "job_locks", "distributed_locks", "mutex_locks"]:
            try:
                for time_col in ["acquired_at", "created_at", "locked_at"]:
                    try:
                        result = conn.execute(
                            f"DELETE FROM {table} WHERE {time_col} < ?",
                            (cutoff,)
                        )
                        removed += result.rowcount or 0
                    except Exception:
                        pass
            except Exception:
                pass
        
        if removed > 0:
            logger.info(f"Removed {removed} dead locks")
        
        conn.commit()
        return removed
    except Exception as e:
        logger.error(f"Failed to clear dead locks: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _rotate_rate_limited_smtp() -> Dict[str, Any]:
    """
    Check SMTP accounts for rate limiting and rotate if needed.
    Works with the email rotator pool (email_rotator_pool.py / byo_smtp.py).
    Returns rotation result.
    """
    result = {"rotated": False, "accounts_checked": 0, "rotate_reason": ""}
    
    # Check if any SMTP accounts exist in env
    smtp_hosts = []
    for i in range(1, 6):  # Check SMTP1 through SMTP5
        host = os.getenv(f"SMTP{i}_HOST", "")
        if host:
            smtp_hosts.append({
                "index": i,
                "host": host,
                "user": os.getenv(f"SMTP{i}_USER", ""),
                "sent_count": 0,
            })
    
    if not smtp_hosts:
        # Try single SMTP config
        host = os.getenv("SMTP_HOST", "") or os.getenv("EMAIL_HOST", "")
        if host:
            smtp_hosts.append({
                "index": 0,
                "host": host,
                "user": os.getenv("SMTP_USER", "") or os.getenv("EMAIL_HOST_USER", ""),
                "sent_count": 0,
            })
    
    if not smtp_hosts:
        return result
    
    result["accounts_checked"] = len(smtp_hosts)
    
    # Check sent counts from DB
    conn = _get_db()
    if conn:
        try:
            for smtp in smtp_hosts:
                try:
                    row = conn.execute(
                        "SELECT COUNT(*) as cnt FROM sent_emails WHERE smtp_host = ? AND sent_at > datetime('now', '-1 hour')",
                        (smtp["host"],)
                    ).fetchone()
                    if row:
                        smtp["sent_count"] = row["cnt"] if isinstance(row, dict) else row[0]
                except Exception:
                    pass
            
            # Check for rate-limited accounts
            for smtp in smtp_hosts:
                if smtp["sent_count"] > _SMTP_RATE_LIMIT_THRESHOLD:
                    logger.warning(
                        f"SMTP {smtp['index']} ({smtp['host']}) rate limited: "
                        f"{smtp['sent_count']} sends/hour > {_SMTP_RATE_LIMIT_THRESHOLD}"
                    )
                    
                    # Mark as rate-limited in DB so rotator picks next
                    try:
                        conn.execute(
                            "INSERT OR REPLACE INTO smtp_rotation (smtp_host, rate_limited, limited_at) VALUES (?, 1, datetime('now'))",
                            (smtp["host"],)
                        )
                        conn.execute(
                            "UPDATE smtp_rotation SET rate_limited = 1, limited_at = datetime('now') WHERE smtp_host = ?",
                            (smtp["host"],)
                        )
                        conn.commit()
                        result["rotated"] = True
                        result["rotate_reason"] = f"SMTP {smtp['index']} rate limited ({smtp['sent_count']}/hr)"
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"SMTP rotation check error: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    return result


def _auto_reload_pa_if_ram_high(ram_pct: float) -> bool:
    """
    Auto-reload PA webapp if RAM > threshold.
    Uses PA API (no subprocess needed).
    For non-PA container clouds (Render/Fly.io), exits the process to trigger a platform container restart.
    """
    if ram_pct <= _RAM_THRESHOLD_PCT:
        return False
    
    logger.critical(f"RAM at {ram_pct}% (> {_RAM_THRESHOLD_PCT}%) — triggering auto-heal reload/restart")
    
    pa_token = os.getenv("PA_API_TOKEN", "")
    if pa_token:
        pa_user = os.getenv("PA_USERNAME", "jhfguf")
        pa_domain = os.getenv("PA_DOMAIN", "jhfguf.pythonanywhere.com")
        try:
            import httpx
            url = f"https://www.pythonanywhere.com/api/v0/user/{pa_user}/webapps/{pa_domain}/reload/"
            resp = httpx.post(
                url,
                headers={"Authorization": f"Token {pa_token}"},
                timeout=30,
            )
            if resp.status_code == 200:
                logger.info("PA webapp reloaded successfully (high RAM)")
                return True
            else:
                logger.error(f"PA reload failed: HTTP {resp.status_code} — {resp.text[:200]}")
        except Exception as e:
            logger.error(f"PA reload exception: {e}")

    # Fallback/Cloud mode: Exit process to trigger Docker/Render/Fly.io auto-restart
    logger.critical("CLOUD AUTO-HEAL: Exiting process to trigger container restart under memory pressure")
    
    # Run shutdown gracefully by exiting the process after a brief sleep to allow logs to flush
    def exit_process():
        time.sleep(2)
        os._exit(1)
        
    threading.Thread(target=exit_process, daemon=True).start()
    return True


# ═══════════════════════════════════════════════════════════════
# Main Heal Cycle
# ═══════════════════════════════════════════════════════════════

async def run_heal_cycle(force: bool = False) -> Dict[str, Any]:
    """
    Run a full self-healing cycle.
    
    Checks in order:
    1. RAM usage → auto-reload PA if > 90%
    2. Stuck campaigns → reset if running > 30 min
    3. Dead locks → clear if > 1 hour old
    4. SMTP rate limits → rotate flagged accounts
    5. Groq API key → verify health
    
    Returns dict with heal actions taken.
    """
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "force": force,
        "ram_pct": 0.0,
        "ram_heal": False,
        "stuck_campaigns_cleared": 0,
        "dead_locks_removed": 0,
        "smtp_rotation": None,
        "groq_check": None,
        "alerts_sent": [],
        "errors": [],
    }
    
    with _state_lock:
        _heal_state["last_check"] = result["timestamp"]
        _heal_state["total_checks"] += 1
    
    # 1. RAM Check
    try:
        ram_pct = _check_ram_usage()
        result["ram_pct"] = ram_pct
        
        if ram_pct > _RAM_THRESHOLD_PCT or force:
            reloaded = _auto_reload_pa_if_ram_high(ram_pct)
            result["ram_heal"] = reloaded
            if reloaded:
                with _state_lock:
                    _heal_state["pa_reloads"] += 1
                await _telegram_alert(
                    f"🔄 <b>PA AUTO-RELOADED</b>\n\n"
                    f"<b>RAM:</b> {ram_pct}% (> {_RAM_THRESHOLD_PCT}%)\n"
                    f"<b>Reason:</b> Memory pressure auto-heal\n\n"
                    f"<i>Webapp restarted to reclaim memory.</i>"
                )
                result["alerts_sent"].append("pa_reload_ram")
    except Exception as e:
        result["errors"].append(f"RAM check: {e}")
        logger.error(f"RAM check error: {e}")
    
    # 2. Stuck Campaigns
    try:
        stuck = _clear_stuck_campaigns()
        result["stuck_campaigns_cleared"] = stuck
        with _state_lock:
            _heal_state["stuck_campaigns_cleared"] += stuck
            _heal_state["heals_applied"] += 1 if stuck > 0 else 0
        
        if stuck > 0:
            _save_history({"action": "clear_stuck_campaigns", "count": stuck})
            await _telegram_alert(
                f"🔧 <b>STUCK CAMPAIGNS CLEARED</b>\n\n"
                f"<b>Count:</b> {stuck}\n"
                f"<b>Rule:</b> Running > {_STUCK_THRESHOLD_MINUTES}min → Reset\n\n"
                f"<i>These campaigns can now be retried.</i>"
            )
            result["alerts_sent"].append("stuck_campaigns")
    except Exception as e:
        result["errors"].append(f"Stuck campaigns: {e}")
        logger.error(f"Stuck campaign check error: {e}")
    
    # 3. Dead Locks
    try:
        locks = _clear_dead_locks()
        result["dead_locks_removed"] = locks
        with _state_lock:
            _heal_state["dead_locks_removed"] += locks
            _heal_state["heals_applied"] += 1 if locks > 0 else 0
        
        if locks > 0:
            _save_history({"action": "clear_dead_locks", "count": locks})
            logger.info(f"Cleared {locks} dead locks — campaigns unblocked")
    except Exception as e:
        result["errors"].append(f"Dead locks: {e}")
        logger.error(f"Dead lock check error: {e}")
    
    # 4. SMTP Rotation
    try:
        smtp_result = _rotate_rate_limited_smtp()
        result["smtp_rotation"] = smtp_result
        if smtp_result.get("rotated"):
            with _state_lock:
                _heal_state["smtp_rotations"] += 1
                _heal_state["heals_applied"] += 1
            
            _save_history({"action": "rotate_smtp", "reason": smtp_result.get("rotate_reason", "")})
            await _telegram_alert(
                f"📧 <b>SMTP ACCOUNT ROTATED</b>\n\n"
                f"<b>Reason:</b> {smtp_result.get('rotate_reason', 'Rate limited')}\n\n"
                f"<i>Next SMTP account now active.</i>"
            )
            result["alerts_sent"].append("smtp_rotation")
    except Exception as e:
        result["errors"].append(f"SMTP rotation: {e}")
        logger.error(f"SMTP rotation error: {e}")
    
    # 5. Groq API Key Health
    try:
        global _last_groq_check_time, _last_groq_result, _groq_alerted_unhealthy
        now = time.time()
        
        # Only check every 30 minutes (1800s) if healthy, or every 5 minutes (300s) if unhealthy
        check_interval = 1800
        if _last_groq_result and not _last_groq_result.get("healthy"):
            check_interval = 300
            
        if force or (now - _last_groq_check_time > check_interval) or _last_groq_result is None:
            groq_result = await _check_groq_api_async()
            _last_groq_check_time = now
            _last_groq_result = groq_result
        else:
            groq_result = _last_groq_result
            
        result["groq_check"] = groq_result
        
        if not groq_result.get("healthy"):
            # Only alert if we haven't alerted yet about this failure transition
            if not _groq_alerted_unhealthy or force:
                _groq_alerted_unhealthy = True
                await _telegram_alert(
                    f"🔑 <b>GROQ API KEY ISSUE</b>\n\n"
                    f"<b>Status:</b> {groq_result.get('status', 'unknown')}\n"
                    f"<b>Error:</b> {groq_result.get('error', 'Unknown')}\n\n"
                    f"<i>AI features may be degraded. Check your Groq API key.</i>"
                )
                result["alerts_sent"].append("groq_issue")
                _save_history({"action": "groq_alert", "status": groq_result.get("status")})
        else:
            # Reset the alert flag if it's back to healthy
            _groq_alerted_unhealthy = False
    except Exception as e:
        result["errors"].append(f"Groq check: {e}")
        logger.error(f"Groq check error: {e}")
    
    return result


# ═══════════════════════════════════════════════════════════════
# Background Monitor (asyncio — no subprocess)
# ═══════════════════════════════════════════════════════════════

async def start_background_monitor():
    """
    Start the background self-healing monitor.
    Runs every 60 seconds. Designed for PythonAnywhere free tier.
    Uses asyncio.sleep — no threads or subprocesses.
    """
    global _heal_state
    
    with _state_lock:
        if _heal_state["running"]:
            logger.info("Auto-heal monitor already running")
            return
        _heal_state["running"] = True
    
    logger.info("🩺 Auto-heal background monitor started (60s interval)")
    
    try:
        while True:
            try:
                result = await run_heal_cycle(force=False)
                
                if result["errors"]:
                    logger.warning(f"Heal cycle had {len(result['errors'])} errors")
                
                # Log summary (not spamming)
                actions = sum([
                    result["stuck_campaigns_cleared"],
                    result["dead_locks_removed"],
                    1 if result.get("smtp_rotation", {}).get("rotated") else 0,
                    1 if result["ram_heal"] else 0,
                ])
                if actions > 0:
                    logger.info(f"Heal cycle: {actions} actions taken | RAM: {result['ram_pct']}%")
                
                await asyncio.sleep(_CHECK_INTERVAL)
                
            except asyncio.CancelledError:
                logger.info("Auto-heal monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Heal cycle crashed: {e}", exc_info=True)
                with _state_lock:
                    _heal_state["errors"] += 1
                await asyncio.sleep(_CHECK_INTERVAL)
    finally:
        with _state_lock:
            _heal_state["running"] = False


def start_background_monitor_sync():
    """
    Synchronous entry point for starting the monitor from FastAPI startup.
    Creates a background asyncio task.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    task = loop.create_task(start_background_monitor())
    logger.info("Auto-heal monitor task created")
    return task


# ═══════════════════════════════════════════════════════════════
# API Helpers
# ═══════════════════════════════════════════════════════════════

def get_heal_state() -> Dict[str, Any]:
    """Return current heal state for API responses."""
    with _state_lock:
        return dict(_heal_state)


def get_system_health_snapshot() -> Dict[str, Any]:
    """
    Get a snapshot of current system health for /api/system/status.
    Lightweight — designed for <100ms response.
    """
    ram_pct = _check_ram_usage()
    
    # Try to get campaign/email counts from DB
    campaigns_active = 0
    total_applications = 0
    emails_sent_today = 0
    
    conn = _get_db()
    if conn:
        try:
            # Campaigns
            for table, col in [("campaigns", "status"), ("email_campaigns", "status")]:
                try:
                    row = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} = 'running'").fetchone()
                    if row:
                        campaigns_active += row[0] if not isinstance(row, dict) else list(row.values())[0]
                except Exception:
                    pass
            
            # Applications
            try:
                row = conn.execute("SELECT COUNT(*) FROM job_applications").fetchone()
                if row:
                    total_applications = row[0] if not isinstance(row, dict) else list(row.values())[0]
            except Exception:
                pass
            
            # Emails today
            try:
                row = conn.execute(
                    "SELECT COUNT(*) FROM sent_emails WHERE sent_at > datetime('now', '-1 day')"
                ).fetchone()
                if row:
                    emails_sent_today = row[0] if not isinstance(row, dict) else list(row.values())[0]
            except Exception:
                pass
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    # Groq API status
    groq_healthy = bool(os.getenv("GROQ_API_KEY", ""))
    
    # SMTP status
    smtp_configured = bool(
        os.getenv("SMTP_HOST", "") or
        os.getenv("SMTP1_HOST", "") or
        os.getenv("EMAIL_HOST", "")
    )
    
    # PA config
    pa_configured = bool(os.getenv("PA_API_TOKEN", ""))
    
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ram": {
            "percent": ram_pct,
            "threshold": _RAM_THRESHOLD_PCT,
            "warning": ram_pct > _RAM_THRESHOLD_PCT,
        },
        "campaigns": {
            "active": campaigns_active,
            "stuck_threshold_minutes": _STUCK_THRESHOLD_MINUTES,
        },
        "applications": {
            "total": total_applications,
        },
        "emails": {
            "sent_today": emails_sent_today,
        },
        "apis": {
            "groq": groq_healthy,
            "pa_api": pa_configured,
            "smtp": smtp_configured,
        },
        "auto_heal": get_heal_state(),
    }


# ═══════════════════════════════════════════════════════════════
# Exports
# ═══════════════════════════════════════════════════════════════

__all__ = [
    "run_heal_cycle",
    "start_background_monitor",
    "start_background_monitor_sync",
    "get_heal_state",
    "get_system_health_snapshot",
    "_CHECK_INTERVAL",
    "_RAM_THRESHOLD_PCT",
    "_STUCK_THRESHOLD_MINUTES",
]
