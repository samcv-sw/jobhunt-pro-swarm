"""
web/routers/enhancements_router.py - Enterprise SDR & Lead Gen Upgrades Router
Exposes API endpoints for:
1. Live Demo Interactive Lead Sandbox (Homepage Widget)
2. Domain Warm-up & Bounce Health Monitor
3. Real-time Lead Enrichment & Intent Scoring
4. SDR Event Webhooks (Email Opened & Lead Replied Alerts)
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from services.domain_warmup_engine import DomainWarmupEngine
from services.lead_enrichment_engine import LeadEnrichmentEngine
from services.sdr_alert_dispatcher import SDRAlertDispatcher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/sdr", tags=["sdr_enhancements"])

warmup_engine = DomainWarmupEngine()
alert_dispatcher = SDRAlertDispatcher()


@router.post("/demo-sandbox")
async def live_demo_sandbox(request: Request):
    """
    Live interactive demo endpoint for homepage visitors.
    Generates instant scrubbed job leads & AI SDR outreach preview without sign-in.
    """
    try:
        body = await request.json()
        job_title = (body.get("job_title") or "Network Engineer").strip()
        location = (body.get("location") or "Riyadh, Saudi Arabia").strip()

        # Simulated live scrubbed leads for instant demo
        sample_leads = [
            {
                "company": "Saudi Telecom Company (STC)",
                "title": f"Senior {job_title}",
                "location": location,
                "email": f"careers.hiring@{job_title.lower().replace(' ', '')}-stc.com",
                "salary": "$6,500 - $9,000 / mo",
                "posted": "2 hours ago",
            },
            {
                "company": "Neom Tech & Digital",
                "title": f"Lead {job_title} Lead",
                "location": "Neom, Saudi Arabia",
                "email": f"talent.acquisition@neom-{job_title.lower().replace(' ', '')}.com",
                "salary": "$8,000 - $12,000 / mo",
                "posted": "5 hours ago",
            },
            {
                "company": "Etisalat (e&)",
                "title": f"{job_title} Specialist",
                "location": "Dubai, UAE",
                "email": "hr.tech@e-and.com",
                "salary": "$7,000 - $10,500 / mo",
                "posted": "1 day ago",
            }
        ]

        enriched_leads = []
        for lead in sample_leads:
            enrichment = LeadEnrichmentEngine.generate_personalized_hook(lead)
            enriched_leads.append({
                **lead,
                "intent_score": enrichment["intent_score"],
                "outreach_subject": enrichment["subject"],
                "outreach_hook": enrichment["hook_opening"],
            })

        return {
            "status": "success",
            "search_query": {"title": job_title, "location": location},
            "total_matched_leads": len(enriched_leads),
            "leads": enriched_leads,
            "demo_message": "Preview Mode: Sign up to dispatch automated AI SDR outreach swarm."
        }
    except Exception as e:
        logger.error(f"Demo sandbox error: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@router.get("/domain-warmup/health/{domain}")
async def get_domain_health(domain: str):
    """Returns 24h deliverability health & warmup status for a sending domain."""
    try:
        health = warmup_engine.get_domain_health(domain)
        return {"status": "success", "health": health}
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@router.post("/events/email-opened")
async def webhook_email_opened(request: Request):
    """Webhook for tracking email opens & dispatching instant SDR notifications."""
    try:
        body = await request.json()
        email = body.get("email") or "hr@company.com"
        company = body.get("company") or "Target Enterprise"
        title = body.get("title") or "Technical Position"
        chat_id = body.get("chat_id")

        sent = alert_dispatcher.notify_email_opened(
            lead_email=email, company=company, job_title=title, user_chat_id=chat_id
        )
        return {"status": "ok", "alert_sent": sent}
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@router.post("/events/lead-replied")
async def webhook_lead_replied(request: Request):
    """Webhook for tracking candidate/HR replies & dispatching instant SDR notifications."""
    try:
        body = await request.json()
        email = body.get("email") or "hr@company.com"
        company = body.get("company") or "Target Enterprise"
        title = body.get("title") or "Technical Position"
        snippet = body.get("reply_snippet") or "We would love to schedule an interview with you this week."
        chat_id = body.get("chat_id")

        sent = alert_dispatcher.notify_lead_replied(
            lead_email=email, company=company, job_title=title, reply_snippet=snippet, user_chat_id=chat_id
        )
        return {"status": "ok", "alert_sent": sent}
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
