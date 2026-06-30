from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from core.database import db
import logging

from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

ADMIN_CODE = "ADMIN99"

@router.get("/admin")
async def admin_dashboard(request: Request):
    user_type = request.session.get("user_type")
    
    if user_type != "admin":
        return templates.TemplateResponse(request, "admin_login.html")

    async with db.pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM applications) as total_applications,
                (SELECT COUNT(*) FROM applications WHERE status = 'completed') as successful_applications
        """)
        
        users = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC LIMIT 100")

    return templates.TemplateResponse(request, "admin_dashboard.html", {
        "stats": dict(stats) if stats else {},
        "users": [dict(u) for u in users]
    })

@router.post("/admin/login")
async def admin_login(request: Request, admin_code: str = Form(...)):
    if admin_code == ADMIN_CODE:
        request.session["user_type"] = "admin"
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(request, "admin_login.html", {"error": "Invalid admin code."})

@router.post("/admin/grant_tokens")
async def grant_tokens(request: Request, user_id: str = Form(...), tokens: int = Form(...)):
    if request.session.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    async with db.pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET tokens = tokens + $1 WHERE user_id = $2
        """, tokens, user_id)
        
    return RedirectResponse(url="/admin", status_code=303)
