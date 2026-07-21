"""
Realtime WebSockets Engine for JobHunt Pro.
Handles sub-5ms WebSocket connections for live job alerts & real-time dashboard updates.
"""

from typing import Dict, List
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("websocket_router")

router = APIRouter(prefix="/ws", tags=["Realtime WebSockets"])

class ConnectionManager:
    """
    Manages active WebSocket connections with group broadcasting capabilities.
    """

    def __init__(self):
        # user_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket client connected: user_id={user_id}")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket client disconnected: user_id={user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)

    async def broadcast(self, message: dict):
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/job-alerts/{user_id}")
async def websocket_job_alerts(websocket: WebSocket, user_id: str):
    """
    Live streaming WebSocket endpoint for instant job alerts.
    """
    await manager.connect(user_id, websocket)
    try:
        # Send initial confirmation connection handshake
        await websocket.send_json({
            "event": "connected",
            "message": f"Realtime Job Alerts channel active for user {user_id}",
            "status": "online"
        })
        
        while True:
            # Keep connection alive & listen for client ping/heartbeats
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id, websocket)


@router.websocket("/war-room")
async def websocket_war_room(websocket: WebSocket):
    """
    Sovereign Live War Room WebSocket endpoint.
    Requires authentic JWT credentials passed in query param, authorization header, or subprotocols.
    Verifies user status (active/inactive) in database.
    """
    token = None
    # 1. Try token query parameter
    token_param = websocket.query_params.get("token")
    if token_param:
        token = token_param

    # 2. Try Authorization header
    if not token:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    # 3. Try subprotocols
    subprotocols = websocket.scope.get("subprotocols", [])
    if not token:
        for sub in subprotocols:
            if sub.startswith("bearer."):
                token = sub[7:]
                break
            elif sub.startswith("bearer_"):
                token = sub[7:]
                break
            elif sub.startswith("ey"):
                token = sub
                break

    if not token:
        await websocket.close(code=4001)
        return

    # Verify token
    try:
        from backend.auth import decode_jwt_token
        payload = decode_jwt_token(token)
    except Exception:
        await websocket.close(code=4001)
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001)
        return

    # Verify user in database
    try:
        from sqlalchemy import text
        from backend.database import async_session
        async with async_session() as session:
            result = await session.execute(
                text("SELECT is_active FROM users WHERE user_id = :uid"),
                {"uid": user_id}
            )
            row = result.fetchone()
            if not row or not row[0]:
                await websocket.close(code=4001)
                return
    except Exception:
        await websocket.close(code=4001)
        return

    # Determine matched subprotocol to accept
    selected_subprotocol = None
    for sub in subprotocols:
        if sub.startswith("bearer.") and sub[7:] == token:
            selected_subprotocol = sub
            break
        elif sub.startswith("bearer_") and sub[7:] == token:
            selected_subprotocol = sub
            break
        elif sub == token:
            selected_subprotocol = sub
            break

    await websocket.accept(subprotocol=selected_subprotocol)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        pass

