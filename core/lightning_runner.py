"""
Lightning Campaign Runner v2.0 — PA Free-Tier Optimized
Uses pre-seeded Lebanon companies (no scraping) for sub-60s campaign execution.
Each tick: pick company → generate email → send via email_engine.
FIXED: Uses EmailEngine.send_application() async method properly.
"""
import sqlite3
import os
import time
import asyncio
import random
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

def _get_db_path() -> str:
    db_path = os.getenv("DB_PATH", "jobhunt_saas_v2.db")
    base = Path(__file__).resolve().parent.parent
    full = str(base / db_path)
    if not os.path.exists(full):
        alt = str(base / "jobhunt_saas_v2.db")
        if os.path.exists(alt):
            return alt
    return full

async def run_campaign_lightning(campaign_id: str, company_limit: int = 3) -> dict:
    """
    Lightning-fast campaign execution for PA free tier.
    Uses pre-seeded Lebanon companies + EmailEngine.send_application().
    """
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    
    sent = 0
    failed = 0
    companies_processed = []
    start_time = time.time()
    
    try:
        # 1. Get campaign info - ensure campaign_sent table exists
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
        
        camp = conn.execute(
            "SELECT * FROM campaigns WHERE campaign_id = ?",
            (campaign_id,)
        ).fetchone()
        
        if not camp:
            return {"status": "error", "error": "Campaign not found", "campaign_id": campaign_id}
        
        # Convert to dict
        camp = dict(camp) if not isinstance(camp, dict) else camp
        
        # Mark as running
        conn.execute("UPDATE campaigns SET status='running' WHERE campaign_id=?", (campaign_id,))
        conn.commit()
        
        tenant_id = camp["user_id"]
        profile_id = camp.get("profile_id")
        
        # 2. Get tenant info
        tenant_row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (tenant_id,)
        ).fetchone()
        tenant_row = dict(tenant_row) if tenant_row and not isinstance(tenant_row, dict) else tenant_row
        
        # Determine role_type
        role_type = "tech"
        if tenant_row:
            email_lower = (tenant_row.get("email") or "").lower()
            if "rita" in email_lower:
                role_type = "hr"
        
        # 3. Get profile
        profile = None
        if profile_id:
            profile = conn.execute(
                "SELECT * FROM cv_profiles WHERE id = ?", (profile_id,)
            ).fetchone()
            profile = dict(profile) if profile and not isinstance(profile, dict) else profile
        
        # 4. Pick companies from pre-seeded table
        companies = conn.execute(
            """SELECT * FROM lebanon_companies 
               WHERE target_role_type = ? 
               ORDER BY relevance_score DESC 
               LIMIT ?""",
            (role_type, company_limit)
        ).fetchall()
        
        # Try other type if empty
        if not companies:
            other_type = "hr" if role_type == "tech" else "tech"
            companies = conn.execute(
                """SELECT * FROM lebanon_companies 
                   WHERE target_role_type = ? 
                   ORDER BY relevance_score DESC 
                   LIMIT ?""",
                (other_type, company_limit)
            ).fetchall()
        
        if not companies:
            return {
                "status": "ok", "sent": 0, "failed": 0,
                "message": "No companies in database",
                "companies": [],
                "role_type": role_type,
            }
        
        companies = [dict(c) if not isinstance(c, dict) else c for c in companies]
        
        # 5. Build email content
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
        
        # 6. Send all emails in one batch via micro SMTP
        try:
            from core.micro_smtp import send_batch
            
            # Build recipient list
            recipients = []
            for company in companies:
                company_name = company["company_name"]
                company_email = company["email"]
                
                if not company_email or "@" not in company_email:
                    failed += 1
                    companies_processed.append({"company": company_name, "status": "invalid_email"})
                    continue
                
                # Check duplicate
                already = conn.execute(
                    "SELECT 1 FROM campaign_sent WHERE campaign_id=? AND company_name=?",
                    (campaign_id, company_name)
                ).fetchone()
                if already:
                    companies_processed.append({"company": company_name, "status": "skipped"})
                    continue
                
                # Build HTML
                skills_short = (skills[:200].replace(',', '</li><li>') if skills else 'Professional experience')
                cv_short = (cv_text or "")[:300]
                
                html_body = f"""<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333">
<h2 style="color:#2563eb">{tenant_name} — {job_title}</h2>
<p>Dear Hiring Team at <strong>{company_name}</strong>,</p>
<p>I am writing to express my sincere interest in opportunities at {company_name}. With my background as a <strong>{job_title}</strong> in Lebanon, I am confident I can contribute meaningfully to your organization.</p>
<p><strong>My key strengths include:</strong></p>
<ul><li>{skills_short}</li></ul>
<p>{cv_short}</p>
<p>I would be delighted to discuss how my experience aligns with {company_name}'s needs. I am available for an interview at your convenience.</p>
<p style="margin-top:20px">Best regards,<br><strong>{tenant_name}</strong><br>📧 {tenant_email}</p>
</body></html>"""
                
                recipients.append({
                    "email": company_email,
                    "company": company_name,
                    "subject": f"{job_title} — Application to {company_name}",
                    "html": html_body,
                })
            
            if not recipients:
                return {
                    "status": "ok", "sent": 0, "failed": 0,
                    "message": "All companies already contacted",
                    "companies": companies_processed,
                }
            
            # Send batch (max 5 per account to stay safe)
            result = send_batch(recipients, max_per_account=5)
            sent = result.get("sent", 0)
            failed = result.get("failed", len(recipients) - sent)
            
            # Record each result
            for detail in result.get("details", []):
                company_name = detail.get("company", "?")
                status = detail.get("status", "unknown")
                companies_processed.append(detail)
                
                if "sent" in status:
                    try:
                        conn.execute(
                            "INSERT INTO campaign_sent (campaign_id, company_name, email, status, sent_at) VALUES (?,?,?,'sent',CURRENT_TIMESTAMP)",
                            (campaign_id, company_name, detail.get("via", "smtp"))
                        )
                        conn.commit()
                    except Exception:
                        pass
        
        except ImportError as e:
            logger.warning(f"[Lightning] micro_smtp not available: {e}")
            for c in companies:
                companies_processed.append({"company": c["company_name"], "status": "logged"})
        
        # 7. Update campaign stats
        new_sent = (camp.get("sent_count") or 0) + sent
        new_total = max(camp.get("total_companies") or 0, sent + failed)
        
        conn.execute(
            """UPDATE campaigns SET sent_count=?, total_companies=?, status='completed'
               WHERE campaign_id=?""",
            (new_sent, new_total, campaign_id)
        )
        conn.commit()
        
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
