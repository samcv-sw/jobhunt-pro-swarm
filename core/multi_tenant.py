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
    └── Demo User pre-configured as tenant #2

API Endpoints (to be mounted in app_v2.py):
  POST /api/v2/cloud-tick        → multi-tenant tick (overrides single-tenant)
  GET  /api/multi-tenant/status  → show all tenants and their stats
  POST /api/multi-tenant/add-tenant → add new tenant via API
"""

import json
import logging
import os

if os.getenv("SUPABASE_MODE") == "1":
    import core.supabase_rest_shim as sqlite3
else:
    import core.pg_sqlite_shim as sqlite3
import contextlib
import time
import uuid
import bcrypt
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Same imports used by campaign_runner for reusability ──
from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)

# ── FastAPI Router (unified; mount in app_v2.py) ───────────────────────────

router = APIRouter(tags=["multi-tenant"])


# ══════════════════════════════════════════════════════════════════════════════
#  PRECONFIGURED TENANT: Sam Salameh
# ══════════════════════════════════════════════════════════════════════════════

SAM_SALAMEH_PROFILE = {
    "tenant_name": "Sam Salameh",
    "email": "samsalameh.cv@gmail.com",
    "phone": "+961 71 019 053",
    "profession": "Senior Network Engineer",
    "target_titles": "network engineer, senior network engineer, network administrator",
    "skills": "cisco, mikrotik, fortinet, juniper, bgp, ospf, vpn, firewalls, linux, python",
    "experience_years": 15,
    "target_locations": "lebanon, uae, dubai, qatar, saudi arabia, remote",
    "target_salary": "$5,000+/month",
    "target_companies": "Cisco, Google, Microsoft, Amazon, Oracle, Huawei, Nokia, Ericsson, local ISPs",
    "linkedin": "https://www.linkedin.com/in/samsalameh/",
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
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.execute("PRAGMA busy_timeout=10000")
        conn.execute("PRAGMA synchronous=FULL")
    except Exception:
        pass
    return conn


# ══════════════════════════════════════════════════════════════════════════════
#  TENANT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════


class TenantManager:
    """Manages tenant (user) records and their associated profiles."""

    @staticmethod
    def _ensure_user_record(conn: sqlite3.Connection, name: str, email: str, phone: str, password: str | None) -> tuple[str, bool]:
        """Ensure a user record exists in the users table, creating it if needed."""
        user_row = conn.execute(
            "SELECT user_id FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user_row:
            return user_row["user_id"], False

        tenant_id = f"user_{uuid.uuid4().hex[:12]}"
        _pw = password or uuid.uuid4().hex
        _hash = bcrypt.hashpw(_pw.encode(), bcrypt.gensalt()).decode()

        try:
            conn.execute(
                """
                INSERT INTO users
                (user_id, email, password_hash, name, phone, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (tenant_id, email, _hash, name, phone),
            )
            conn.commit()
            logger.info(f"[MultiTenant] Created user: {name} ({tenant_id})")
            return tenant_id, True
        except sqlite3.IntegrityError:
            # Race condition — another worker created it. Re-read.
            user_row = conn.execute(
                "SELECT user_id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if user_row:
                return user_row["user_id"], False
            raise

    @staticmethod
    def _ensure_cv_profile(
        conn: sqlite3.Connection,
        tenant_id: str,
        name: str,
        profession: str,
        skills: str,
        experience_years: int,
        phone: str,
        email: str,
        linkedin: str,
    ) -> tuple[int, bool]:
        """Ensure a CV profile exists for the user in the cv_profiles table."""
        profile_row = conn.execute(
            "SELECT id FROM cv_profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (tenant_id,),
        ).fetchone()

        if profile_row:
            return profile_row["id"], False

        cv_text = TenantManager._generate_cv_text(
            name=name,
            profession=profession,
            skills=skills,
            experience_years=experience_years,
            phone=phone,
            email=email,
            linkedin=linkedin,
        )
        conn.execute(
            """
            INSERT INTO cv_profiles
            (user_id, target_titles, skills, experience_years,
             cv_text, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (tenant_id, profession, skills, experience_years, cv_text),
        )
        conn.commit()
        profile_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        logger.info(f"[MultiTenant] Created CV profile #{profile_id} for {name}")
        return profile_id, True

    @staticmethod
    def ensure_tenant(
        name: str,
        email: str,
        phone: str = "",
        linkedin: str = "",
        profession: str = "",
        skills: str = "",
        experience_years: int = 5,
        password: str = None,
    ) -> dict[str, Any]:
        """
        Ensure a tenant exists in the users table and their CV profile
        exists in cv_profiles. Auto-creates if missing.

        Returns: {"tenant_id": str, "profile_id": int, "created": bool}
        """
        conn = _get_conn()
        try:
            tenant_id, created_user = TenantManager._ensure_user_record(
                conn, name, email, phone, password
            )
            profile_id, created_profile = TenantManager._ensure_cv_profile(
                conn, tenant_id, name, profession, skills, experience_years, phone, email, linkedin
            )
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
    def _generate_cv_text(
        name: str,
        profession: str,
        skills: str,
        experience_years: int,
        phone: str = "",
        email: str = "",
        linkedin: str = "",
    ) -> str:
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
• {experience_years}+ years in {profession.split("/")[0].strip()}
• Expertise in {skills[:200]}

EDUCATION
• Bachelor's Degree (Lebanon)

LANGUAGES
• Arabic (Native), English (Fluent), French (Intermediate)
"""
        return cv.strip()

    @staticmethod
    def list_tenants() -> list[dict[str, Any]]:
        """List all tenants with a CV profile."""
        conn = _get_conn()
        try:
            rows = conn.execute("""
                SELECT u.user_id, u.name, u.email, u.phone, u.created_at,
                       p.id AS profile_id, p.target_titles, p.skills,
                       p.experience_years
                FROM users u
                INNER JOIN cv_profiles p ON p.user_id = u.user_id
                GROUP BY u.user_id, u.name, u.email, u.phone, u.created_at,
                         p.id, p.target_titles, p.skills, p.experience_years
                ORDER BY u.created_at ASC
            """).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_tenant_stats(tenant_id: str) -> dict[str, Any]:
        """Get per-tenant campaign stats optimized in a single SQL query."""
        conn = _get_conn()
        try:
            row = conn.execute(
                """
                SELECT
                    u.name,
                    u.email,
                    (SELECT COUNT(*) FROM campaigns WHERE user_id = ?) AS total_campaigns,
                    (SELECT COUNT(*) FROM campaigns WHERE user_id = ? AND status IN ('pending','running')) AS active_campaigns,
                    (SELECT COUNT(*) FROM campaigns WHERE user_id = ? AND status = 'completed') AS completed_campaigns,
                    (SELECT COUNT(*) FROM campaign_emails ce JOIN campaigns c ON c.campaign_id = ce.campaign_id WHERE c.user_id = ? AND ce.status = 'sent') AS emails_sent,
                    (SELECT COALESCE(SUM(sent_count), 0) FROM campaigns WHERE user_id = ?) AS total_sent_count
                FROM users u
                WHERE u.user_id = ?
            """,
                (tenant_id, tenant_id, tenant_id, tenant_id, tenant_id, tenant_id),
            ).fetchone()

            if row:
                return {
                    "tenant_id": tenant_id,
                    "name": row["name"] or "Unknown",
                    "email": row["email"] or "Unknown",
                    "total_campaigns": row["total_campaigns"] or 0,
                    "active_campaigns": row["active_campaigns"] or 0,
                    "completed_campaigns": row["completed_campaigns"] or 0,
                    "emails_sent": row["emails_sent"] or 0,
                    "total_sent_count": row["total_sent_count"] or 0,
                }
            else:
                return {
                    "tenant_id": tenant_id,
                    "name": "Unknown",
                    "email": "Unknown",
                    "total_campaigns": 0,
                    "active_campaigns": 0,
                    "completed_campaigns": 0,
                    "emails_sent": 0,
                    "total_sent_count": 0,
                }
        finally:
            conn.close()

    @staticmethod
    def get_all_tenants_stats() -> list[dict[str, Any]]:
        """Get stats for all tenants in a single optimized query."""
        conn = _get_conn()
        try:
            rows = conn.execute("""
                SELECT
                    u.user_id,
                    u.name,
                    u.email,
                    COUNT(DISTINCT c.campaign_id) AS total_campaigns,
                    SUM(CASE WHEN c.status IN ('pending','running') THEN 1 ELSE 0 END) AS active_campaigns,
                    SUM(CASE WHEN c.status = 'completed' THEN 1 ELSE 0 END) AS completed_campaigns,
                    COALESCE(SUM(c.sent_count), 0) AS total_sent_count,
                    (
                        SELECT COUNT(*)
                        FROM campaign_emails ce
                        JOIN campaigns c2 ON c2.campaign_id = ce.campaign_id
                        WHERE c2.user_id = u.user_id AND ce.status = 'sent'
                    ) AS emails_sent
                FROM users u
                LEFT JOIN campaigns c ON c.user_id = u.user_id
                GROUP BY u.user_id, u.name, u.email, u.created_at
                ORDER BY u.created_at ASC
            """).fetchall()

            return [
                {
                    "tenant_id": r["user_id"],
                    "name": r["name"] or "Unknown",
                    "email": r["email"] or "Unknown",
                    "total_campaigns": r["total_campaigns"] or 0,
                    "active_campaigns": r["active_campaigns"] or 0,
                    "completed_campaigns": r["completed_campaigns"] or 0,
                    "emails_sent": r["emails_sent"] or 0,
                    "total_sent_count": r["total_sent_count"] or 0,
                }
                for r in rows
            ]
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

    def __init__(
        self, company_limit: int = 15, max_campaigns: int = 10, campaign_id: str = None
    ):
        self.company_limit = company_limit
        self.max_campaigns = max_campaigns
        self.campaign_id = campaign_id
        self.tenant_stats: dict[str, dict[str, Any]] = {}

    async def _get_active_campaigns(self) -> list[dict[str, Any]]:
        """
        Fetch all active campaigns, using the edge cache if enabled.

        Returns:
            A list of active campaign dictionaries.
        """
        campaigns = None
        from core.edge_cache import edge_cache

        if edge_cache.enabled:
            try:
                cached_data = await edge_cache.get("hydra_active_campaigns")
                if cached_data:
                    campaigns = json.loads(cached_data)
                    logger.info(
                        "[MultiTenant] Loaded active campaigns list from Upstash Redis cache."
                    )
            except Exception as cache_err:
                logger.warning(
                    f"Failed to read campaigns from Redis cache: {cache_err}"
                )

        if not campaigns:
            campaigns = self._fetch_all_active_campaigns()
            if edge_cache.enabled and campaigns:
                try:
                    await edge_cache.set(
                        "hydra_active_campaigns", json.dumps(campaigns), ex=120
                    )
                except Exception as cache_err:
                    logger.warning(
                        f"Failed to write campaigns to Redis cache: {cache_err}"
                    )

        if self.campaign_id:
            campaigns = [
                c for c in campaigns if c.get("campaign_id") == self.campaign_id
            ]

        return campaigns or []

    def _schedule_fair_campaigns(self, campaigns: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Group campaigns by tenant and apply fair-share scheduling to select campaigns.

        Args:
            campaigns: A list of candidate campaigns.

        Returns:
            A list of selected campaign dictionaries.
        """
        by_tenant: dict[str, list[dict]] = {}
        for c in campaigns:
            tid = c.get("user_id", "unknown")
            if tid not in by_tenant:
                by_tenant[tid] = []
            by_tenant[tid].append(c)

        selected_campaigns = []
        tenant_ids = list(by_tenant.keys())
        import random

        random.shuffle(tenant_ids)

        while len(selected_campaigns) < self.max_campaigns and tenant_ids:
            active_tenants = []
            for tid in tenant_ids:
                if by_tenant[tid]:
                    selected_campaigns.append(by_tenant[tid].pop(0))
                    if len(selected_campaigns) >= self.max_campaigns:
                        break
                    active_tenants.append(tid)
            tenant_ids = active_tenants

        return selected_campaigns

    async def _run_tenant_campaigns(self, tid: str, t_campaigns: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Execute campaigns for a specific tenant sequentially.

        Args:
            tid: The tenant ID.
            t_campaigns: A list of campaigns for this tenant.

        Returns:
            A dictionary containing execution results for the tenant.
        """
        tenant_result = {
            "tenant_id": tid,
            "campaigns": [],
            "total_sent": 0,
            "total_failed": 0,
        }
        for camp in t_campaigns:
            cid = camp["campaign_id"]
            engine_type = camp.get("engine_type", "piggyback")

            if engine_type == "cloud":
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
                    tenant_result["campaigns"].append(
                        {
                            "campaign_id": cid,
                            "result": camp_result,
                        }
                    )
                    if isinstance(camp_result, dict):
                        tenant_result["total_sent"] += camp_result.get("sent", 0)
                        tenant_result["total_failed"] += camp_result.get(
                            "failed", 0
                        )
                except Exception as e2:
                    safe_err = (
                        str(e2).encode("ascii", errors="replace").decode("ascii")
                    )
                    logger.error(
                        f"[MultiTenant] Full runner failed for cloud campaign {cid}: {safe_err}"
                    )
                    tenant_result["campaigns"].append(
                        {
                            "campaign_id": cid,
                            "error": str(e2),
                        }
                    )
            else:
                try:
                    from core.lightning_runner import run_campaign_lightning

                    camp_result = await run_campaign_lightning(
                        campaign_id=cid,
                        company_limit=self.company_limit,
                    )
                    tenant_result["campaigns"].append(
                        {
                            "campaign_id": cid,
                            "result": camp_result,
                        }
                    )
                    if isinstance(camp_result, dict):
                        tenant_result["total_sent"] += camp_result.get("sent", 0)
                        tenant_result["total_failed"] += camp_result.get(
                            "failed", 0
                        )
                except Exception as e:
                    safe_err = (
                        str(e).encode("ascii", errors="replace").decode("ascii")
                    )
                    logger.error(
                        f"[MultiTenant] Lightning runner failed for {cid}: {safe_err}"
                    )
                    tenant_result["campaigns"].append(
                        {
                            "campaign_id": cid,
                            "error": str(e),
                        }
                    )
        return tenant_result

    async def tick(self) -> dict[str, Any]:
        """
        Main multi-tenant tick:
        0. Auto-create campaigns for tenants with profiles but no active campaign
        1. Fetch ALL active campaigns across ALL users
        2. Group by tenant
        3. Run in parallel with asyncio.gather
        4. Aggregate results

        Returns:
            A dictionary containing summary statistics of the tick execution.
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

        # ── Step 0: Auto-create campaigns for tenants without one ──
        self._auto_create_campaigns()

        # ── Step 1: Fetch all active campaigns ──
        campaigns = await self._get_active_campaigns()

        if not campaigns:
            logger.info("[MultiTenant] No active campaigns across any tenant.")
            results["message"] = "No active campaigns found"
            return results

        logger.info(
            f"[MultiTenant] Found {len(campaigns)} active campaign(s) across tenants."
        )

        selected_campaigns = self._schedule_fair_campaigns(campaigns)

        logger.info(
            f"[MultiTenant] Selected {len(selected_campaigns)} campaign(s) for execution via fair scheduling."
        )

        # ── Step 2: Group selected campaigns by tenant_id ──
        tenant_campaigns: dict[str, list[dict]] = {}
        for c in selected_campaigns:
            tid = c.get("user_id", "unknown")
            if tid not in tenant_campaigns:
                tenant_campaigns[tid] = []
            tenant_campaigns[tid].append(c)

        results["tenant_count"] = len(tenant_campaigns)

        # Execute tenants SEQUENTIALLY (PA free tier - avoid timeout)
        tenant_results = []
        for tid, t_campaigns in tenant_campaigns.items():
            try:
                tr = await self._run_tenant_campaigns(tid, t_campaigns)
                tenant_results.append(tr)
            except Exception as e:
                logger.error(f"[MultiTenant] Tenant {tid} crashed: {e}")
                tenant_results.append(e)

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
            with contextlib.suppress(Exception):
                self.tenant_stats[tid] = TenantManager.get_tenant_stats(tid)

        return results

    def _fetch_all_active_campaigns(self) -> list[dict[str, Any]]:
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

    def _auto_create_campaigns(self):
        """Auto-create campaigns for tenants that have a profile but no active campaign."""
        conn = _get_conn()
        try:
            # Find tenants (users with profiles) that have no active campaign
            # Using NOT EXISTS instead of LEFT JOIN/GROUP BY for PostgreSQL compatibility
            rows = conn.execute("""
                SELECT u.user_id, u.name, p.id AS profile_id, p.target_titles, p.target_locations
                FROM users u
                INNER JOIN cv_profiles p ON p.user_id = u.user_id
                WHERE NOT EXISTS (
                    SELECT 1 FROM campaigns c
                    WHERE c.user_id = u.user_id
                    AND c.status IN ('pending','running')
                )
            """).fetchall()

            for row in rows:
                tid = row["user_id"]
                profile_id = row["profile_id"]
                name = row["name"]
                titles = row["target_titles"] or "Professional"
                row["target_locations"] or "Lebanon"

                # Create a default campaign
                campaign_id = f"auto_{uuid.uuid4().hex[:12]}"
                job_title = titles.split(",")[0].strip() if titles else "Professional"

                conn.execute(
                    """
                    INSERT INTO campaigns (campaign_id, user_id, order_id, profile_id,
                    status, total_companies, sent_count, created_at, bouquets, engine_type)
                    VALUES (?, ?, ?, ?, 'pending', 100, 0, CURRENT_TIMESTAMP, 'Priority Shield', 'cloud')
                """,
                    (campaign_id, tid, f"auto_{tid[:8]}", profile_id),
                )
                conn.commit()
                logger.info(
                    f"[MultiTenant] Auto-created campaign {campaign_id} for {name} ({job_title})"
                )
        except Exception as e:
            logger.error(f"[MultiTenant] Auto-create campaigns error: {e}")
        finally:
            conn.close()

    # ── Per-tenant SMTP pool (each tenant gets their own rotation) ──

    @staticmethod
    def get_tenant_smtp_provider(tenant_id: str, config_module=None) -> dict | None:
        """
        Returns an SMTP provider for a given tenant. If the tenant has their own
        credentials configured (via demo_user_* env vars for demo_user, or env vars like
        TENANT_<ID>_SMTP_USER etc.), use those. Otherwise falls back to the
        default pool shared by all tenants.

        Per-tenant SMTP caps are enforced based on the provider's daily_limit.
        """
        # 0. Check database for tenant's BYO SMTP credentials
        conn = _get_conn()
        user_row = None
        byo_email = None
        byo_token = None
        try:
            row = conn.execute(
                "SELECT email, byo_smtp_email, byo_smtp_token FROM users WHERE user_id = ?",
                (tenant_id,),
            ).fetchone()
            if row:
                user_row = dict(row)
                byo_email = user_row.get("byo_smtp_email")
                byo_token = user_row.get("byo_smtp_token")
        except Exception as db_err:
            logger.warning(f"Failed to query BYO SMTP for tenant {tenant_id}: {db_err}")
            # Fallback to query only email for compatibility (e.g. standard SQLite test tables)
            try:
                row = conn.execute(
                    "SELECT email FROM users WHERE user_id = ?", (tenant_id,)
                ).fetchone()
                if row:
                    user_row = dict(row)
            except Exception:
                pass
        finally:
            conn.close()

        if user_row and byo_email and byo_token:
            try:
                # Decode character shift-13 token
                decoded = "".join(chr(ord(c) - 13) for c in byo_token)
                parts = decoded.split(":")
                email_part = parts[0]
                password_part = ":".join(parts[1:])
                if email_part and password_part:
                    domain = byo_email.split("@")[-1].lower()
                    host = "smtp.gmail.com"
                    if (
                        "outlook" in domain
                        or "hotmail" in domain
                        or "live" in domain
                    ):
                        host = "smtp-mail.outlook.com"
                    elif "yahoo" in domain:
                        host = "smtp.mail.yahoo.com"

                    return {
                        "name": f"{tenant_id}_byo_smtp",
                        "server": host,
                        "port": 587,
                        "user": byo_email,
                        "password": password_part,
                        "daily_limit": 100,
                        "weight": 10,
                    }
            except Exception as decode_err:
                logger.error(
                    f"[MultiTenant] Failed to decode user SMTP: {decode_err}"
                )

        # Check if this is a known tenant with custom SMTP config
        if tenant_id.startswith("user_"):
            if user_row:
                # 1. General tenant SMTP detection via env vars
                env_id = tenant_id.upper().replace("-", "_").replace(".", "_")
                tenant_smtp_user = os.getenv(f"TENANT_{env_id}_SMTP_USER", "")
                tenant_smtp_pass = os.getenv(f"TENANT_{env_id}_SMTP_PASS", "")
                if tenant_smtp_user and tenant_smtp_pass:
                    return {
                        "name": f"{tenant_id}_tenant",
                        "server": os.getenv(
                            f"TENANT_{env_id}_SMTP_SERVER", "smtp.gmail.com"
                        ),
                        "port": int(os.getenv(f"TENANT_{env_id}_SMTP_PORT", "587")),
                        "user": tenant_smtp_user,
                        "password": tenant_smtp_pass,
                        "daily_limit": int(
                            os.getenv(f"TENANT_{env_id}_SMTP_LIMIT", "100")
                        ),
                        "weight": 2,
                    }

                tenant_email = user_row["email"] or ""
                if (
                    "demo_useruser" in tenant_email.lower()
                    or "demo_user.user" in tenant_email.lower()
                ):
                    logger.warning(
                        "[MultiTenant] Demo User is deactivated. Blocking SMTP rotation for this tenant."
                    )
                    return None

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
                idx = (seed + int(time.time() / 60)) % len(
                    available
                )  # rotate every minute
                return available[idx]

        return None


# ══════════════════════════════════════════════════════════════════════════════
#  AUTO-SEED: Ensure Sam Salameh exists in DB
# ══════════════════════════════════════════════════════════════════════════════


def _auto_seed_sam():
    """
    Called on module import.
    Ensures Sam Salameh exists in the DB.
    """
    try:
        result = TenantManager.ensure_tenant(
            name=SAM_SALAMEH_PROFILE["tenant_name"],
            email=SAM_SALAMEH_PROFILE["email"],
            phone=SAM_SALAMEH_PROFILE["phone"],
            linkedin=SAM_SALAMEH_PROFILE["linkedin"],
            profession=SAM_SALAMEH_PROFILE["profession"],
            skills=SAM_SALAMEH_PROFILE["skills"],
            experience_years=SAM_SALAMEH_PROFILE["experience_years"],
        )
        if result.get("created_user") or result.get("created_profile"):
            logger.info(
                f"[MultiTenant] ✅ Auto-seeded Sam Salameh: "
                f"tenant={result['tenant_id']}, profile={result['profile_id']}"
            )
    except Exception as e:
        logger.error(f"[MultiTenant] ⚠️ Failed to auto-seed Sam Salameh: {e}")


# Run on import (safe — idempotent)
_auto_seed_sam()


# ══════════════════════════════════════════════════════════════════════════════
#  API ENDPOINTS (FastAPI Router)
# ══════════════════════════════════════════════════════════════════════════════


def verify_system_key(request: Request):
    """Verify that the request has the correct CRON_SECRET or session admin privileges."""
    from web.app_v2 import verify_system_key as vsk

    return vsk(request)


@router.get("/multi-tenant/status")
async def multi_tenant_status(request: Request):
    """
    Show all tenants and their campaign stats (fully optimized, 1 query).
    """
    verify_system_key(request)
    try:
        stats = TenantManager.get_all_tenants_stats()
        return {
            "status": "ok",
            "tenant_count": len(stats),
            "tenants": stats,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"[MultiTenant] Status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-tenant/add-tenant")
async def add_tenant(request: Request):
    """
    Add a new tenant via API.
    """
    verify_system_key(request)
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
        body.get("target_locations", "Lebanon")
        body.get("target_salary", "")
        body.get("target_companies", "")

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
            conn.execute(
                """
                UPDATE cv_profiles SET
                    target_titles = ?,
                    skills = ?
                WHERE user_id = ? AND id = ?
            """,
                (target_titles, skills, result["tenant_id"], result["profile_id"]),
            )
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


@router.get("/multi-tenant/sam")
async def get_sam_profile(request: Request):
    """
    Return Sam Salameh's pre-configured profile and stats.
    """
    verify_system_key(request)
    try:
        conn = _get_conn()
        user_row = conn.execute(
            "SELECT user_id FROM users WHERE email = ?", (SAM_SALAMEH_PROFILE["email"],)
        ).fetchone()
        conn.close()

        if not user_row:
            return {
                "status": "error",
                "message": "Sam Salameh not found in DB. Run seed first.",
            }

        tid = user_row["user_id"]
        stats = TenantManager.get_tenant_stats(tid)
        return {
            "status": "ok",
            "profile": SAM_SALAMEH_PROFILE,
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multi-tenant/debug-db")
async def debug_db(request: Request):
    """
    Return a snapshot of the database users, profiles, and campaigns for live diagnostics.
    Only accessible if DEBUG=1 or DEBUG=true is set in environment variables.
    """
    verify_system_key(request)
    if os.getenv("DEBUG", "").lower() not in ("1", "true"):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Diagnostics endpoint is only active in debug mode.",
        )

    conn = _get_conn()
    try:
        users = [
            dict(r)
            for r in conn.execute(
                "SELECT user_id, email, name, phone, created_at FROM users"
            ).fetchall()
        ]
        profiles = [
            dict(r)
            for r in conn.execute(
                "SELECT id, user_id, target_titles, target_locations, skills, experience_years FROM cv_profiles"
            ).fetchall()
        ]
        campaigns = [
            dict(r)
            for r in conn.execute(
                "SELECT campaign_id, user_id, status, total_companies, sent_count, created_at, engine_type FROM campaigns"
            ).fetchall()
        ]
        return {
            "status": "ok",
            "users": users,
            "profiles": profiles,
            "campaigns": campaigns,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        conn.close()


@router.post("/multi-tenant/cleanup-db")
async def cleanup_db(request: Request):
    """
    Scrubs the database of all non-Sam users/profiles/campaigns.
    Ensures Sam's CV profile has correct target titles and locations.
    """
    verify_system_key(request)
    conn = _get_conn()
    try:
        allowed_emails = ("samsalameh.cv@gmail.com", "samatou683@gmail.com")

        # Find all user_ids that are NOT Sam
        rows = conn.execute("SELECT user_id, email FROM users").fetchall()
        to_delete_user_ids = []
        for r in rows:
            if r["email"] not in allowed_emails:
                to_delete_user_ids.append(r["user_id"])

        deleted_campaigns = 0
        deleted_profiles = 0
        deleted_users = 0
        deleted_emails = 0

        for uid in to_delete_user_ids:
            camps = conn.execute(
                "SELECT campaign_id FROM campaigns WHERE user_id = ?", (uid,)
            ).fetchall()
            for c in camps:
                cid = c["campaign_id"]
                ce = conn.execute(
                    "DELETE FROM campaign_emails WHERE campaign_id = ?", (cid,)
                )
                deleted_emails += ce.rowcount

            c = conn.execute("DELETE FROM campaigns WHERE user_id = ?", (uid,))
            deleted_campaigns += c.rowcount

            p = conn.execute("DELETE FROM cv_profiles WHERE user_id = ?", (uid,))
            deleted_profiles += p.rowcount

            u = conn.execute("DELETE FROM users WHERE user_id = ?", (uid,))
            deleted_users += u.rowcount

        # Verify and optimize Sam Salameh's CV profiles
        sam_rows = conn.execute(
            "SELECT user_id, email FROM users WHERE email IN ('samsalameh.cv@gmail.com', 'samatou683@gmail.com')"
        ).fetchall()

        for sr in sam_rows:
            uid = sr["user_id"]
            # Check if he has a CV profile
            p_row = conn.execute(
                "SELECT id, target_titles, target_locations FROM cv_profiles WHERE user_id = ?",
                (uid,),
            ).fetchone()
            if p_row:
                # Update his profile to have correct titles and locations if they are empty or basic
                conn.execute(
                    """
                    UPDATE cv_profiles SET
                        target_titles = 'network engineer, senior network engineer, network administrator',
                        target_locations = 'lebanon, uae, dubai, qatar, saudi arabia, remote',
                        skills = 'cisco, mikrotik, fortinet, juniper, bgp, ospf, vpn, firewalls, linux, python',
                        experience_years = 15
                    WHERE id = ?
                """,
                    (p_row["id"],),
                )
            else:
                # Insert a default CV profile for him
                conn.execute(
                    """
                    INSERT INTO cv_profiles (user_id, target_titles, target_locations, skills, experience_years, cv_text, created_at)
                    VALUES (?, 'network engineer, senior network engineer, network administrator', 'lebanon, uae, dubai, qatar, saudi arabia, remote',
                            'cisco, mikrotik, fortinet, juniper, bgp, ospf, vpn, firewalls, linux, python', 15,
                            'Sam Salameh | Senior Network Engineer | 15+ years experience | CCNA, CCNP, MikroTik MTCNA', CURRENT_TIMESTAMP)
                """,
                    (uid,),
                )

        conn.commit()
        return {
            "status": "ok",
            "message": f"Successfully deleted {deleted_users} users, {deleted_profiles} profiles, {deleted_campaigns} campaigns, and {deleted_emails} emails. Confirmed Sam Salameh's profile is fully optimized.",
        }
    except Exception as e:
        conn.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  CONVENIENCE: Direct runner for PA tick replacement
# ══════════════════════════════════════════════════════════════════════════════


async def run_multi_tenant_tick(company_limit: int = 15) -> dict[str, Any]:
    """Convenience function — call from cloud_orchestrator or app router."""
    runner = MultiTenantRunner(company_limit=company_limit, max_campaigns=10)
    return await runner.tick()

