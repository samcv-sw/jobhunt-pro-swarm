"""
CRM & Webhook Integrations Router for JobHunt Pro.
"""

from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any
from core.crm_sync import sync_lead_to_crm

router = APIRouter(prefix="/api/v1/integrations", tags=["Integrations"])

@router.post("/sync-crm")
async def sync_crm_lead(payload: Dict[str, Any] = Body(...)):
    """Syncs a converted lead directly to HubSpot, Salesforce, or Pipedrive."""
    provider = payload.get("crm_provider")
    api_key = payload.get("api_key", "demo_api_key")
    lead_data = payload.get("lead", {})

    if not provider or not lead_data:
        raise HTTPException(status_code=400, detail="crm_provider and lead data are required.")

    result = sync_lead_to_crm(crm_provider=provider, api_key=api_key, lead_data=lead_data)
    return result
