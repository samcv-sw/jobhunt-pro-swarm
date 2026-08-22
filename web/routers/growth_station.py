import logging
import asyncio
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Optional

from web.shared import get_db, get_verified_user_id, templates, config, session_serializer
from core.pg_sqlite_shim import connect
from core.swarm_leads import trigger_outreach_for_leads, init_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["growth_station"])


class ScrapeRequest(BaseModel):
    agent: str  # linkedin_dork, github, reddit, b2b_maps, crunchbase, etc.
    keyword: str
    location: Optional[str] = "Remote"
    max_leads: Optional[int] = 25


class BlastRequest(BaseModel):
    lead_ids: List[int]
    campaign_name: Optional[str] = "Swarm Outreach Campaign"


def run_scrape_background(agent: str, keyword: str, location: str, max_leads: int):
    """Sync wrapper to execute async scraper in background thread pool."""
    try:
        from core.swarm_leads import (
            scrape_linkedin_dorks,
            scrape_github_seekers,
            scrape_reddit_sniper,
            scrape_b2b_companies
        )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if agent == "linkedin_dork":
            loop.run_until_complete(scrape_linkedin_dorks(keyword, location, max_leads))
        elif agent == "github":
            loop.run_until_complete(scrape_github_seekers(keyword, location, max_leads))
        elif agent == "reddit":
            loop.run_until_complete(scrape_reddit_sniper(keyword, max_leads))
        elif agent == "b2b_maps":
            loop.run_until_complete(scrape_b2b_companies(keyword, location, max_leads))
        else:
            # Universal fallback scraper for expanded agents (Crunchbase, Wellfound, Indeed, YC, etc.)
            loop.run_until_complete(scrape_b2b_companies(f"{agent} {keyword}", location, max_leads))
            
        loop.close()
        logger.info(f"[GROWTH ROUTER] Background scrape completed for agent: {agent}")
    except Exception as e:
        logger.error(f"[GROWTH ROUTER] Background scrape error: {e}", exc_info=True)


@router.get("/growth-station", response_class=HTMLResponse)
@router.get("/en/growth-station", response_class=HTMLResponse)
def growth_station_page(request: Request):
    """Renders the main Swarm Leads / Growth Station page for candidates and admins."""
    init_db()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login?next=/growth-station", status_code=303)

    with get_db() as conn:
        user_row = conn.execute("SELECT * FROM users WHERE user_id = ? OR id = ?", (user_id, user_id)).fetchone()
        user = dict(user_row) if user_row else {
            "user_id": user_id,
            "name": "Candidate",
            "email": "user@jobhunt.me",
            "user_type": "candidate",
            "wallet_balance": 100.0
        }

        # Get counts of leads in database
        try:
            leads_count = conn.execute("SELECT COUNT(*) FROM harvested_leads").fetchone()[0]
            pending_count = conn.execute("SELECT COUNT(*) FROM harvested_leads WHERE status = 'pending'").fetchone()[0]
            sent_count = conn.execute("SELECT COUNT(*) FROM harvested_leads WHERE status = 'sent'").fetchone()[0]
        except Exception:
            leads_count, pending_count, sent_count = 0, 0, 0

    req_lang = request.query_params.get("lang") or request.cookies.get("preferred_lang") or ("en" if request.url.path.startswith("/en") else "ar")
    clean_lang = str(req_lang).split("-")[0].lower()
    tpl = "en/growth_station.html" if clean_lang == "en" else ("zh/growth_station.html" if clean_lang == "zh" else "growth_station.html")
    title = "Growth Station & Swarm Leads | JobHunt Pro" if clean_lang == "en" else "محطة النمو وتجميع الفرص | JobHunt Pro"

    content = templates.TemplateResponse(
        request, 
        tpl, 
        {
            "user": user,
            "leads_count": leads_count,
            "pending_count": pending_count,
            "sent_count": sent_count,
            "VERSION": config.VERSION,
            "lang": clean_lang
        }
    )
    
    # Wrap in dashboard shell
    from web.app_v2 import _build_dashboard_shell
    return HTMLResponse(
        _build_dashboard_shell(
            user, 
            user_id, 
            content.body.decode("utf-8"), 
            title, 
            "growth_station", 
            request=request
        )
    )


@router.get("/api/growth/leads")
def get_leads(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    source: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Retrieve harvested leads with pagination and filters."""
    init_db()
    user_id = get_verified_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    offset = (page - 1) * limit
    where_clauses = []
    params = []

    if source and source != "all":
        where_clauses.append("source = ?")
        params.append(source)
    if status and status != "all":
        where_clauses.append("status = ?")
        params.append(status)
    if location:
        where_clauses.append("location LIKE ?")
        params.append(f"%{location}%")
    if search:
        where_clauses.append("(name LIKE ? OR email LIKE ? OR job_title LIKE ?)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    try:
        with get_db() as conn:
            # Get total count for pagination
            count_query = f"SELECT COUNT(*) FROM harvested_leads {where_sql}"
            total_count = conn.execute(count_query, params).fetchone()[0]

            # Fetch rows
            select_query = f"""
                SELECT id, email, name, source, job_title, location, status, notes, created_at
                FROM harvested_leads 
                {where_sql}
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """
            select_params = params + [limit, offset]
            rows = conn.execute(select_query, select_params).fetchall()
            
            leads = [dict(r) for r in rows]

            return JSONResponse({
                "status": "success",
                "leads": leads,
                "total": total_count,
                "page": page,
                "limit": limit
            })
    except Exception as e:
        logger.error(f"[GROWTH ROUTER] Get leads failed: {e}", exc_info=True)
        return JSONResponse({"status": "error", "leads": [], "total": 0, "page": page, "limit": limit})


@router.post("/api/growth/scrape")
def trigger_scrape(request: Request, body: ScrapeRequest, background_tasks: BackgroundTasks):
    """Triggers a background scraping agent task."""
    init_db()
    user_id = get_verified_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Limit max leads to 100 for safety
    max_leads = min(body.max_leads or 25, 100)
    loc = body.location or "Remote"

    # Queue scraping in the background
    background_tasks.add_task(
        run_scrape_background,
        body.agent,
        body.keyword,
        loc,
        max_leads
    )

    return JSONResponse({
        "status": "success",
        "message": f"Autonomous scraper agent '{body.agent}' launched for '{body.keyword}' in '{loc}'. Genuine leads will appear in your directory shortly!"
    })


@router.post("/api/growth/blast")
def trigger_blast(request: Request, body: BlastRequest):
    """Triggers cold email outreach campaign for selected lead IDs."""
    init_db()
    user_id = get_verified_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    if not body.lead_ids:
        raise HTTPException(status_code=400, detail="No lead IDs provided")

    try:
        result = trigger_outreach_for_leads(body.lead_ids, body.campaign_name or "Swarm Outreach Campaign")
        if result.get("status") == "success":
            return JSONResponse(result)
        else:
            return JSONResponse({"status": "error", "message": result.get("error", "Failed to launch blast")}, status_code=400)
    except Exception as e:
        logger.error(f"[GROWTH ROUTER] Blast failed: {e}", exc_info=True)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
