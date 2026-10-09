import asyncio
import json
import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel

try:
    from ..streaming.websocket_hub import ws_hub
except (ImportError, ValueError):
    from streaming.websocket_hub import ws_hub

logger = logging.getLogger("routers.streaming")
router = APIRouter(prefix="", tags=["Streaming"])


class BroadcastRequest(BaseModel):
    channel: str
    data: dict


@router.websocket("/ws/stream")
async def websocket_stream_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None),
):
    """Full-duplex WebSocket stream endpoint for real-time telemetry, topology updates, and MITRE alerts."""
    cid = client_id or f"client-{uuid.uuid4().hex[:8]}"
    session = await ws_hub.register(websocket, cid)

    # Send initial welcome and connection confirmation frame
    welcome_frame = json.dumps({
        "type": "welcome",
        "client_id": cid,
        "active_channels": list(session.subscriptions),
        "protocol_version": "v1-duplex",
    })
    session.enqueue(welcome_frame)

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                msg = json.loads(raw_text)
                action = msg.get("action")

                if action == "subscribe":
                    channels = msg.get("channels", ["*"])
                    ws_hub.update_subscriptions(cid, set(channels))
                    session.enqueue(json.dumps({
                        "type": "subscription_ack",
                        "subscribed": list(channels),
                    }))

                elif action == "ping":
                    session.enqueue(json.dumps({
                        "type": "pong",
                        "timestamp": msg.get("timestamp"),
                    }))

                else:
                    logger.debug(f"[WS] Unknown client action '{action}' from {cid}")

            except json.JSONDecodeError:
                logger.warning(f"[WS] Malformed JSON from client {cid}: {raw_text[:50]}")

    except WebSocketDisconnect:
        logger.info(f"[WS] Client disconnected gracefully: {cid}")
    except Exception as err:
        logger.warning(f"[WS] Connection terminated with error for {cid}: {err}")
    finally:
        await ws_hub.unregister(cid)


@router.get("/api/streaming/stats")
def get_streaming_stats():
    """Retrieve operational telemetry for active WebSocket clients, buffer depths, and message counts."""
    return ws_hub.stats()


@router.post("/api/streaming/broadcast")
async def trigger_manual_broadcast(req: BroadcastRequest):
    """Publish an event to all connected clients on a given topic (used by internal simulation agents)."""
    await ws_hub.broadcast(req.channel, req.data)
    return {
        "status": "DISPATCHED",
        "channel": req.channel,
        "active_listeners": len(ws_hub._clients),
    }
