"""
Lightning Campaign Runner v2.0 — PA Free-Tier Optimized
Uses pre-seeded Lebanon companies (no scraping) for sub-60s campaign execution.
Each tick: pick company → generate email → send via email_engine.
FIXED: Uses EmailEngine.send_application() async method properly.
"""

import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

if os.getenv("FORCE_PG") == "1" or os.getenv("CLOUD_MODE") == "true":
    import core.pg_sqlite_shim as sqlite3
else:
    import sqlite3

from core.anti_ban import anti_ban

logger = logging.getLogger(__name__)

__all__ = ["run_campaign_lightning"]


# ── DB Helpers ─────────────────────────────────────────────────────────────

def _get_db_path() -> str:
    """Return the absolute path to the primary SQLite database."""
    db_path = os.getenv("DB_PATH", "jobhunt_saas_v2.db")
    base = Path(__file__).resolve().parent.parent
    full = str(base / db_path)
    if not os.path.exists(full):
        alt = str(base / "jobhunt_saas_v2.db")
        if os.path.exists(alt):
            return alt
    return full


def _ensure_campaign_sent_table(conn: Any) -> None:
    """Ensure the campaign_sent tracking table exists."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS campaign_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id TEXT,
            company_name TEXT,
            email TEXT,
            status TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


# ── Campaign Setup ─────────────────────────────────────────────────────────

def _load_campaign(conn: Any, campaign_id: str) -> dict | None:
    """Fetch and mark campaign as running. Returns dict or None if missing."""
    camp = conn.execute(
        "SELECT * FROM campaigns WHERE campaign_id = ?", (campaign_id,)
    ).fetchone()
    if not camp:
        return None
    camp = dict(camp) if not isinstance(camp, dict) else camp
    conn.execute(
        "UPDATE campaigns SET status='running' WHERE campaign_id=?", (campaign_id,)
    )
    conn.commit()
    return camp


def _determine_role_type(tenant_row: dict | None) -> str:
    """Infer role type (tech/hr) from tenant email."""
    if tenant_row:
        email_lower = (tenant_row.get("email") or "").lower()
        if "demo_user" in email_lower:
            return "hr"
    return "tech"


def _load_tenant_and_profile(
    conn: Any, camp: dict
) -> tuple[dict | None, dict | None, str]:
    """Return (tenant_row, profile, role_type) for a campaign."""
    tenant_id = camp["user_id"]
    profile_id = camp.get("profile_id")

    tenant_row = conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (tenant_id,)
    ).fetchone()
    tenant_row = (
        dict(tenant_row) if tenant_row and not isinstance(tenant_row, dict) else tenant_row
    )

    profile = None
    if profile_id:
        profile = conn.execute(
            "SELECT * FROM cv_profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        profile = dict(profile) if profile and not isinstance(profile, dict) else profile

    role_type = _determine_role_type(tenant_row)
    return tenant_row, profile, role_type


# ── Company Selection ──────────────────────────────────────────────────────

def _pick_companies(
    conn: Any, campaign_id: str, role_type: str, company_limit: int
) -> list[dict]:
    """
    Select up to company_limit companies not yet contacted by this campaign.

    Falls back to the opposite role type if no companies remain for the primary type.
    """
    def _query(rtype: str) -> list[dict]:
        rows = conn.execute(
            """SELECT lc.* FROM lebanon_companies lc
               WHERE lc.target_role_type = ?
               AND lc.company_name NOT IN (
                   SELECT company_name FROM campaign_sent WHERE campaign_id = ?
               )
               ORDER BY lc.relevance_score DESC
               LIMIT ?""",
            (rtype, campaign_id, company_limit),
        ).fetchall()
        return [dict(r) if not isinstance(r, dict) else r for r in rows]

    companies = _query(role_type)
    if not companies:
        other = "hr" if role_type == "tech" else "tech"
        companies = _query(other)
    return companies


# ── Email Building ─────────────────────────────────────────────────────────

def _build_email_html(
    tenant_name: str,
    tenant_email: str,
    job_title: str,
    company_name: str,
    skills: str,
    cv_text: str,
) -> str:
    """Render the application email HTML body."""
    skills_short = (
        skills[:200].replace(",", "</li><li>") if skills else "Professional experience"
    )
    cv_short = (cv_text or "")[:300]
    return f"""<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333">
