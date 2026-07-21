"""
WebSocket Live Telemetry Engine — GOD-MODE Module
Manages real-time event broadcasting for system analytics, latency monitoring,
conversion tracking, and security honeypot alerts.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class TelemetryBroadcaster:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.metrics_history: List[Dict] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")
        # Send initial snapshot
        await websocket.send_text(json.dumps({
            "event": "snapshot",
            "timestamp": time.time(),
            "active_clients": len(self.active_connections),
            "system_status": "GOD_MODE_ACTIVE"
        }))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast_event(self, event_type: str, data: Dict):
        """Broadcasts a telemetry event to all connected WebSocket clients."""
        payload = {
            "event": event_type,
            "timestamp": time.time(),
            "data": data
        }
        self.metrics_history.append(payload)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)

        dead_sockets = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(payload))
            except Exception as e:
                logger.warning(f"Failed to send telemetry event: {e}")
                dead_sockets.add(connection)
        
        for dead in dead_sockets:
            self.disconnect(dead)

# Global singleton
telemetry_broadcaster = TelemetryBroadcaster()
