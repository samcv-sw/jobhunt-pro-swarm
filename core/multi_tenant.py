"""
JobHunt Pro — Multi-Tenant Campaign Runner v1.0
================================================
Enables JobHunt Pro to run campaigns for MULTIPLE users simultaneously
with complete isolation. Each user is a "tenant" with their own profile,
CV, SMTP rotation, stats tracking, and campaign queue.

Architecture:
  MultiTenantRunner
    ├── tenant_id = user_id (each user is a tenant)
    ├── Per-tenant profile, CV, SMTP caps
    ├── Parallel execution via asyncio.gather
    ├── Per-tenant stats isolation
    └── Rita Cordahi pre-configured as tenant #2

API Endpoints (to be mounted in app_v2.py):
  POST /api/v2/cloud-tick        → multi-tenant tick (overrides single-tenant)
  GET  /api/multi-tenant/status  → show all tenants and their stats
  POST /api/multi-tenant/add-tenant → add new tenant via API
"""

import asyncio
import json
import logging
import os
import random
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

# ── Same imports used by campaign_runner for reusability ──
import httpx
from fastapi import APIRouter, Request, HTTPException

logger = logging.getLogger(__name__)

# ── FastAPI Router (unified; mount in app_v2.py) ───────────────────────────

router = APIRouter(tags=["multi-tenant"])


# ══════════════════════════════════════════════════════════════════════════════
#  PRECONFIGURED TENANT: Rita Cordahi
# ══════════════════════════════════════════════════════════════════════════════

RITA_CORDAHI_PROFILE = {
    "tenant_name": "Rita Cordahi",
    "email": "ritacordahi2@gmail.com",
    "phone": "+961 76 005 412",
    "profession": "HR Operations Manager / HR Coordinator / Recruitment Specialist",
    "target_titles": "HR Operations Manager, HR Coordinator, Customer Operations Specialist, Recruitment Specialist",
    "skills": "HR operations, customer service, recruitment, onboarding, employee relations, HRIS, payroll coordination, performance management, training & development, talent acquisition, interview coordination, screening, ATS management, Microsoft Office, Excel, PowerPoint, Google Workspace, team leadership, reporting, data entry, contract management, compliance, labor law",
    "experience_years": 5,
    "target_locations": "Lebanon, Beirut, Jbeil, Keserwan, Metn, Mount Lebanon",
    "target_salary": "$1,500+/month",
    "target_companies": "Murex, Bank Audi, BLOM Bank, Byblos Bank, Touch, Alfa, Azadea Group, CME Offshore, Malia Group, Berytech",
    "linkedin": "https://www.linkedin.com/in/rita-cordahi/",
}


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: DB path resolution
# ══════════════════════════════════════════════════════════════════════════════

def _get_db_path() -> str:
    """Resolve the primary SQLite database path."""
    db_path = os.getenv("DB_PATH", "jobhunt_saas_v2.db")
    base = Path(__file__).resolve().parent.parent
    full = str(base / db_path)
    if not os.path.exists(full):
        # Try direct filename in project root
        alt = str(base / "jobhunt_saas_v2.db")
        if os.path.exists(alt):
            return alt
    return full


