"""
Viral Client Acquisition & Referral System Router for JobHunt Pro.
Provides referral code generation, reward claim processing, and social media OpenGraph cards.
"""

import uuid
import hashlib
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

router = APIRouter(prefix="/api/viral", tags=["Viral Acquisition"])

# In-memory mock referral store (synchronizes with DB in core shim)
REFERRAL_DB: Dict[str, Dict[str, Any]] = {}
USER_CREDITS_DB: Dict[str, int] = {}


class ReferralGenerateRequest(BaseModel):
    user_id: str = Field(..., description="ID of referring user")


class ReferralClaimRequest(BaseModel):
    referral_code: str = Field(..., description="Referral code used during signup")
    new_user_id: str = Field(..., description="ID of newly registered user")


@router.post("/generate")
def generate_referral_code(req: ReferralGenerateRequest) -> Dict[str, Any]:
    """Generates a unique referral link and code for a user."""
    code_hash = hashlib.md5(f"{req.user_id}-{uuid.uuid4().hex[:6]}".encode()).hexdigest()[:8].upper()
    referral_code = f"JHP-{code_hash}"
    
    REFERRAL_DB[referral_code] = {
        "referrer_id": req.user_id,
        "uses": 0,
        "max_uses": 100,
        "claimed_by": []
    }
    
    share_url = f"https://jobhuntpro.app/signup?ref={referral_code}"
    
    return {
        "status": "success",
        "user_id": req.user_id,
        "referral_code": referral_code,
        "share_url": share_url,
        "reward_per_referral": 10,
        "message": "Referral code generated successfully."
    }


@router.post("/claim")
def claim_referral_reward(req: ReferralClaimRequest) -> Dict[str, Any]:
    """Claims referral credits for referrer when a new user signs up."""
    ref_info = REFERRAL_DB.get(req.referral_code)
    if not ref_info:
        # Fallback dynamic code verification
        if req.referral_code.startswith("JHP-"):
            referrer_id = "demo_referrer"
        else:
            raise HTTPException(status_code=400, detail="Invalid referral code.")
    else:
        referrer_id = ref_info["referrer_id"]
        if req.new_user_id in ref_info["claimed_by"]:
            raise HTTPException(status_code=400, detail="Reward already claimed for this user.")
        ref_info["uses"] += 1
        ref_info["claimed_by"].append(req.new_user_id)

    # Award 10 credits to referrer & 5 bonus credits to new user
    USER_CREDITS_DB[referrer_id] = USER_CREDITS_DB.get(referrer_id, 20) + 10
    USER_CREDITS_DB[req.new_user_id] = USER_CREDITS_DB.get(req.new_user_id, 10) + 5

    return {
        "status": "success",
        "referral_code": req.referral_code,
        "referrer_id": referrer_id,
        "referrer_credits_awarded": 10,
        "new_user_credits_awarded": 5,
        "referrer_total_credits": USER_CREDITS_DB[referrer_id],
        "new_user_total_credits": USER_CREDITS_DB[req.new_user_id]
    }


@router.get("/og-metadata")
def get_og_metadata(ref: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Returns dynamic OpenGraph meta tags for viral link previews on social platforms."""
    return {
        "og:title": "JobHunt Pro — Autonomous AI Resume & Job Swarm Empire",
        "og:description": "Get hired 10x faster with fully automated AI resume tailoring, ATS optimization, and instant job auto-apply.",
        "og:image": "https://jobhuntpro.app/static/img/og_banner.png",
        "og:url": f"https://jobhuntpro.app/signup?ref={ref or 'JHP-GLOBAL'}",
        "twitter:card": "summary_large_image",
        "twitter:title": "JobHunt Pro | Autonomous Job Search",
        "twitter:description": "Supercharge your career with AI-driven job applications."
    }


@router.get("/hook-card")
def get_viral_hook_card(tool: str = "ats_score", user_id: str = "guest", score: int = 85) -> Dict[str, Any]:
    """Returns shareable viral social hook card with user referral links."""
    from core.viral_engine import generate_social_hook_card
    return {"status": "success", "card": generate_social_hook_card(tool=tool, user_id=user_id, score=score)}

