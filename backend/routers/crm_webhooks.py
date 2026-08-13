from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, List, Optional
import datetime
import urllib.request
import json
import uuid

router = APIRouter(prefix="/api/v1/crm-webhooks", tags=["CRM & Webhooks"])

# In-memory webhook registry store for active endpoints
WEBHOOK_SUBSCRIPTIONS: List[Dict[str, Any]] = [
    {
        "id": "wh_zapier_default",
        "name": "Zapier Lead Sync",
        "target_url": "https://hooks.zapier.com/hooks/catch/sample/jobhuntpro",
        "events": ["lead.qualified", "response.received"],
        "crm_target": "zapier",
        "status": "active",
        "created_at": "2026-08-01T10:00:00Z"
    },
    {
        "id": "wh_hubspot_default",
        "name": "HubSpot CRM Integration",
        "target_url": "https://api.hubapi.com/crm/v3/objects/contacts/sync",
        "events": ["lead.qualified"],
        "crm_target": "hubspot",
        "status": "active",
        "created_at": "2026-08-05T14:30:00Z"
    }
]

class WebhookRegistration(BaseModel):
    name: str
    target_url: str
    crm_target: str = "zapier" # zapier, hubspot, salesforce, pipedrive, custom
    events: List[str] = ["lead.qualified", "response.received"]

class WebhookTestPayload(BaseModel):
    webhook_id: str
    sample_lead: Optional[Dict[str, Any]] = None

@router.get("/list")
async def list_webhooks():
    return {
        "total": len(WEBHOOK_SUBSCRIPTIONS),
        "webhooks": WEBHOOK_SUBSCRIPTIONS,
        "available_crm_connectors": ["Zapier", "Make", "HubSpot", "Salesforce", "Pipedrive", "Custom Webhook"],
        "supported_events": ["lead.qualified", "response.received", "email.bounced", "meeting.booked"]
    }

@router.post("/register")
async def register_webhook(payload: WebhookRegistration):
    if not payload.target_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Target URL must start with http:// or https://")
    
    new_sub = {
        "id": f"wh_{uuid.uuid4().hex[:10]}",
        "name": payload.name,
        "target_url": payload.target_url,
        "crm_target": payload.crm_target.lower(),
        "events": payload.events,
        "status": "active",
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    WEBHOOK_SUBSCRIPTIONS.append(new_sub)
    return {
        "message": "Webhook successfully registered and active.",
        "subscription": new_sub
    }

@router.post("/dispatch-test")
async def dispatch_test_webhook(payload: WebhookTestPayload):
    target = next((w for w in WEBHOOK_SUBSCRIPTIONS if w["id"] == payload.webhook_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Webhook subscription ID not found.")
    
    lead_data = payload.sample_lead or {
        "lead_id": "ld_99812",
        "first_name": "Sami",
        "last_name": "Al-Hassan",
        "email": "sami.hassan@gccenterprise.com",
        "company": "GCC Enterprise Tech",
        "job_title": "VP of Engineering",
        "location": "Riyadh, Saudi Arabia",
        "sentiment": "Interested",
        "qualified_at": datetime.datetime.utcnow().isoformat()
    }
    
    dispatch_payload = {
        "event": "lead.qualified",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "crm_target": target["crm_target"],
        "data": lead_data
    }
    
    # Simulate execution response
    return {
        "status": "success",
        "webhook_id": target["id"],
        "target_url": target["target_url"],
        "dispatched_event": "lead.qualified",
        "http_status": 200,
        "response_time_ms": 142,
        "payload_delivered": dispatch_payload
    }
