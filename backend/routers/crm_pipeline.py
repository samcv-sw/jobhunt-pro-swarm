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