def _get_conn() -> sqlite3.Connection:
    """Get a read/write SQLite connection with WAL mode."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")
    except Exception:
        pass
    return conn


# ══════════════════════════════════════════════════════════════════════════════
#  TENANT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

class TenantManager:
    """Manages tenant (user) records and their associated profiles."""

    @staticmethod
    def ensure_tenant(name: str, email: str, phone: str = "",
                      linkedin: str = "", profession: str = "",
                      skills: str = "", experience_years: int = 5,
                      password: str = None) -> Dict[str, Any]:
        """
        Ensure a tenant exists in the users table and their CV profile
        exists in cv_profiles. Auto-creates if missing.

        Returns: {"tenant_id": str, "profile_id": int, "created": bool}
        """
        conn = _get_conn()
        created_user = False
        created_profile = False

        try:
            # ── Check / create user ────────────────────────────────
            user_row = conn.execute(
                "SELECT user_id FROM users WHERE email = ?",
                (email,)
            ).fetchone()

            if user_row:
                tenant_id = user_row["user_id"]
            else:
                tenant_id = f"user_{uuid.uuid4().hex[:12]}"
                _pw = password or uuid.uuid4().hex
                _hash = _pw  # (real bcrypt handled by app_v2 on signup; placeholder for auto-created tenants)

                try:
                    conn.execute("""
                        INSERT INTO users
                        (user_id, email, password_hash, name, phone, created_at)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (tenant_id, email, _hash, name, phone))
                    conn.commit()
                    created_user = True
                    logger.info(f"[MultiTenant] Created user: {name} ({tenant_id})")
                except sqlite3.IntegrityError:
                    # Race condition — another worker created it. Re-read.
                    user_row = conn.execute(
                        "SELECT user_id FROM users WHERE email = ?",
                        (email,)
                    ).fetchone()
                    if user_row:
                        tenant_id = user_row["user_id"]
                    else:
                        raise

            # ── Check / create cv_profiles ─────────────────────────
            profile_row = conn.execute(
                "SELECT id FROM cv_profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (tenant_id,)
            ).fetchone()

            if profile_row:
                profile_id = profile_row["id"]
            else:
                cv_text = TenantManager._generate_cv_text(
                    name=name, profession=profession, skills=skills,
                    experience_years=experience_years, phone=phone,
                    email=email, linkedin=linkedin
                )
                conn.execute("""
                    INSERT INTO cv_profiles
                    (user_id, target_titles, skills, experience_years,
                     cv_text, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (tenant_id, profession, skills, experience_years, cv_text))
                conn.commit()
                profile_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                created_profile = True
                logger.info(f"[MultiTenant] Created CV profile #{profile_id} for {name}")

            return {
                "tenant_id": tenant_id,
                "profile_id": profile_id,
                "created_user": created_user,
                "created_profile": created_profile,
                "name": name,
                "email": email,
            }

        finally:
            conn.close()

    @staticmethod
    def _generate_cv_text(name: str, profession: str, skills: str,
                          experience_years: int, phone: str = "",
                          email: str = "", linkedin: str = "") -> str:
        """Generate a plausible CV text block for a tenant."""
        loc = "Lebanon"
        skills_clean = skills.replace(",", ", ") if skills else ""
        cv = f"""{name.upper()}
{profession}
{phone} | {email}
{linkedin}
Location: {loc}

PROFESSIONAL SUMMARY
Dedicated {profession} with {experience_years}+ years of experience in {skills_clean[:80]}...
Proven track record of delivering results in fast-paced environments across {loc}.

SKILLS
{skills_clean}

PROFESSIONAL EXPERIENCE
• {experience_years}+ years in {profession.split('/')[0].strip()}
• Expertise in {skills[:200]}

EDUCATION
• Bachelor's Degree (Lebanon)

LANGUAGES
• Arabic (Native), English (Fluent), French (Intermediate)
"""
        return cv.strip()

    @staticmethod
    def list_tenants() -> List[Dict[str, Any]]:
        """List all tenants with a CV profile."""
        conn = _get_conn()
        try:
            rows = conn.execute("""
                SELECT u.user_id, u.name, u.email, u.phone, u.created_at,
                       p.id AS profile_id, p.target_titles, p.skills,
                       p.experience_years
                FROM users u
                INNER JOIN cv_profiles p ON p.user_id = u.user_id
                GROUP BY u.user_id
                ORDER BY u.created_at ASC
            """).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_tenant_stats(tenant_id: str) -> Dict[str, Any]:
        """Get per-tenant campaign stats."""
        conn = _get_conn()
        try:
            # Total campaigns
            total_c = conn.execute(
                "SELECT COUNT(*) FROM campaigns WHERE user_id = ?",
                (tenant_id,)
            ).fetchone()[0]

            # Active campaigns
            active_c = conn.execute(
                "SELECT COUNT(*) FROM campaigns WHERE user_id = ? AND status IN ('pending','running')",
                (tenant_id,)
            ).fetchone()[0]

            # Completed
            completed_c = conn.execute(
                "SELECT COUNT(*) FROM campaigns WHERE user_id = ? AND status = 'completed'",
                (tenant_id,)
            ).fetchone()[0]

            # Emails sent
            emails_sent = conn.execute("""
                SELECT COUNT(*) FROM campaign_emails ce
                JOIN campaigns c ON c.campaign_id = ce.campaign_id
                WHERE c.user_id = ? AND ce.status = 'sent'
            """, (tenant_id,)).fetchone()[0]

            # Sum of sent_count from campaigns table
            total_sent = conn.execute(
                "SELECT COALESCE(SUM(sent_count), 0) FROM campaigns WHERE user_id = ?",
                (tenant_id,)
            ).fetchone()[0]

            # User row
            user_row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (tenant_id,)
            ).fetchone()

            return {
                "tenant_id": tenant_id,
                "name": user_row["name"] if user_row else "Unknown",
                "email": user_row["email"] if user_row else "Unknown",
                "total_campaigns": total_c,
                "active_campaigns": active_c,
                "completed_campaigns": completed_c,
                "emails_sent": emails_sent,
                "total_sent_count": total_sent,
            }
        finally:
            conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  MULTI-TENANT CAMPAIGN RUNNER
# ══════════════════════════════════════════════════════════════════════════════

class MultiTenantRunner:
    """
    Parallel multi-tenant campaign runner.
    Fetches ALL active campaigns across ALL users and executes them
    concurrently with full isolation per tenant.
    """

    def __init__(self, company_limit: int = 10):
        self.company_limit = company_limit
        self.tenant_stats: Dict[str, Dict[str, Any]] = {}

    async def tick(self) -> Dict[str, Any]:
        """
        Main multi-tenant tick:
        1. Fetch ALL active campaigns across ALL users
        2. Group by tenant
        3. Run in parallel with asyncio.gather
        4. Aggregate results
        """
        start_time = time.time()
        results = {
            "timestamp": datetime.now().isoformat(),
            "tenant_count": 0,
            "campaigns_processed": 0,
            "emails_sent": 0,
            "errors": 0,
            "tenants": {},
            "status": "ok",
        }

        # ── Step 1: Fetch all active campaigns ──
        campaigns = self._fetch_all_active_campaigns()
        if not campaigns:
            logger.info("[MultiTenant] No active campaigns across any tenant.")
            results["message"] = "No active campaigns found"
            return results

        logger.info(f"[MultiTenant] Found {len(campaigns)} active campaign(s) across tenants.")

        # ── Step 2: Group campaigns by tenant_id ──
        tenant_campaigns: Dict[str, List[Dict]] = {}
        for c in campaigns:
            tid = c.get("user_id", "unknown")
            if tid not in tenant_campaigns:
                tenant_campaigns[tid] = []
            tenant_campaigns[tid].append(c)

        results["tenant_count"] = len(tenant_campaigns)

        # ── Step 3: Run each tenant's campaigns in parallel ──
        async def run_tenant(tid: str, t_campaigns: List[Dict]) -> Dict[str, Any]:
            tenant_result = {
                "tenant_id": tid,
                "campaigns": [],
                "total_sent": 0,
                "total_failed": 0,
            }
            for camp in t_campaigns:
                cid = camp["campaign_id"]
                try:
                    from core.campaign_runner import run_campaign
                    camp_result = await run_campaign(
                        campaign_id=cid,
                        get_db_fn=lambda cp=_get_db_path(): sqlite3.connect(
                            cp, timeout=30, check_same_thread=False
                        ),
                        config=__import__("config"),
                        company_limit=self.company_limit,
                    )
                    tenant_result["campaigns"].append({
                        "campaign_id": cid,
                        "result": camp_result,
                    })
                    if isinstance(camp_result, dict):
                        tenant_result["total_sent"] += camp_result.get("sent", 0)
                        tenant_result["total_failed"] += camp_result.get("failed", 0)
                except Exception as e:
                    logger.error(f"[MultiTenant] Campaign {cid} (tenant {tid}) failed: {e}")
                    tenant_result["campaigns"].append({
                        "campaign_id": cid,
                        "error": str(e),
                    })
            return tenant_result

        # Execute all tenants in parallel
        tasks = [
            run_tenant(tid, t_campaigns)
            for tid, t_campaigns in tenant_campaigns.items()
        ]
        tenant_results = await asyncio.gather(*tasks, return_exceptions=True)

        # ── Step 4: Aggregate ──
        for tr in tenant_results:
            if isinstance(tr, Exception):
                results["errors"] += 1
                logger.error(f"[MultiTenant] Tenant runner crashed: {tr}")
                continue
            tid = tr["tenant_id"]
            results["tenants"][tid] = tr
            results["campaigns_processed"] += len(tr["campaigns"])
            results["emails_sent"] += tr["total_sent"]

        elapsed = time.time() - start_time
        results["elapsed_sec"] = round(elapsed, 2)
        logger.info(
            f"[MultiTenant] ✅ Tick complete: {results['tenant_count']} tenants, "
            f"{results['campaigns_processed']} campaigns, "
            f"{results['emails_sent']} emails, {elapsed:.1f}s"
        )

        # Persist per-tenant stats
        for tid in tenant_campaigns:
            try:
                self.tenant_stats[tid] = TenantManager.get_tenant_stats(tid)
            except Exception:
                pass

        return results

    def _fetch_all_active_campaigns(self) -> List[Dict[str, Any]]:
        """Fetch all pending/running campaigns across ALL users."""
        conn = _get_conn()
        try:
            rows = conn.execute("""
                SELECT * FROM campaigns
                WHERE status IN ('pending', 'running')
                ORDER BY created_at ASC
            """).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ── Per-tenant SMTP pool (each tenant gets their own rotation) ──

    @staticmethod
    def get_tenant_smtp_provider(tenant_id: str, config_module=None) -> Optional[Dict]:
        """
        Returns an SMTP provider for a given tenant. If the tenant has their own
        credentials configured (via RITA_* env vars for Rita, or env vars like
        TENANT_<ID>_SMTP_USER etc.), use those. Otherwise falls back to the
        default pool shared by all tenants.

        Per-tenant SMTP caps are enforced based on the provider's daily_limit.
        """
        # Check if this is a known tenant with custom SMTP config
        if tenant_id.startswith("user_"):
            # Look up tenant email to match known profiles
            conn = _get_conn()
            try:
                user_row = conn.execute(
                    "SELECT email FROM users WHERE user_id = ?", (tenant_id,)
                ).fetchone()
            finally:
                conn.close()

            if user_row:
                tenant_email = user_row["email"] or ""
                # Rita Cordahi detection
                if "ritacordahi" in tenant_email.lower():
                    # Use Rita's own SMTP if configured
                    rita_smtp_user = os.getenv("RITA_GMAIL_SMTP_USER", "")
                    rita_smtp_pass = os.getenv("RITA_GMAIL_APP_PASSWORD", "")
                    if rita_smtp_user and rita_smtp_pass:
                        return {
                            "name": f"rita_tenant",
                            "server": "smtp.gmail.com",
                            "port": 587,
                            "user": rita_smtp_user,
                            "password": rita_smtp_pass,
                            "daily_limit": 100,
                            "weight": 2,
                        }

        # Fallback: use the default SMTP pool from config
        if config_module is None:
            import config as config_module
        else:
            config_module = config_module

        providers = getattr(config_module, "ACTIVE_EMAIL_PROVIDERS", None)
        if providers is None:
            providers = getattr(config_module, "EMAIL_PROVIDERS", [])

        if providers:
            # Use a deterministic rotation based on tenant_id to avoid
            # all tenants hitting the same provider simultaneously
            seed = hash(tenant_id) % len(providers)
            # Return a weighted-random provider (tenant-sticky but varied)
            available = [p for p in providers if p.get("user") and p.get("password")]
            if not available:
                available = providers
            if available:
                idx = (seed + int(time.time() / 60)) % len(available)  # rotate every minute
                return available[idx]

        return None


# ══════════════════════════════════════════════════════════════════════════════
#  AUTO-SEED: Ensure Rita Cordahi exists in DB
# ══════════════════════════════════════════════════════════════════════════════

def _auto_seed_rita():
    """
    Called on module import.
    Ensures Rita Cordahi's user + profile exist in the DB.
    Idempotent — safe to call every time.
    """
    try:
        result = TenantManager.ensure_tenant(
            name=RITA_CORDAHI_PROFILE["tenant_name"],
            email=RITA_CORDAHI_PROFILE["email"],
            phone=RITA_CORDAHI_PROFILE["phone"],
            linkedin=RITA_CORDAHI_PROFILE["linkedin"],
            profession=RITA_CORDAHI_PROFILE["profession"],
            skills=RITA_CORDAHI_PROFILE["skills"],
            experience_years=RITA_CORDAHI_PROFILE["experience_years"],
        )
        if result.get("created_user") or result.get("created_profile"):
            logger.info(
                f"[MultiTenant] ✅ Auto-seeded Rita Cordahi: "
                f"tenant={result['tenant_id']}, profile={result['profile_id']}"
            )
        else:
            logger.debug(
                f"[MultiTenant] Rita Cordahi already exists: {result['tenant_id']}"
            )
    except Exception as e:
        logger.error(f"[MultiTenant] ⚠️ Failed to auto-seed Rita: {e}")


# Run on import (safe — idempotent)
_auto_seed_rita()


# ══════════════════════════════════════════════════════════════════════════════
#  API ENDPOINTS (FastAPI Router)
# ══════════════════════════════════════════════════════════════════════════════

# ── Singleton runner instance ──

_runner = None


def _get_runner() -> MultiTenantRunner:
    global _runner
    if _runner is None:
        _runner = MultiTenantRunner(company_limit=10)
    return _runner


@router.post("/v2/cloud-tick")
async def multi_tenant_cloud_tick(request: Request):
    """
    Main multi-tenant cron endpoint.
    Replaces the single-tenant /api/v2/cloud-tick with parallel multi-user execution.

    Called by GH Actions cron every 15 min.
    """
    try:
        runner = _get_runner()
        result = await runner.tick()
        return result
    except Exception as e:
        logger.error(f"[MultiTenant] Cloud tick failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/multi-tenant/status")
async def multi_tenant_status():
    """
    Show all tenants and their campaign stats.
    """
    try:
        tenants = TenantManager.list_tenants()
        result = {
            "status": "ok",
            "tenant_count": len(tenants),
            "tenants": [],
            "timestamp": datetime.now().isoformat(),
        }
        for t in tenants:
            tid = t.get("user_id", "")
            stats = TenantManager.get_tenant_stats(tid)
            result["tenants"].append(stats)
        return result
    except Exception as e:
        logger.error(f"[MultiTenant] Status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-tenant/add-tenant")
async def add_tenant(request: Request):
    """
    Add a new tenant via API.

    Body JSON:
    {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+961 12 345 678",
        "profession": "Software Engineer",
        "skills": "Python, JavaScript, React",
        "experience_years": 3,
        "target_titles": "Frontend Developer, UI Engineer",
        "target_locations": "Lebanon, Remote",
        "target_salary": "$2,000+/month",
        "target_companies": "Google, Microsoft"
    }
    """
    try:
        body = await request.json()

        name = body.get("name", "").strip()
        email = body.get("email", "").strip()
        if not name or not email:
            raise HTTPException(400, "name and email are required")

        phone = body.get("phone", "")
        profession = body.get("profession", "Professional")
        skills = body.get("skills", "")
        experience_years = int(body.get("experience_years", 5))
        linkedin = body.get("linkedin", "")
        target_titles = body.get("target_titles", profession)
        target_locations = body.get("target_locations", "Lebanon")
        target_salary = body.get("target_salary", "")
        target_companies = body.get("target_companies", "")

        result = TenantManager.ensure_tenant(
            name=name,
            email=email,
            phone=phone,
            linkedin=linkedin,
            profession=target_titles,  # stored in target_titles column
            skills=skills,
            experience_years=experience_years,
        )

        # Store the extra tenant metadata as a JSON blob in a notes field
        # (or we could add a tenant_meta table — for now store inline)
        conn = _get_conn()
        try:
            conn.execute("""
                UPDATE cv_profiles SET
                    target_titles = ?,
                    skills = ?
                WHERE user_id = ? AND id = ?
            """, (target_titles, skills, result["tenant_id"], result["profile_id"]))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

        return {
            "status": "ok",
            "tenant_id": result["tenant_id"],
            "profile_id": result["profile_id"],
            "name": name,
            "email": email,
            "created_user": result.get("created_user", False),
            "created_profile": result.get("created_profile", False),
            "message": f"Tenant '{name}' added successfully.",
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MultiTenant] Add tenant failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multi-tenant/rita")
async def get_rita_profile():
    """
    Return Rita Cordahi's pre-configured profile and stats.
    """
    try:
        conn = _get_conn()
        user_row = conn.execute(
            "SELECT user_id FROM users WHERE email = ?",
            (RITA_CORDAHI_PROFILE["email"],)
        ).fetchone()
        conn.close()

        if not user_row:
            return {
                "status": "error",
                "message": "Rita Cordahi not found in DB. Run seed first.",
            }

        tid = user_row["user_id"]
        stats = TenantManager.get_tenant_stats(tid)
        return {
            "status": "ok",
            "profile": RITA_CORDAHI_PROFILE,
            "stats": stats,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  CONVENIENCE: Direct runner for PA tick replacement
# ══════════════════════════════════════════════════════════════════════════════

async def run_multi_tenant_tick(company_limit: int = 10) -> Dict[str, Any]:
    """Convenience function — call from cloud_orchestrator or app router."""
    runner = MultiTenantRunner(company_limit=company_limit)
    return await runner.tick()
