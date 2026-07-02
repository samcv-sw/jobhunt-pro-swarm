import os
import logging
import uuid
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from web.app_v2 import get_db
from core.pricing_manager import PRICING_TIERS_MAP, BOUQUET_PACKAGES_MAP

router = APIRouter()
logger = logging.getLogger(__name__)

def get_verified_user_id(request: Request) -> str:
    from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
    import config
    SECRET_KEY = os.getenv("SECRET_KEY") or getattr(config, "SECRET_KEY", None)
    if not SECRET_KEY:
        return None
    session_serializer = URLSafeTimedSerializer(SECRET_KEY)
    cookie = request.cookies.get("user_id", "")
    if cookie:
        try:
            return session_serializer.loads(cookie, max_age=86400 * 30)
        except (BadSignature, SignatureExpired):
            pass
    try:
        session_user = request.session.get("user")
        if session_user and session_user.get("id"):
            return session_user["id"]
    except Exception:
        pass
    return None

@router.get("/new-campaign", response_class=HTMLResponse)
def new_campaign_page(request: Request):
    from web.app_v2 import render_template, _build_dashboard_shell, get_all_pricing
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    conn = get_db()
    profiles = [dict(r) for r in conn.execute("SELECT * FROM cv_profiles WHERE user_id = ?", (user_id,)).fetchall()]
    user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    if not user_row:
        return RedirectResponse("/login", status_code=303)
    user = dict(user_row)

    pricing_data = get_all_pricing()

    content = render_template("new_campaign_v2.html",
        user=user, user_id=user_id, active_page="new-campaign",
        profiles=profiles, pricing=pricing_data, balance=user["wallet_balance"]
    )
    return HTMLResponse(_build_dashboard_shell(user, user_id, content, "New Campaign", "new-campaign"))

@router.post("/api/v1/delete-cv-profile")
async def delete_cv_profile(request: Request):
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=401)
    
    try:
        data = await request.json()
        profile_id = data.get("profile_id")
        if not profile_id:
            return JSONResponse({"success": False, "message": "Missing profile_id"})
            
        conn = get_db()
        row = conn.execute("SELECT id FROM cv_profiles WHERE id=? AND user_id=?", (profile_id, user_id)).fetchone()
        if not row:
            conn.close()
            return JSONResponse({"success": False, "message": "Profile not found or unauthorized"})
            
        conn.execute("DELETE FROM cv_profiles WHERE id=? AND user_id=?", (profile_id, user_id))
        conn.commit()
        conn.close()
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)})

@router.post("/create-campaign")
@router.post("/api/campaigns")
def create_campaign(request: Request, profile_id: int = Form(...),
                          company_count: int = Form(0), bouquet: str = Form(""), bouquet_names: str = Form(""), engine_type: str = Form("cloud")):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    conn = get_db()
    user_row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user_row:
        conn.close()
        return RedirectResponse("/login", status_code=303)
    user = dict(user_row)

    tier = PRICING_TIERS_MAP.get(company_count)

    bouquet_price = 0
    bouquets_selected = []
    if bouquet:
        b_pkg = BOUQUET_PACKAGES_MAP.get(bouquet)
        if b_pkg:
            bouquet_price = b_pkg["price_usd"]
            bouquets_selected.append(bouquet)
            
    if bouquet_names:
        for bname in bouquet_names.split(","):
            bname = bname.strip()
            b_pkg = BOUQUET_PACKAGES_MAP.get(bname)
            if b_pkg:
                bouquet_price += b_pkg["price_usd"]
                bouquets_selected.append(bname)

    if not tier:
        conn.close()
        return RedirectResponse("/new-campaign", status_code=303)

    total_price = tier["price_usd"] + bouquet_price
    
    if user["wallet_balance"] < total_price:
        conn.close()
        return RedirectResponse("/wallet?error=insufficient_funds", status_code=303)

    campaign_id = f"camp_{uuid.uuid4().hex[:16]}"
    order_id = f"ord_{uuid.uuid4().hex[:16]}"

    try:
        conn.execute("BEGIN TRANSACTION")

        cursor = conn.execute("""
            UPDATE users 
            SET wallet_balance = wallet_balance - ?, 
                total_spent = total_spent + ? 
            WHERE user_id = ? AND wallet_balance >= ?
        """, (total_price, total_price, user_id, total_price))
        
        if cursor.rowcount == 0:
            conn.rollback()
            conn.close()
            return RedirectResponse("/wallet?error=insufficient_funds", status_code=303)
            
        new_balance = user["wallet_balance"] - total_price

        conn.execute("""INSERT INTO orders (order_id, user_id, order_type, package_name, company_count, amount_usd, payment_method, payment_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                     (order_id, user_id, "campaign", tier["tier"], company_count, total_price, "wallet", "completed"))
        
        bouquets_str = ",".join(bouquets_selected)
        conn.execute("""INSERT INTO campaigns (campaign_id, user_id, order_id, profile_id, total_companies, bouquets, engine_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                     (campaign_id, user_id, order_id, profile_id, company_count, bouquets_str, engine_type))

        conn.execute("""INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description)
                        VALUES (?, ?, ?, ?, ?)""",
                     (user_id, "spend", -total_price, new_balance, f"Campaign: {company_count} companies"))

        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"[DB] Transaction failed in create_campaign: {e}")
        conn.close()
        return HTMLResponse("Internal Server Error: Could not process transaction.", status_code=500)
    finally:
        conn.close()

    from core.job_queue import enqueue_task
    try:
        enqueue_task("run_campaign", {"campaign_id": campaign_id})
    except Exception as e:
        logger.error(f"[QUEUE] Error enqueuing campaign {campaign_id}: {e}")

    return RedirectResponse(f"/campaign/{campaign_id}?queued=1", status_code=303)

