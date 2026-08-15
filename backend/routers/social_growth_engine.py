"""
Automated Social Growth & pSEO Indexing Router
JobHunt Pro SaaS - REST endpoints for Viral Content Generation and Indexing
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import List, Optional

from core.automated_viral_growth_engine import viral_growth_engine

router = APIRouter(prefix="/api/v2/growth", tags=["Social Growth & Content Engine"])


class IndexPulseRequest(BaseModel):
    urls: List[str] = Field(default_factory=lambda: [
        "https://jobhunt-pro.com/jobs/devops-engineer-in-riyadh",
        "https://jobhunt-pro.com/jobs/ai-architect-in-dubai"
    ])


@router.get("/linkedin-post")
def get_viral_linkedin_post(
    topic: str = Query("salary_negotiation", description="Topic category"),
    role: Optional[str] = Query(None, description="Target role"),
    city: Optional[str] = Query(None, description="Target city")
):
    """Generates an authoritative, highly-converting LinkedIn post with hashtags and CTA."""
    return viral_growth_engine.generate_viral_linkedin_post(
        topic_category=topic,
        target_role=role,
        city=city
    )


@router.get("/twitter-thread")
def get_viral_twitter_thread(
    topic: str = Query("ats_hacks", description="Topic category"),
    role: Optional[str] = Query(None, description="Target role")
):
    """Generates a 5-tweet educational thread optimized for high reach and bookmarks."""
    return viral_growth_engine.generate_viral_twitter_thread(
        topic_category=topic,
        role=role
    )


@router.post("/index-pulse")
def submit_indexing_pulse(req: IndexPulseRequest):
    """Submits pSEO URLs to Google Indexing API / IndexNow protocol."""
    return viral_growth_engine.dispatch_pseo_indexing_pulse(req.urls)