<h2 style="color:#2563eb">{tenant_name} — {job_title}</h2>
<p>Dear Hiring Team at <strong>{company_name}</strong>,</p>
<p>I am writing to express my sincere interest in opportunities at {company_name}. With my background as a <strong>{job_title}</strong> in Lebanon, I am confident I can contribute meaningfully to your organization.</p>
<p><strong>My key strengths include:</strong></p>
<ul><li>{skills_short}</li></ul>
<p>{cv_short}</p>
<p>I would be delighted to discuss how my experience aligns with {company_name}'s needs. I am available for an interview at your convenience.</p>
<p style="margin-top:20px">Best regards,<br><strong>{tenant_name}</strong><br>📧 {tenant_email}</p>
</body></html>"""


def _build_recipient_list(
    companies: list[dict],
    tenant_id: str,
    tenant_name: str,
    tenant_email: str,
    job_title: str,
    skills: str,
    cv_text: str,
) -> tuple[list[dict], list[dict]]:
    """
    Filter companies through anti-ban checks and build the SMTP recipient list.

    Returns:
        (recipients, rejected_entries) where rejected_entries are dicts for companies_processed.
    """
    recipients: list[dict] = []
    rejected: list[dict] = []

    for company in companies:
        company_name = company["company_name"]
        company_email = company["email"]

        if not company_email or "@" not in company_email:
            rejected.append({"company": company_name, "status": "invalid_email"})
            continue

        if anti_ban.is_honeypot(company_email, company_name, ""):
            rejected.append({"company": company_name, "status": "failed", "reason": "honeypot"})
            continue

        can_apply, reason = anti_ban.can_apply_to_company(company_name, user_id=tenant_id)
        if not can_apply:
            rejected.append({"company": company_name, "status": "skipped", "reason": f"rate_limited: {reason}"})
            continue

        if anti_ban.should_blacklist_company(company_name, user_id=tenant_id):
            rejected.append({"company": company_name, "status": "failed", "reason": "blacklisted"})
            continue

        html_body = _build_email_html(tenant_name, tenant_email, job_title, company_name, skills, cv_text)
        recipients.append({
            "email": company_email,
            "company": company_name,
            "subject": f"{job_title} — Application to {company_name}",
            "html": html_body,
        })

    return recipients, rejected


# ── Record Keeping ─────────────────────────────────────────────────────────

def _record_sent_application(
    conn: Any,
    campaign_id: str,
    tenant_id: str,
    job_title: str,
    company_name: str,
    detail: dict,
) -> None:
    """Persist a successfully-sent application to campaign_sent and jobs tables."""
    try:
        conn.execute(
            "INSERT INTO campaign_sent (campaign_id, company_name, email, status, sent_at) VALUES (?,?,?,'sent',CURRENT_TIMESTAMP)",
            (campaign_id, company_name, detail.get("via", "smtp")),
        )
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        has_user_id = True
        try:
            conn.execute("SELECT user_id FROM jobs LIMIT 1")
        except Exception:
            has_user_id = False

        if has_user_id:
            conn.execute(
                """INSERT INTO jobs
                (job_id, user_id, title, company, email, location, url, source, snippet, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'applied', datetime('now'), datetime('now'))""",
                (job_id, tenant_id, job_title, company_name, detail.get("email", ""), "Lebanon", "", "lightning_campaign",
                 f"Applied via Lightning Campaign {campaign_id}"),
            )
        else:
            conn.execute(
                """INSERT INTO jobs
                (job_id, title, company, email, location, url, source, snippet, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'applied', datetime('now'), datetime('now'))""",
                (job_id, job_title, company_name, detail.get("email", ""), "Lebanon", "", "lightning_campaign",
                 f"Applied via Lightning Campaign {campaign_id}"),
            )
        conn.commit()
        anti_ban.record_application(company_name, user_id=tenant_id)
    except Exception as ex:
        logger.error(f"[Lightning] Failed to record successful application: {ex}")


def _finalize_campaign(conn: Any, camp: dict, campaign_id: str, sent: int, failed: int, company_limit: int, companies: list) -> None:
    """Update campaign status and counters in DB."""
    new_sent = (camp.get("sent_count") or 0) + sent
    new_total = max(camp.get("total_companies") or 0, sent + failed)
    target_limit = camp.get("total_companies") or 100
    has_more = (len(companies) >= company_limit) and (new_sent < target_limit)

    if has_more:
        conn.execute(
            """UPDATE campaigns SET sent_count=?, total_companies=?, status='pending'
               WHERE campaign_id=?""",
            (new_sent, new_total, campaign_id),
        )
        logger.info(f"[Lightning] Campaign {campaign_id} updated: sent={new_sent}/{new_total}, status remains pending")
    else:
        conn.execute(
            """UPDATE campaigns SET sent_count=?, total_companies=?, status='completed', completed_at=CURRENT_TIMESTAMP
               WHERE campaign_id=?""",
            (new_sent, new_total, campaign_id),
        )
        logger.info(f"[Lightning] Campaign {campaign_id} COMPLETED: sent={new_sent}/{new_total}")
    conn.commit()


# ── Public Entry Point ─────────────────────────────────────────────────────

async def run_campaign_lightning(campaign_id: str, company_limit: int = 3) -> dict:
    """
    Lightning-fast campaign execution for PA free tier.

    Uses pre-seeded Lebanon companies + micro_smtp batch sender.
    Each call processes up to ``company_limit`` companies and marks the campaign
    as 'pending' if more companies remain, or 'completed' otherwise.

    Args:
        campaign_id: UUID of the campaign row to execute.
        company_limit: Max companies to contact per tick (default 3).

    Returns:
        Result dict with keys: status, sent, failed, companies, elapsed_sec, role_type.
    """
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row

    sent = 0
    failed = 0
    companies_processed: list[dict] = []
    start_time = time.time()

    try:
        _ensure_campaign_sent_table(conn)

        camp = _load_campaign(conn, campaign_id)
        if not camp:
            return {"status": "error", "error": "Campaign not found", "campaign_id": campaign_id}

        tenant_id = camp["user_id"]
        tenant_row, profile, role_type = _load_tenant_and_profile(conn, camp)
        companies = _pick_companies(conn, campaign_id, role_type, company_limit)

        if not companies:
            return {
                "status": "ok", "sent": 0, "failed": 0,
                "message": "No companies in database",
                "companies": [], "role_type": role_type,
            }

        tenant_name = tenant_row.get("name", "Candidate") if tenant_row else "Candidate"
        tenant_email = tenant_row.get("email", "samatou683@gmail.com") if tenant_row else "samatou683@gmail.com"
        job_title = "Professional"
        if profile:
            titles = (profile.get("target_titles") or "").strip()
            if titles:
                job_title = titles.split(",")[0].strip()

        skills = (profile.get("skills") or "") if profile else ""
        cv_text = (profile.get("cv_text") or "") if profile else ""

        logger.info(f"[Lightning v3] Campaign {campaign_id}: {len(companies)} companies ({role_type}) - {tenant_name}")

        try:
            from core.micro_smtp import send_batch

            recipients, rejected = _build_recipient_list(
                companies, tenant_id, tenant_name, tenant_email, job_title, skills, cv_text
            )
            companies_processed.extend(rejected)
            failed += len(rejected)

            if not recipients:
                return {
                    "status": "ok", "sent": 0, "failed": failed,
                    "message": "All companies already contacted or filtered by anti-ban",
                    "companies": companies_processed,
                }

            result = send_batch(recipients, max_per_account=5, tenant_id=tenant_id, from_name=tenant_name)
            sent = result.get("sent", 0)
            failed += result.get("failed", len(recipients) - sent)

            for detail in result.get("details", []):
                cname = detail.get("company", "?")
                status = detail.get("status", "unknown")
                companies_processed.append(detail)
                if "sent" in status:
                    _record_sent_application(conn, campaign_id, tenant_id, job_title, cname, detail)
                else:
                    try:
                        anti_ban.record_failure(cname, user_id=tenant_id)
                    except Exception as ex:
                        logger.error(f"[Lightning] Failed to record failed application: {ex}")

        except ImportError as e:
            logger.warning(f"[Lightning] micro_smtp not available: {e}")
            companies_processed.extend({"company": c["company_name"], "status": "logged"} for c in companies)

        _finalize_campaign(conn, camp, campaign_id, sent, failed, company_limit, companies)
        elapsed = time.time() - start_time

        return {
            "status": "ok",
            "campaign_id": campaign_id,
            "sent": sent,
            "failed": failed,
            "total_companies": len(companies),
            "companies": companies_processed,
            "elapsed_sec": round(elapsed, 2),
            "role_type": role_type,
        }

    except Exception as e:
        logger.error(f"[Lightning] Fatal error: {e}", exc_info=True)
        return {"status": "error", "error": str(e), "campaign_id": campaign_id}
    finally:
        try:
            conn.close()
        except Exception:
            pass
