"""
web/routers/lead_nurture.py - Automated Lead Nurture & Conversion Drip Router
JobHunt Pro SaaS - Manages lead sequence subscription and cron drip execution.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from core.lead_nurture_engine import LeadNurtureEngine

logger = logging.getLogger("lead_nurture_router")
router = APIRouter(tags=["Lead Nurture Drip"])


@router.post("/api/nurture/subscribe-lead")
async def subscribe_lead(request: Request):
    """Enrolls a lead into the 3-stage behavioral conversion sequence."""
    try:
        data = await request.json()
        email = data.get("email", "").strip()
        job_title = data.get("job_title", "Software Specialist")
        ats_score = int(data.get("ats_score", 85))
        city = data.get("city", "Riyadh")

        if not email or "@" not in email:
            return JSONResponse({"success": False, "error": "Invalid email address."}, status_code=400)

        result = LeadNurtureEngine.schedule_guest_nurture(
            email=email,
            job_title=job_title,
            ats_score=ats_score,
            city=city
        )
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error subscribing lead to nurture: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/api/nurture/trigger-cron-pulse")
async def trigger_cron_pulse():
    """Processes pending nurture drips ready for delivery."""
    try:
        result = LeadNurtureEngine.process_pending_drips()
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error executing nurture drip cron pulse: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.get("/api/nurture/lead-status/{email}")
async def get_lead_nurture_status(email: str):
    """Returns active nurture drip status for a given email address."""
    LeadNurtureEngine.init_db()
    with LeadNurtureEngine.get_db() as conn:
        rows = conn.execute(
            "SELECT stage, status, scheduled_at, sent_at, channel FROM lead_nurture_drips WHERE email = ? ORDER BY stage ASC",
            (email.strip(),)
        ).fetchall()
        
        stages = [dict(r) for r in rows]
        return JSONResponse({
            "success": True,
            "email": email,
            "total_stages": len(stages),
            "stages": stages
        })
