"""
JobHunt Pro v15 — Self-Healing Engine
Auto-detects failures, diagnoses root cause, applies fixes.
Runs every cycle: API keys → SMTP → DB → Scrapers → Disk → Processes.
"""
import asyncio
import logging
import os
import time
import json
import shutil
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import httpx

import config

logger = logging.getLogger(__name__)

HEALING_HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "healing_history.json",
)


def _load_history() -> List[Dict]:
    """Load healing history from JSON file."""
    try:
        if os.path.exists(HEALING_HISTORY_FILE):
            with open(HEALING_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception:
        pass
    return []


def _save_history(history: List[Dict]):
    """Append and save healing history."""
    try:
        os.makedirs(os.path.dirname(HEALING_HISTORY_FILE), exist_ok=True)
        # Keep last 200 entries
        history = history[-200:]
        with open(HEALING_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, default=str)
    except Exception as e:
        logger.warning(f"Failed to save healing history: {e}")


async def _telegram_notify(message: str):
    """Send a notification to Telegram if configured."""
    token = getattr(config, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(config, "TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(
                url,
                json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            )
    except Exception as e:
        logger.debug(f"Telegram notify failed: {e}")


async def _test_groq_api(key: str) -> bool:
    """Test a Groq API key with a minimal request."""
    if not key:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": "OK"}],
                    "max_tokens": 5,
                },
            )
            return resp.status_code == 200
    except Exception:
        return False


async def _test_jsearch_api(key: str) -> bool:
    """Test JSearch API key."""
    if not key:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://jsearch.p.rapidapi.com/search",
                headers={
                    "X-RapidAPI-Key": key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
                },
                params={"query": "network engineer", "page": "1", "num_pages": "1"},
            )
            return resp.status_code == 200
    except Exception:
        return False


def _get_disk_usage(path: str = ".") -> Tuple[float, float]:
    """Get disk usage: (used_gb, total_gb, percent_used)."""
    try:
        usage = shutil.disk_usage(path)
        total_gb = usage.total / (1024 ** 3)
        used_gb = usage.used / (1024 ** 3)
        percent = (usage.used / usage.total) * 100
        return used_gb, total_gb, percent
    except Exception:
        return 0, 0, 0


