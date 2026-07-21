"""
Live WebSockets Real-Time Event Bus Router for JobHunt Pro SaaS.
Provides zero-latency connection manager for live dashboard notifications, application updates, and scraper events.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSockets"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        disconnected = []
        payload = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.error(f"Error broadcasting WebSocket message: {e}")
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@router.websocket("/live-feed")
async def websocket_live_feed(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial welcome telemetry event
        await websocket.send_json({
            "event": "CONNECTED",
            "status": "active",
            "channel": "live-feed",
            "message": "Sovereign WebSockets Event Bus Connected"
        })
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                # Echo back acknowledgment or ping-pong
                if parsed.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": parsed.get("timestamp")})
                else:
                    await websocket.send_json({
                        "event": "ACK",
                        "received": parsed
                    })
            except Exception:
                await websocket.send_json({"event": "ECHO", "payload": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
