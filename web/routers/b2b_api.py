import logging
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException

import config

logger = logging.getLogger(__name__)
router = APIRouter()

VALID_B2B_KEYS = config.B2B_API_KEYS


@router.get("/api/v1/market-data/trends")
async def get_market_trends(x_b2b_key: str = Header(None)):
    """
    Data Broker API: Sells anonymous, aggregated hiring trends to hedge funds,
    recruiters, and universities based on our scraping data.
    (Infinite $0 MRR potential).
    """
    if not x_b2b_key or x_b2b_key not in VALID_B2B_KEYS:
        raise HTTPException(
            status_code=401, detail="Invalid B2B API Key. Upgrade to Corporate Tier."
        )

    # Mock aggregation for demonstration.
    # In production, this would query the `jobs` and `applications` tables
    # grouped by `title` and `created_at` over the last 30 days.

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "insights": {
            "top_growing_roles": [
                "AI Prompt Engineer",
                "Rust Developer",
                "FastAPI Architect",
            ],
            "declining_roles": ["Manual QA", "Entry Level React"],
            "average_salary_trends": {
                "Software Engineer": "+4.5% MoM",
                "Data Scientist": "+2.1% MoM",
            },
            "total_active_listings_scraped": 14502,
            "application_velocity_index": 8.7,  # High demand
        },
    }
