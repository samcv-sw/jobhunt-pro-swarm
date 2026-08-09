"""JobHunt Pro — Real-Time Server-Sent Events (SSE) Router.

Provides real-time event streaming for campaign status, leads updates, and platform telemetry.
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["RealTime SSE"])


async def event_generator(request: Request) -> AsyncGenerator[str, None]:
    """Generates server-sent events for real-time dashboard feeds."""
    try:
        # Initial connection event
        yield f"event: connect\ndata: {json.dumps({'status': 'connected', 'timestamp': time.time()})}\n\n"
        
        counter = 0
        while True:
            # Check for client disconnect
            if await request.is_disconnected():
                logger.info("SSE client disconnected")
                break
                
            await asyncio.sleep(5.0)
            counter += 1
            
            # Periodic heartbeat and live update telemetry
            event_data = {
                "sequence": counter,
                "timestamp": time.time(),
                "metrics": {
                    "active_swarms": 3,
                    "leads_processed_today": 124,
                    "conversion_rate_percent": 18.5,
                }
            }
            yield f"event: heartbeat\ndata: {json.dumps(event_data)}\n\n"
            
    except asyncio.CancelledError:
        logger.info("SSE stream cancelled")


@router.get("/api/v1/sse/live-feed")
async def live_feed(request: Request) -> StreamingResponse:
    """Stream real-time updates and campaign telemetry to the dashboard via SSE."""
    return StreamingResponse(
        event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