@router.get("/campaign/{campaign_id}", response_class=HTMLResponse)
def campaign_detail(request: Request, campaign_id: str):
    from web.app_v2 import render_template, _build_dashboard_shell
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    conn = get_db()
    campaign_row = conn.execute("SELECT * FROM campaigns WHERE campaign_id = ? AND user_id = ?",
                                 (campaign_id, user_id)).fetchone()
    if not campaign_row:
        conn.close()
        return RedirectResponse("/dashboard", status_code=303)
    campaign = dict(campaign_row)
    emails = [dict(r) for r in conn.execute(
        "SELECT * FROM campaign_emails WHERE campaign_id = ? ORDER BY sent_at DESC",
        (campaign_id,)).fetchall()]
    conn.close()

    content_html = render_template("campaign_detail.html", request=request,
        campaign=campaign, emails=emails)
    return HTMLResponse(_build_dashboard_shell(None, user_id, content_html, f"Campaign {campaign.get('campaign_name', 'Detail')}", "new-campaign"))

@router.get("/campaign/{campaign_id}/war-room", response_class=HTMLResponse)
def campaign_war_room(request: Request, campaign_id: str):
    from web.app_v2 import render_template, _build_dashboard_shell
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    conn = get_db()
    for col, typ in [("cover_html", "TEXT DEFAULT ''"), ("competition_score", "INTEGER DEFAULT 0"), ("followup_scheduled", "INTEGER DEFAULT 0")]:
        try:
            conn.execute(f"ALTER TABLE campaign_emails ADD COLUMN {col} {typ}")
            conn.commit()
        except Exception:
            pass  # column already exists
    campaign_row = conn.execute("SELECT * FROM campaigns WHERE campaign_id = ? AND user_id = ?",
                                 (campaign_id, user_id)).fetchone()
    if not campaign_row:
        conn.close()
        return RedirectResponse("/dashboard", status_code=303)
    campaign = dict(campaign_row)
    user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    user = dict(user_row) if user_row else {}
    emails = [dict(r) for r in conn.execute(
        "SELECT * FROM campaign_emails WHERE campaign_id = ? ORDER BY sent_at DESC",
        (campaign_id,)).fetchall()]
    conn.close()

    weapon_count = int(campaign.get("premium_weapons", 0) or 0)
    is_running = campaign.get("status", "") == "running"

    if weapon_count >= 14:
        weapon_badge = '<span class="wb-god">💀 GOD MODE V4 — 15/15 WEAPONS ACTIVE</span>'
    elif weapon_count >= 10:
        weapon_badge = f'<span class="wb-emperor">👑 EMPEROR — {weapon_count}/12 WEAPONS ACTIVE</span>'
    elif weapon_count >= 3:
        weapon_badge = f'<span class="wb-pro">🦅 PRO HUNTER V2 — {weapon_count}/5 WEAPONS ACTIVE</span>'
    elif weapon_count >= 1:
        weapon_badge = f'<span class="wb-starter">⚡ {weapon_count} WEAPON(S) ACTIVE</span>'
    else:
        weapon_badge = '<span class="wb-none">🔒 NO WEAPONS — Visit Premium Services to arm up</span>'

    progress_pct = min(100, int((weapon_count / 15) * 100))
    sent = sum(1 for e in emails if e.get("status") == "sent")
    failed = sum(1 for e in emails if e.get("status") in ("pending", "brevo_failed", "gmail_failed"))
    followups = sum(1 for e in emails if e.get("followup_scheduled"))

    comp_rows = []
    for e in emails:
        cs = int(e.get("competition_score") or 0)
        if cs:
            heat, heat_cls = (("FIRE HOT", "hot") if cs >= 80 else (("GOOD", "good") if cs >= 70 else ("COLD", "cold")))
            comp_rows.append({"company": e.get("company_name", "?"), "job_title": e.get("job_title", ""),
                "score": cs, "heat_label": heat, "heat_cls": heat_cls})

    linkedin_rows = [{"company": e.get("company_name", "?"), "job_title": e.get("job_title", ""),
        "message": (e.get("linkedin_message") or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}
        for e in emails if (e.get("linkedin_message") or "").strip()]

    interview_rows = [{"company": e.get("company_name", "?"), "job_title": e.get("job_title", ""),
        "prep": (e.get("interview_prep") or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}
        for e in emails if (e.get("interview_prep") or "").strip()]

    cover_rows = []
    for e in emails[:20]:
        ch = (e.get("cover_html") or "").strip()
        status = "SENT" if e.get("status") == "sent" else "FAILED"
        cover_rows.append({"company": e.get("company_name", "?"), "job_title": e.get("job_title", ""),
            "id": e.get("id"),
            "status": status, "status_cls": "sent" if status == "SENT" else "failed",
            "html": ch.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") if ch else "",
            "raw_html": ch if ch else "",
            "has_preview": bool(ch)})

    st = campaign.get("status", "")
    if st == "completed":
        actions = [{"sev": "crit", "label": "CRITICAL", "text": "Send follow-ups to non-responsive companies (Day 3/7/14)"},
                   {"sev": "high", "label": "HIGH", "text": "Send LinkedIn connection requests (open LinkedIn Station below)"},
                   {"sev": "high", "label": "HIGH", "text": "Practice interview questions per company (open Armory below)"},
                   {"sev": "med", "label": "MED", "text": "Launch a new campaign targeting different locations/roles"}]
    elif st == "running":
        actions = [{"sev": "info", "label": "INFO", "text": "Campaign is actively sending — this page auto-refreshes"}]
    elif st == "failed":
        actions = [{"sev": "crit", "label": "CRITICAL", "text": "Campaign failed — check error details and retry"}]
    else:
        actions = [{"sev": "info", "label": "INFO", "text": "Campaign pending — refresh when started"}]

    content = render_template("war_room.html",
        campaign_id=campaign_id,
        campaign={"cid": campaign_id[:12], "status": campaign.get("status", "?").upper(),
            "total_companies": campaign.get("total_companies", 0),
            "open_count": campaign.get("open_count", 0),
            "response_count": campaign.get("response_count", 0)},
        stats={"sent": sent, "failed": failed, "followups": followups},
        weapon_badge=weapon_badge, progress_pct=progress_pct,
        auto_refresh=is_running,
        comp_rows=comp_rows, linkedin_rows=linkedin_rows,
        interview_rows=interview_rows, cover_rows=cover_rows, actions=actions)
    user_dict = {"wallet_balance": user.get("wallet_balance", 0)}
    return HTMLResponse(_build_dashboard_shell(user_dict, user_id, content, "⚔️ War Room", "war-room"))

@router.post("/api/generate-interview-prep/{email_id}")
async def api_generate_interview_prep(request: Request, email_id: int):
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    conn = get_db()
    row = conn.execute("SELECT e.*, c.user_id FROM campaign_emails e JOIN campaigns c ON e.campaign_id = c.campaign_id WHERE e.id = ?", (email_id,)).fetchone()
    if not row or str(row["user_id"]) != str(user_id):
        conn.close()
        return JSONResponse({"error": "Not found"}, status_code=404)
    
    email_data = dict(row)
    
    if email_data.get("interview_prep"):
        conn.close()
        return {"success": True, "redirect": f"/interview-prep/{email_id}"}
        
    company = email_data.get("company_name", "the company")
    title = email_data.get("job_title", "the role")
    cover_letter = email_data.get("cover_html", "")
    
    profile_row = conn.execute("SELECT cv_text FROM cv_profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
    cv_text = profile_row["cv_text"] if profile_row and profile_row["cv_text"] else "No CV content provided."
    
    try:
        from core.agent_graph import run_interview_prep_graph
        import asyncio
        
        prep_html = await asyncio.to_thread(
            run_interview_prep_graph,
            company=company,
            job_title=title,
            cover_letter=cover_letter,
            cv_text=cv_text
        )
        
        conn.execute("UPDATE campaign_emails SET interview_prep = ? WHERE id = ?", (prep_html, email_id))
        conn.commit()
    except Exception as e:
        conn.close()
        return JSONResponse({"error": str(e)}, status_code=500)
        
    conn.close()
    return {"success": True, "redirect": f"/interview-prep/{email_id}"}

@router.get("/interview-prep/{email_id}", response_class=HTMLResponse)
def view_interview_prep(request: Request, email_id: int):
    from web.app_v2 import render_template, _build_dashboard_shell
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
        
    conn = get_db()
    row = conn.execute("SELECT * FROM campaign_emails WHERE id = ?", (email_id,)).fetchone()
    conn.close()
    if not row:
        return RedirectResponse("/dashboard", status_code=303)
        
    email_data = dict(row)
    
    content_html = render_template("interview_prep.html", request=request,
        campaign_id=email_data.get("campaign_id", ""),
        company=email_data.get("company_name", ""),
        job_title=email_data.get("job_title", ""),
        prep_content=email_data.get("interview_prep", "")
    )
    return HTMLResponse(_build_dashboard_shell(None, user_id, content_html, "Interview Prep", "interview-prep"))

@router.get("/battle-station", response_class=HTMLResponse)
def battle_station_page(request: Request):
    from web.app_v2 import render_template, _build_dashboard_shell
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    conn = get_db()
    
    campaigns = []
    running_count = paused_count = completed_count = failed_count = total_sent = total_responses = 0

    try:
        user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user_row:
            conn.close()
            return RedirectResponse("/login", status_code=303)
        user = dict(user_row)
        
        camp_rows = conn.execute("SELECT * FROM campaigns WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
        campaigns = [dict(c) for c in camp_rows]
        
        running_count = sum(1 for c in campaigns if c.get("status") == "running")
        paused_count = sum(1 for c in campaigns if c.get("status") == "paused")
        completed_count = sum(1 for c in campaigns if c.get("status") == "completed")
        failed_count = sum(1 for c in campaigns if c.get("status") in ("failed", "error"))
        
        total_sent = sum(int(c.get("sent_count") or 0) for c in campaigns)
        
        total_responses = conn.execute(
            "SELECT COUNT(*) FROM campaign_emails ce JOIN campaigns c ON ce.campaign_id = c.campaign_id WHERE c.user_id = ? AND ce.responded_at IS NOT NULL",
            (user_id,)
        ).fetchone()[0]
    except Exception as e:
        logger.error(f"Error in /battle-station query for user {user_id}: {e}", exc_info=True)
        user = {}
    finally:
        conn.close()
    content = render_template("battle_station.html", request=request,
                              campaigns=campaigns, running_count=running_count,
                              paused_count=paused_count, completed_count=completed_count,
                              failed_count=failed_count, total_sent=total_sent, total_responses=total_responses)
    return HTMLResponse(_build_dashboard_shell(user, user_id, content, "&#x2694;&#xFE0F; Battle Station", "battle-station"))
