"""
A/B Testing & Subject Line Optimizer Router.
"""

from fastapi import APIRouter, Query, Body, HTTPException
from typing import List, Dict, Any
from core.ab_testing import generate_subject_line_variants, select_winning_variant

router = APIRouter(prefix="/api/v1/ab-tests", tags=["A/B Testing"])

@router.post("/generate-variants")
async def create_variants(payload: Dict[str, Any] = Body(...)):
    """Generates 3 optimized A/B subject line variants for outreach campaigns."""
    topic = payload.get("topic", "Sales Automation")
    role = payload.get("target_role", "Sales Director")
    variants = generate_subject_line_variants(topic=topic, target_role=role)
    return {"status": "success", "variants": variants}

@router.post("/select-winner")
async def evaluate_winner(variants: List[Dict[str, Any]] = Body(...)):
    """Selects the winning subject line variant based on performance metrics."""
    if not variants:
        raise HTTPException(status_code=400, detail="Variants list cannot be empty.")
    winner = select_winning_variant(variants)
    return {"status": "success", "winning_variant": winner}

@router.post("/mab-select")
async def multi_armed_bandit_select(
    variants: List[Dict[str, Any]] = Body(...),
    epsilon: float = Query(0.20, ge=0.05, le=0.50, description="Exploration rate (default 20% exploration, 80% exploitation)")
):
    """
    Multi-Armed Bandit (MAB) Epsilon-Greedy allocation algorithm.
    Dynamically assigns campaign traffic to maximize overall campaign conversion rate.
    """
    import random

    if not variants:
        raise HTTPException(status_code=400, detail="Variants list cannot be empty.")

    total_sends = sum(v.get("sends", 0) for v in variants)

    # If initial exploration phase (< 50 total sends across variants), pick uniform random
    if total_sends < 50 or random.random() < epsilon:
        chosen = random.choice(variants)
        selection_reason = "Exploration Phase (Uniform Random Trial)"
    else:
        # Exploitation Phase: Pick variant with highest conversion rate (replies/sends or opens/sends)
        best_variant = None
        best_rate = -1.0
        for v in variants:
            sends = max(1, v.get("sends", 0))
            conversions = v.get("conversions", 0) or v.get("replies", 0) or v.get("opens", 0)
            rate = conversions / sends
            if rate > best_rate:
                best_rate = rate
                best_variant = v

        chosen = best_variant or variants[0]
        selection_reason = f"Exploitation Phase (Selected highest converting variant: {best_rate*100:.1f}% rate)"

    return {
        "status": "success",
        "algorithm": "Epsilon-Greedy Multi-Armed Bandit",
        "epsilon_exploration": epsilon,
        "exploitation_weight": 1.0 - epsilon,
        "total_campaign_sends": total_sends,
        "selected_variant": chosen,
        "selection_reason": selection_reason
    }

