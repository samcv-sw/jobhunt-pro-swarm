from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from core.database import db
from typing import Dict, List
import logging
import json

from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected: {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected: {user_id}")

    async def broadcast_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"WS broadcast failed to {user_id}: {e}")


manager = ConnectionManager()


@router.get("/legacy-dashboard")
async def legacy_dashboard(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")

    async with db.pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if not user:
            return RedirectResponse(url="/logout")

        stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM applications 
            WHERE user_id = $1
        """,
            user_id,
        )

        applications = await conn.fetch(
            """
            SELECT * FROM applications 
            WHERE user_id = $1 
            ORDER BY created_at DESC LIMIT 50
        """,
            user_id,
        )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": dict(user),
            "stats": dict(stats)
            if stats
            else {"total": 0, "successful": 0, "failed": 0},
            "applications": [dict(app) for app in applications],
        },
    )


@router.get("/dashboard/kanban")
async def dashboard_kanban(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")

    async with db.pool.acquire() as conn:
        applications = await conn.fetch(
            """
            SELECT * FROM applications 
            WHERE user_id = $1 
            ORDER BY created_at DESC LIMIT 100
        """,
            user_id,
        )

    return templates.TemplateResponse(
        request, "kanban_board.html", {"jobs": [dict(app) for app in applications]}
    )


from fastapi import Form


@router.post("/api/htmx/update_status")
async def update_status(request: Request, id: str = Form(...), status: str = Form(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return {"error": "unauthorized"}

    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE applications SET status = $1 WHERE id = $2 AND user_id = $3",
            status,
            int(id),
            user_id,
        )
    return {"success": True}


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    user_id = (
        websocket.session.get("user_id") if hasattr(websocket, "session") else None
    )
    if not user_id:
        await websocket.close()
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
            # Handle incoming ping/pong if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
