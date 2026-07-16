"""JobHunt Pro — WebSocket Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import logging
import os
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.auth import decode_jwt_token, _get_client_ip, _check_lockout, _record_failure, _record_success, _IS_TESTING
from backend.database import async_session
from backend.websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/war-room")
async def websocket_war_room(websocket: WebSocket) -> None:
    """War Room real-time WebSocket connection handler."""
    logger.info("War Room WebSocket connection handshake initiated.")
    
    client_ip = _get_client_ip(websocket)
    if not _IS_TESTING:
        lockout_remaining = _check_lockout(client_ip)
        if lockout_remaining > 0:
            logger.warning(f"WebSocket connection rejected: IP {client_ip} is locked out for {lockout_remaining:.1f}s.")
            await websocket.close(code=4003)
            return

    # Verify JWT Bearer token
    token = websocket.query_params.get("token")
    if not token:
        # Check Authorization header
        auth_header = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token:
        # Check subprotocols
        subprotocols = websocket.scope.get("subprotocols") or []
        for sub in subprotocols:
            if sub and sub.startswith("ey"):
                token = sub
                break
            elif sub and sub.lower().startswith("bearer."):
                token = sub.split(".", 1)[1]
                break
            elif sub and sub.lower().startswith("bearer"):
                parts = sub.split("_", 1)
                if len(parts) > 1:
                    token = parts[1]
                    break

    if not token:
        logger.warning("WebSocket connection rejected: Bearer token missing.")
        await websocket.close(code=4001)
        return

    from sqlalchemy import text

    try:
        claims = decode_jwt_token(token)
        sub = claims.get("sub")
        if not sub:
            logger.warning("WebSocket connection rejected: invalid JWT subject.")
            await websocket.close(code=4001)
            return

        async with async_session() as session:
            result = await session.execute(
                text("SELECT is_active FROM users WHERE user_id = :user_id"),
                {"user_id": sub}
            )
            row = result.fetchone()
            if not row or not row[0]:
                logger.warning(f"WebSocket connection rejected: user {sub} is inactive or missing.")
                await websocket.close(code=4001)
                return

        if not _IS_TESTING:
            _record_success(client_ip)
    except Exception as jwt_err:
        if not _IS_TESTING:
            _record_failure(client_ip)
        logger.error(f"WebSocket authentication error: {jwt_err}")
        await websocket.close(code=4001)
        return

    await manager.connect(websocket)
    logger.info(f"WebSocket client {sub} connected to War Room.")
    try:
        while True:
            raw = await websocket.receive_text()
            if raw == "ping":
                await websocket.send_text("pong")
                continue
            
            # Try to process as JSON for admin dashboard actions
            try:
                data = json.loads(raw)
                msg_type = data.get("type", "")
                if msg_type == "fetch_dlq":
                    async with async_session() as session:
                        rows = (
                            await session.execute(
                                text("""
                                    SELECT id, task_name, error, created_at
                                    FROM failed_jobs
                                    ORDER BY created_at DESC
                                    LIMIT 50
                                """)
                            )
                        ).fetchall()
                    dlq_items = [
                        {
                            "id": r.id,
                            "task_name": r.task_name,
                            "error": r.error,
                            "created_at": str(r.created_at),
                        }
                        for r in rows
                    ]
                    await websocket.send_text(
                        json.dumps({"type": "dlq_list", "items": dlq_items})
                    )
                elif msg_type == "fetch_logs":
                    import datetime as _dt
                    cutoff = data.get("minutes", 60) or 60
                    since = _dt.datetime.utcnow() - _dt.timedelta(minutes=cutoff)
                    async with async_session() as session:
                        rows = (
                            await session.execute(
                                text("""
                                    SELECT id, level, message, created_at
                                    FROM app_logs
                                    WHERE created_at >= :since
                                    ORDER BY created_at DESC
                                    LIMIT 200
                                """),
                                {"since": since},
                            )
                        ).fetchall()
                    log_items = [
                        {
                            "id": r.id,
                            "level": r.level,
                            "message": r.message,
                            "created_at": str(r.created_at),
                        }
                        for r in rows
                    ]
                    await websocket.send_text(
                        json.dumps({"type": "log_list", "items": log_items})
                    )
                else:
                    await manager.send_personal_message(f"Message text was: {raw}", websocket)
            except Exception:
                # If not JSON or parsing fails, treat it as plain text message
                await manager.send_personal_message(f"Message text was: {raw}", websocket)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {sub} disconnected from War Room.")
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error(f"War Room WebSocket error: {exc}")
        manager.disconnect(websocket)
