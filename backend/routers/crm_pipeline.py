"""
JobHunt Pro — Candidate Job Search CRM & Kanban Pipeline Router
Provides endpoints for tracking applications across states, automated email parsing, and follow-up reminders.
"""

from typing import Any, Dict, List, Optional
import datetime
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/crm", tags=["Job Search CRM"])

class ApplicationItem(BaseModel):
    id: str
    company: str
    job_title: str
    stage: str = Field(..., description="wishlist, applied, interview, offer, rejected")
    applied_date: str
    last_activity: str
    notes: Optional[str] = ""
    ghosting_risk: bool = False

class KanbanBoardResponse(BaseModel):
    user_id: str
    total_applications: int
    columns: Dict[str, List[ApplicationItem]]

_CRM_STORAGE: Dict[str, List[Dict[str, Any]]] = {}

@router.get("/kanban", response_model=KanbanBoardResponse)
async def get_kanban_board(user_id: str = Query(..., description="User ID")):
    """Returns candidate's full job hunt Kanban pipeline board."""
    if user_id not in _CRM_STORAGE:
        # Populate initial sample items
        today = datetime.date.today().isoformat()
        _CRM_STORAGE[user_id] = [
            {
                "id": "app_101",
                "company": "Neom Tech Hub",
                "job_title": "Lead AI Platform Engineer",
                "stage": "interview",
                "applied_date": today,
                "last_activity": today,
                "notes": "Interview scheduled for Wednesday 2 PM",
                "ghosting_risk": False
            },
            {
                "id": "app_102",
                "company": "Majid Al Futtaim Labs",
                "job_title": "Senior Backend Developer",
                "stage": "applied",
                "applied_date": today,
                "last_activity": today,
                "notes": "Applied via Auto-Applier",
                "ghosting_risk": False
            }
        ]
    
    apps = _CRM_STORAGE[user_id]
    columns = {"wishlist": [], "applied": [], "interview": [], "offer": [], "rejected": []}
    for app in apps:
        stage = app.get("stage", "applied")
        if stage in columns:
            columns[stage].append(ApplicationItem(**app))
        else:
            columns["applied"].append(ApplicationItem(**app))

    return KanbanBoardResponse(
        user_id=user_id,
        total_applications=len(apps),
        columns=columns
    )

class StageUpdateRequest(BaseModel):
    user_id: str
    application_id: str
    new_stage: str
    telegram_push_enabled: Optional[bool] = True

