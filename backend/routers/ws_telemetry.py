"""
Real-Time Telemetry WebSocket Router for JobHunt Pro.
Pushes live task execution, auto-application progress, and telemetry updates to web & Telegram mini-apps.
"""

import json
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("ws_telemetry")
router = APIRouter(prefix="/ws", tags=["telemetry_ws"])

class TelemetryConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket Client Connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket Client Disconnected.")

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        payload = json.dumps({"event": event_type, "data": data})
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning(f"Error broadcasting to WebSocket client: {e}")
                disconnected.append(connection)
                
        for conn in disconnected:
            self.disconnect(conn)

manager = TelemetryConnectionManager()

@router.websocket("/telemetry")
async def telemetry_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back telemetry heartbeat
            await websocket.send_text(json.dumps({"status": "heartbeat_ok", "received": data}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
