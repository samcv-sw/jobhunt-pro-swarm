"""
AI Email Subject Line & Body A/B Testing Engine Router
JobHunt Pro SaaS - Campaign Performance & Optimization Swarm
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("email_ab_testing")

router = APIRouter(prefix="/api/v1/ab-testing", tags=["AI Email A/B Testing Engine"])

# In-memory store for A/B testing campaign variants
AB_CAMPAIGNS: Dict[str, Dict[str, Any]] = {}


class EmailVariant(BaseModel):
    variant_id: Optional[str] = Field(default="")
    subject: str = Field(..., description="Subject line text")
    body: str = Field(..., description="Email body text")


class ABCampaignCreateRequest(BaseModel):
    campaign_name: str = Field(...)
    user_id: str = Field(...)
    variants: List[EmailVariant] = Field(..., min_items=2, max_items=5, description="List of 2 to 5 email variations")
    sample_threshold: int = Field(default=50, description="Number of sends before auto-selecting winning variant")


class TrackVariantEventRequest(BaseModel):
    campaign_id: str = Field(...)
    variant_id: str = Field(...)
    event_type: str = Field(..., description="sent, opened, clicked, replied")


@router.post("/create-campaign")
def create_ab_campaign(req: ABCampaignCreateRequest) -> Dict[str, Any]:
    """Creates a multi-variant email campaign with automated winning variant detection."""
    campaign_id = f"ab_{uuid.uuid4().hex[:12]}"

    prepared_variants = []
    for idx, var in enumerate(req.variants):
        vid = var.variant_id or f"var_{chr(65 + idx)}"  # Var A, Var B, Var C...
        prepared_variants.append({
            "variant_id": vid,
            "subject": var.subject,
            "body": var.body,
            "sends": 0,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "conversion_rate": 0.0
        })

    campaign = {
        "campaign_id": campaign_id,
        "campaign_name": req.campaign_name,
        "user_id": req.user_id,
        "sample_threshold": req.sample_threshold,
        "total_sends": 0,
        "status": "testing",
        "winning_variant_id": None,
        "variants": prepared_variants
    }

    AB_CAMPAIGNS[campaign_id] = campaign

    return {
        "status": "success",
        "message": "A/B campaign created successfully",
        "campaign_id": campaign_id,
        "variants_count": len(prepared_variants)
    }


@router.get("/select-next-variant/{campaign_id}")
def select_next_variant(campaign_id: str) -> Dict[str, Any]:
    """Selects which variant to send next based on sample threshold and conversion performance."""
    campaign = AB_CAMPAIGNS.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="A/B Campaign not found")

    # If winner already locked, return winner
    if campaign["winning_variant_id"]:
        winner = next((v for v in campaign["variants"] if v["variant_id"] == campaign["winning_variant_id"]), campaign["variants"][0])
        return {"status": "success", "variant": winner, "is_winner": True}

    # If total sends exceed sample threshold, calculate winner
    if campaign["total_sends"] >= campaign["sample_threshold"]:
        best_variant = max(campaign["variants"], key=lambda v: (v["replies"] * 3 + v["clicks"] * 2 + v["opens"]) / (v["sends"] or 1))
        campaign["winning_variant_id"] = best_variant["variant_id"]
        campaign["status"] = "optimized"
        logger.info(f"A/B Campaign {campaign_id} optimized! Winner selected: {best_variant['variant_id']}")
        return {"status": "success", "variant": best_variant, "is_winner": True}

    # Round-robin selection during initial testing phase
    var_index = campaign["total_sends"] % len(campaign["variants"])
    selected = campaign["variants"][var_index]
    selected["sends"] += 1
    campaign["total_sends"] += 1

    return {"status": "success", "variant": selected, "is_winner": False}


@router.post("/track-event")
def track_variant_event(req: TrackVariantEventRequest) -> Dict[str, Any]:
    """Tracks opens, clicks, or replies for a specific variant to update performance scores."""
    campaign = AB_CAMPAIGNS.get(req.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    variant = next((v for v in campaign["variants"] if v["variant_id"] == req.variant_id), None)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    if req.event_type == "opened":
        variant["opens"] += 1
    elif req.event_type == "clicked":
        variant["clicks"] += 1
    elif req.event_type == "replied":
        variant["replies"] += 1

    # Recalculate score
    sends = variant["sends"] or 1
    variant["conversion_rate"] = round(((variant["replies"] * 3 + variant["clicks"] * 2 + variant["opens"]) / sends) * 100, 2)

    return {
        "status": "success",
        "campaign_id": req.campaign_id,
        "variant_id": req.variant_id,
        "new_conversion_rate": variant["conversion_rate"]
    }