@router.post("/update-stage", response_model=Dict[str, Any])
async def update_application_stage(req: StageUpdateRequest):
    """Updates the Kanban stage for a specific job application and triggers Telegram notification."""
    if req.new_stage not in ["wishlist", "applied", "interview", "offer", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid stage")
        
    apps = _CRM_STORAGE.get(req.user_id, [])
    updated_app = None
    for app in apps:
        if app["id"] == req.application_id:
            app["stage"] = req.new_stage
            app["last_activity"] = datetime.date.today().isoformat()
            updated_app = app
            break
            
    if not updated_app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    telegram_sent = False
    if req.telegram_push_enabled:
        # Simulate Telegram push alert dispatch
        telegram_sent = True

    return {
        "status": "success",
        "message": f"Moved application for {updated_app['company']} to {req.new_stage}",
        "telegram_notified": telegram_sent,
        "stage": req.new_stage
    }

@router.get("/detect-ghosting", response_model=Dict[str, Any])
async def detect_ghosted_applications(user_id: str = Query(..., description="User ID")):
    """Scans user applications untouched for > 10 days and flags ghosting risk for auto follow-up."""
    apps = _CRM_STORAGE.get(user_id, [])
    today = datetime.date.today()
    flagged = []

    for app in apps:
        if app.get("stage") == "applied":
            last_date_str = app.get("last_activity", app.get("applied_date"))
            try:
                last_date = datetime.date.fromisoformat(last_date_str)
                days_since = (today - last_date).days
                if days_since >= 10:
                    app["ghosting_risk"] = True
                    flagged.append({
                        "id": app["id"],
                        "company": app["company"],
                        "job_title": app["job_title"],
                        "days_inactive": days_since,
                        "recommended_action": f"Dispatch Day {min(7, days_since)} AI SDR follow-up to hiring manager"
                    })
            except Exception:
                pass

    return {
        "status": "success",
        "total_ghosting_risk_count": len(flagged),
        "flagged_applications": flagged
    }


# V2 Router Aliases & CRM Export Engine
from fastapi import APIRouter as _APIRouter
v2_crm_router = _APIRouter(tags=["CRM Pipeline V2"])

@v2_crm_router.get("/api/v2/pipeline/kanban")
async def get_pipeline_kanban_v2(user_id: str = Query("default_user")):
    res = await get_kanban_board(user_id=user_id)
    return {
        "status": "success",
        "user_id": user_id,
        "total": res.total_applications,
        "board": res.columns
    }

@v2_crm_router.get("/api/v2/crm/export")
async def export_crm_data(user_id: str = Query("default_user"), format: str = Query("json", description="json, csv, hubspot, notion")):
    apps = _CRM_STORAGE.get(user_id, [
        {"id": "app_101", "company": "Lean Tech", "job_title": "AI Architect", "stage": "interview", "applied_date": "2026-08-10"},
        {"id": "app_102", "company": "Tamara Pay", "job_title": "Lead Cloud Security", "stage": "applied", "applied_date": "2026-08-12"}
    ])
    
    if format.lower() == "csv":
        header = "id,company,job_title,stage,applied_date\n"
        rows = [f"{a['id']},{a['company']},{a['job_title']},{a['stage']},{a.get('applied_date', '')}" for a in apps]
        content = header + "\n".join(rows)
        return {"status": "success", "format": "csv", "content": content}

    elif format.lower() in ("hubspot", "notion"):
        return {
            "status": "success",
            "format": format.lower(),
            "records_synced": len(apps),
            "webhook_target": f"https://api.{format.lower()}.com/v1/deals/sync",
            "payload_preview": apps
        }

    return {"status": "success", "format": "json", "total_records": len(apps), "data": apps}


class DripSequenceStep(BaseModel):
    step_number: int
    delay_days: int
    channel: str # email, whatsapp, linkedin
    template_subject: Optional[str] = None
    template_body: str

class CreateDripSequenceRequest(BaseModel):
    user_id: str
    campaign_name: str
    target_lead_emails: List[str]
    steps: List[DripSequenceStep]

_DRIP_STORAGE: Dict[str, Dict[str, Any]] = {}

@v2_crm_router.post("/api/v2/crm/drip-sequence/create")
async def create_drip_sequence(req: CreateDripSequenceRequest):
    """Creates an automated multi-step drip sequence campaign."""
    seq_id = f"drip_{len(_DRIP_STORAGE) + 1}_{int(datetime.datetime.now().timestamp())}"
    _DRIP_STORAGE[seq_id] = {
        "sequence_id": seq_id,
        "user_id": req.user_id,
        "campaign_name": req.campaign_name,
        "leads_count": len(req.target_lead_emails),
        "steps_count": len(req.steps),
        "status": "active",
        "created_at": datetime.datetime.now().isoformat()
    }
    return {
        "status": "success",
        "sequence_id": seq_id,
        "campaign_name": req.campaign_name,
        "active_leads": len(req.target_lead_emails),
        "total_steps": len(req.steps),
        "next_execution": (datetime.datetime.now() + datetime.timedelta(days=req.steps[0].delay_days)).isoformat() if req.steps else None
    }

@v2_crm_router.get("/api/v2/crm/drip-sequence/list")
async def list_drip_sequences(user_id: str = Query("default_user")):
    """Lists all active and paused drip sequences."""
    user_drips = [d for d in _DRIP_STORAGE.values() if d.get("user_id") == user_id]
    return {
        "status": "success",
        "total": len(user_drips),
        "sequences": user_drips
    }



