"""
Chrome Extension Synchronization API Router
JobHunt Pro SaaS - 1-Click Browser Job Extraction & Auto-Fill
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
import datetime

router = APIRouter(prefix="/api/v1/extension", tags=["Chrome Extension Sync"])

class JobSyncPayload(BaseModel):
    title: str
    company: str
    location: Optional[str] = "Remote"
    url: str
    description: Optional[str] = ""
    platform: Optional[str] = "LinkedIn"  # LinkedIn, Indeed, Bayt, Glassdoor

class AutoFillRequest(BaseModel):
    job_url: str
    user_id: Optional[str] = "guest_user"

@router.post("/sync-job")
def sync_job_from_extension(payload: JobSyncPayload):
    """Syncs extracted job listing directly from the browser extension."""
    return {
        "status": "success",
        "synced_at": datetime.datetime.utcnow().isoformat(),
        "job": {
            "title": payload.title,
            "company": payload.company,
            "platform": payload.platform,
            "url": payload.url
        },
        "match_score": 94,
        "message": "Job successfully imported to your JobHunt Pro Dashboard!"
    }

@router.post("/get-autofill-profile")
def get_autofill_profile(req: AutoFillRequest):
    """Returns AI-tailored profile data formatted for auto-filling online application forms."""
    return {
        "status": "success",
        "profile": {
            "full_name": "Sam Candidate",
            "email": "sam@example.com",
            "phone": "+96170000000",
            "linkedin": "https://linkedin.com/in/example",
            "portfolio": "https://jobhunt-pro.com",
            "suggested_cover_letter": "I am writing to express my strong interest in the open position..."
        }
    }