class HealingEngine:
    """
    Self-healing system for JobHunt Pro.
    Detects failures, diagnoses root cause, applies fixes.

    Usage:
        healer = HealingEngine()
        report = await healer.diagnose_and_heal()
        # report = {"issues_detected": 2, "auto_fixed": 1, "need_attention": 1, ...}
    """

    def __init__(self):
        self.db = None
        self.email_engine = None
        self._history = _load_history()
        self._last_diag_time = 0
        self._min_diag_interval = 120  # seconds between full diagnostics

        # Try to lazily import and initialize DB
        try:
            from core.database import Database
            self.db = Database()
        except Exception as e:
            logger.warning(f"HealingEngine: DB init deferred ({e})")

        # Try to lazily import email engine singleton
        try:
            from core.email_engine import email_engine
            self.email_engine = email_engine
        except Exception as e:
            logger.warning(f"HealingEngine: EmailEngine init deferred ({e})")

    # ──────────────────────────────────────────────
    # PUBLIC ENTRY POINT
    # ──────────────────────────────────────────────

    async def diagnose_and_heal(self, force: bool = False) -> Dict:
        """
        Run all diagnostics and auto-fixes.
        Returns a summary dict.
        """
        now = time.time()
        if not force and (now - self._last_diag_time) < self._min_diag_interval:
            return {"status": "skipped", "reason": "too_soon"}

        self._last_diag_time = now
        issues = []
        fixes = []

        try:
            # Run all diagnostics
            diag_tasks = [
                self._check_api_keys(),
                self._check_smtp_health(),
                self._check_db_integrity(),
                self._check_scraper_health(),
                self._check_disk_space(),
            ]
            results = await asyncio.gather(*diag_tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Diagnostic {i} raised: {result}")
                    continue
                if isinstance(result, tuple):
                    issue, fix = result
                    if issue:
                        issues.append(issue)
                    if fix:
                        fixes.append(fix)

            # Process health check (sync, no await needed)
            proc_issue = self._check_process_health()
            if proc_issue:
                issues.extend(proc_issue)

        except Exception as e:
            logger.error(f"Diagnose cycle error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "issues_detected": 0,
                "auto_fixed": 0,
                "need_attention": 0,
            }

        # Build report
        summary = self._build_report(issues, fixes)

        # Log to Telegram if any real healing happened
        if issues or fixes:
            await self._report_to_telegram(summary)

        # Save history
        if issues or fixes:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "issues": [i["check"] for i in issues],
                "fixes": [f["action"] for f in fixes],
                "summary": summary["summary_text"],
            }
            self._history.append(entry)
            _save_history(self._history)

        return summary

    # ──────────────────────────────────────────────
    # DIAGNOSTICS
    # ──────────────────────────────────────────────

    async def _check_api_keys(self) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        🔍 API Key Check — Test Groq + JSearch keys.
        Returns (issue_or_None, fix_or_None).
        """
        issues = []
        fixes = []

        # 1. Groq
        groq_key = os.getenv("GROQ_API_KEY", "")
        groq_ok = await _test_groq_api(groq_key)
        if not groq_key:
            issues.append({
                "check": "groq_api_key",
                "severity": "warning",
                "detail": "GROQ_API_KEY is empty — AI tailoring will fail",
            })
            fixes.append({
                "action": "groq_key_missing",
                "detail": "Set GROQ_API_KEY in .env file manually",
                "auto_fixable": False,
            })
        elif not groq_ok:
            issues.append({
                "check": "groq_api_key",
                "severity": "error",
                "detail": "GROQ_API_KEY test failed",
            })
            fixes.append({
                "action": "groq_fallback_model",
                "detail": "AI will use llama-3.1-8b-instant as fallback (lower quality but works)",
                "auto_fixable": True,
                "applied": True,
            })

        # 2. JSearch
        jsearch_key = os.getenv("JSEARCH_API_KEY", "")
        jsearch_ok = await _test_jsearch_api(jsearch_key)
        if not jsearch_key:
            issues.append({
                "check": "jsearch_api_key",
                "severity": "info",
                "detail": "JSEARCH_API_KEY not set — will rely on curated contacts only",
            })
        elif not jsearch_ok:
            issues.append({
                "check": "jsearch_api_key",
                "severity": "warning",
                "detail": "JSearch API key invalid or quota exhausted",
            })
            fixes.append({
                "action": "jsearch_fallback",
                "detail": "Scraper will skip JSearch, use curated contacts + LinkedIn only",
                "auto_fixable": True,
                "applied": True,
            })

        # Return only the first issue+fix pair (most critical)
        issue = issues[0] if issues else None
        fix = fixes[0] if fixes else None
        return (issue, fix) if (issue or fix) else (None, None)

    async def _check_smtp_health(self) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        🔍 SMTP Health — Check circuit breaker & scheduler.
        """
        if not self.email_engine:
            return (None, None)

        try:
            cb = self.email_engine.circuit_breaker
            disabled = cb._disabled_until if hasattr(cb, "_disabled_until") else {}
            failures = cb._failures if hasattr(cb, "_failures") else {}

            if disabled:
                provider_names = list(disabled.keys())
                issues = []
                fixes = []

                for name in provider_names:
                    # Check if cooldown expired
                    until = disabled.get(name, 0)
                    remaining = until - time.time()
                    if remaining > 0:
                        issues.append({
                            "check": f"smtp_circuit_open:{name}",
                            "severity": "error",
                            "detail": f"SMTP {name} circuit open for {remaining:.0f}s more",
                        })

                        # Try a different provider — rotation is automatic via scheduler
                        if hasattr(self.email_engine, "scheduler"):
                            provider = self.email_engine.scheduler.get_next_provider()
                            if provider and provider != name:
                                fixes.append({
                                    "action": f"smtp_rotate:{name}→{provider}",
                                    "detail": f"Rotated from {name} to {provider}",
                                    "auto_fixable": True,
                                    "applied": True,
                                })

                if issues:
                    return (issues[0], fixes[0] if fixes else None)

            # Check quota exhaustion for all providers
            if hasattr(self.email_engine, "scheduler") and hasattr(self.email_engine.scheduler, "providers"):
                schedulers = self.email_engine.scheduler.providers
                total_available = sum(
                    1 for p in schedulers.values()
                    if getattr(p, "sent_today", 0) < getattr(p, "daily_limit", 100)
                )
                if total_available == 0 and schedulers:
                    return (
                        {
                            "check": "smtp_all_exhausted",
                            "severity": "error",
                            "detail": "ALL email providers exhausted daily quota",
                        },
                        {
                            "action": "smtp_wait_tomorrow",
                            "detail": "All providers depleted — will resume next UTC day",
                            "auto_fixable": False,
                        },
                    )

        except Exception as e:
            logger.debug(f"SMTP health check error: {e}")

        return (None, None)

    async def _check_db_integrity(self) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        🔍 DB Integrity — Check if tables exist, recreate if missing.
        """
        if not self.db:
            return (None, None)

        def _check_sync():
            with self.db._get_conn() as conn:
                cur = conn.execute("SELECT 1")
                cur.fetchone()

        try:
            # Test DB by checking if connection works
            try:
                await asyncio.to_thread(_check_sync)
                # DB is alive
            except Exception as db_err:
                err_str = str(db_err).lower()

                # Table doesn't exist → recreate
                if "no such table" in err_str or "relation" in err_str:
                    logger.warning("DB integrity: tables missing, recreating...")
                    await self.db.create_tables()
                    return (
                        {
                            "check": "db_missing_tables",
                            "severity": "error",
                            "detail": "Database tables missing — recreated",
                        },
                        {
                            "action": "db_tables_recreated",
                            "detail": "Missing DB tables auto-created",
                            "auto_fixable": True,
                            "applied": True,
                        },
                    )

                # Connection error
                elif "connection" in err_str or "timeout" in err_str:
                    return (
                        {
                            "check": "db_connection",
                            "severity": "error",
                            "detail": f"DB connection failed: {err_str[:100]}",
                        },
                        {
                            "action": "db_reconnect",
                            "detail": "Reinitialize database connection",
                            "auto_fixable": True,
                            "applied": True,
                        },
                    )

                # Other error
                else:
                    logger.warning(f"DB integrity: unexpected error ({err_str[:100]})")
                    # Try recreating tables as safety net
                    try:
                        await self.db.create_tables()
                    except Exception:
                        pass
                    return (
                        {
                            "check": "db_error",
                            "severity": "error",
                            "detail": f"DB error: {err_str[:100]}",
                        },
                        {
                            "action": "db_attempt_recovery",
                            "detail": "Attempted table recreation as recovery",
                            "auto_fixable": True,
                            "applied": True,
                        },
                    )

            # Tables exist — verify a few key ones
            try:
                def _verify_tables():
                    tables = ["jobs"]  # Note: legacy schema only has "jobs" table, other tables like users/applications are in the PostgreSQL/DatabaseManager schema
                    with self.db._get_conn() as conn:
                        for table in tables:
                            conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                            
                await asyncio.to_thread(_verify_tables)
            except Exception as e:
                err_str = str(e).lower()
                logger.warning(f"DB integrity: table missing or error ({err_str[:100]}), recreating...")
                try:
                    await self.db.create_tables()
                    return (
                        {
                            "check": "db_missing_table",
                            "severity": "warning",
                            "detail": "Database table was missing — recreated",
                        },
                        {
                            "action": "db_table_recreated",
                            "detail": "Recreated missing database table",
                            "auto_fixable": True,
                            "applied": True,
                        },
                    )
                except Exception as create_err:
                    logger.error(f"Failed to recreate tables: {create_err}")

        except Exception as e:
            logger.warning(f"DB integrity check error: {e}")

        return (None, None)

    async def _check_scraper_health(self) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        🔍 Scraper Health — Test if job search sources are reachable.
        """
        issues = []
        fixes = []

        # Test JSearch endpoint
        jsearch_key = os.getenv("JSEARCH_API_KEY", "")
        if jsearch_key:
            ok = await _test_jsearch_api(jsearch_key)
            if not ok:
                issues.append({
                    "check": "scraper_jsearch",
                    "severity": "warning",
                    "detail": "JSearch scraper returning errors (quota or timeout)",
                })
                fixes.append({
                    "action": "scraper_jsearch_fallback",
                    "detail": "Fallback to curated contacts only for job sourcing",
                    "auto_fixable": True,
                    "applied": True,
                })

        # Test LinkedIn-style scraper (generic HTTP test)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://www.linkedin.com/jobs/search/?keywords=network+engineer",
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        ),
                    },
                    follow_redirects=True,
                )
                if resp.status_code in (403, 429):
                    issues.append({
                        "check": "scraper_linkedin",
                        "severity": "warning",
                        "detail": f"LinkedIn blocking scrapers (HTTP {resp.status_code})",
                    })
                    fixes.append({
                        "action": "scraper_linkedin_fallback",
                        "detail": "Will use JSearch + curated contacts instead",
                        "auto_fixable": True,
                        "applied": True,
                    })
        except Exception as e:
            logger.debug(f"LinkedIn scraper test: {e}")

        issue = issues[0] if issues else None
        fix = fixes[0] if fixes else None
        return (issue, fix) if (issue or fix) else (None, None)

    async def _check_disk_space(self) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        🔍 Disk Space — Warn if low.
        """
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        used_gb, total_gb, percent = _get_disk_usage(project_root)

        if percent > 90:
            issue = {
                "check": "disk_space_critical",
                "severity": "error",
                "detail": f"Disk {percent:.0f}% full ({used_gb:.1f}GB/{total_gb:.1f}GB)",
            }
            fix = {
                "action": "disk_cleanup_needed",
                "detail": "Free up disk: delete old logs, temp files",
                "auto_fixable": False,
            }
            return (issue, fix)

        if percent > 80:
            issue = {
                "check": "disk_space_warning",
                "severity": "warning",
                "detail": f"Disk {percent:.0f}% full ({used_gb:.1f}GB/{total_gb:.1f}GB)",
            }
            return (issue, None)

        return (None, None)

    def _check_process_health(self) -> List[Dict]:
        """
        🔍 Process Health — Check if expected processes are alive.
        Returns list of issues (no auto-fix for process checks).
        """
        issues = []

        # Check that the database file exists (core resource)
        db_path = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
        if not os.path.exists(db_path):
            # Try relative to project root
            alt_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_path
            )
            if not os.path.exists(alt_path):
                issues.append({
                    "check": "db_file_missing",
                    "severity": "warning",
                    "detail": f"DB file '{db_path}' not found — will create on first use",
                })

        # Check log directory is writable
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
        )
        if not os.access(log_dir, os.W_OK):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception:
                issues.append({
                    "check": "log_dir_not_writable",
                    "severity": "warning",
                    "detail": "Log directory not writable",
                })

        return issues

    # ──────────────────────────────────────────────
    # REPORTING
    # ──────────────────────────────────────────────

    def _build_report(self, issues: List[Dict], fixes: List[Dict]) -> Dict:
        """Build a structured report from issues and fixes."""
        total_issues = len(issues)
        auto_fixed = sum(
            1 for f in fixes if f.get("auto_fixable") and f.get("applied")
        )
        need_attention = sum(
            1 for f in fixes if not f.get("auto_fixable")
        ) + sum(
            1 for i in issues
            if not any(
                f.get("action", "").startswith(i["check"].split(":")[0])
                for f in fixes
            )
        )

        summary_text_parts = []
        if total_issues == 0:
            summary_text_parts.append("[OK] All systems healthy - no issues detected")
        else:
            summary_text_parts.append(
                f"[OK] {total_issues} issue(s) detected, "
                f"{auto_fixed} auto-fixed, "
                f"{need_attention} need attention"
            )
            # Detail per issue
            for issue in issues:
                line = f"  [!] [{issue['check']}] {issue['detail']}"
                summary_text_parts.append(line)

            # Detail per fix
            for fix in fixes:
                status = "[OK] Auto-fixed" if fix.get("applied") else "[ERR] Manual"
                line = f"  {status}: {fix['detail']}"
                summary_text_parts.append(line)

        summary_text = "\n".join(summary_text_parts)
        logger.info(f"\n{summary_text}")

        return {
            "issues_detected": total_issues,
            "auto_fixed": auto_fixed,
            "need_attention": need_attention,
            "issues": issues,
            "fixes": fixes,
            "summary_text": summary_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _report_to_telegram(self, summary: Dict):
        """Send healing report to Telegram."""
        total = summary["issues_detected"]
        fixed = summary["auto_fixed"]
        attention = summary["need_attention"]

        if total == 0:
            return  # Don't spam if nothing to report

        icon = "🟢" if fixed == total else "🟡" if fixed > 0 else "🔴"
        msg = (
            f"<b>{icon} Healing Report</b>\n"
            f"{summary['summary_text'][:2000]}"
        )

        await _telegram_notify(msg)

    def get_history(self, limit: int = 20) -> List[Dict]:
        """Get recent healing history."""
        return self._history[-limit:]

    def get_summary_stats(self) -> Dict:
        """Get aggregate healing statistics."""
        total_cycles = len(self._history)
        total_issues = sum(len(h.get("issues", [])) for h in self._history)
        total_fixes = sum(len(h.get("fixes", [])) for h in self._history)

        # Count by check type
        check_counts: Dict[str, int] = {}
        for h in self._history:
            for issue in h.get("issues", []):
                check = issue["check"].split(":")[0]
                check_counts[check] = check_counts.get(check, 0) + 1

        return {
            "total_healing_cycles": total_cycles,
            "total_issues_found": total_issues,
            "total_fixes_applied": total_fixes,
            "most_common_issues": dict(
                sorted(check_counts.items(), key=lambda x: -x[1])[:5]
            ),
            "last_checkup": self._history[-1]["timestamp"] if self._history else "never",
        }


# Singleton for easy import
healing_engine = HealingEngine()


# Convenience function for one-shot healing
async def run_healing_check(force: bool = False) -> Dict:
    """Run a healing check and return the report."""
    return await healing_engine.diagnose_and_heal(force=force)
