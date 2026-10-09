import asyncio
import json
import logging
import time
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("streaming.websocket")


class ClientSession:
    """Represents an active WebSocket client with channel subscriptions and bounded send queue."""

    def __init__(self, websocket: WebSocket, client_id: str, queue_size: int = 500):
        self.websocket = websocket
        self.client_id = client_id
        self.subscriptions: Set[str] = {"*"}  # Default: all channels
        self.send_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self.connected_at = time.time()
        self.messages_sent = 0
        self.messages_dropped = 0
        self.is_active = True
        self._sender_task: Optional[asyncio.Task] = None

    def start(self):
        self._sender_task = asyncio.create_task(self._send_loop())

    async def _send_loop(self):
        """Worker task draining the queue and transmitting to the physical socket."""
        try:
            while self.is_active:
                msg = await self.send_queue.get()
                try:
                    await self.websocket.send_text(msg)
                    self.messages_sent += 1
                except Exception as err:
                    logger.debug(f"[WS] Send failed for client {self.client_id}: {err}")
                    break
                finally:
                    self.send_queue.task_done()
        except asyncio.CancelledError:
            pass
        finally:
            self.is_active = False

    def enqueue(self, payload_str: str) -> bool:
        """Non-blocking queue submission. Drops frame if client backpressure occurs."""
        if not self.is_active:
            return False
        try:
            self.send_queue.put_nowait(payload_str)
            return True
        except asyncio.QueueFull:
            self.messages_dropped += 1
            return False

    async def close(self):
        self.is_active = False
        if self._sender_task and not self._sender_task.done():
            self._sender_task.cancel()
        try:
            await self.websocket.close()
        except Exception:
            pass


class WebSocketHub:
    """Enterprise full-duplex WebSocket hub with topic-based pub/sub and backpressure control."""

    def __init__(self):
        self._clients: Dict[str, ClientSession] = {}
        self._lock = asyncio.Lock()
        self._total_broadcasts = 0
        self._total_dropped = 0

    async def register(self, websocket: WebSocket, client_id: str) -> ClientSession:
        await websocket.accept()
        session = ClientSession(websocket, client_id)
        session.start()

        async with self._lock:
            self._clients[client_id] = session

        logger.info(f"[WS] Client connected: {client_id} (Total: {len(self._clients)})")
        return session

    async def unregister(self, client_id: str):
        session = None
        async with self._lock:
            session = self._clients.pop(client_id, None)

        if session:
            await session.close()
            logger.info(f"[WS] Client disconnected: {client_id} (Total: {len(self._clients)})")

    def update_subscriptions(self, client_id: str, channels: Set[str]):
        if client_id in self._clients:
            self._clients[client_id].subscriptions = set(channels)
            logger.debug(f"[WS] Updated subs for {client_id}: {channels}")

    async def broadcast(self, channel: str, data: dict):
        """Dispatches event to all subscribed clients concurrently without blocking."""
        self._total_broadcasts += 1
        payload = json.dumps({
            "channel": channel,
            "timestamp": time.time(),
            "data": data,
        })

        dead_clients = []

        # Snapshot active clients to avoid holding lock during queue ops
        clients = list(self._clients.values())

        for client in clients:
            if not client.is_active:
                dead_clients.append(client.client_id)
                continue

            # Check if subscribed to this channel or wildcard
            if "*" in client.subscriptions or channel in client.subscriptions:
                ok = client.enqueue(payload)
                if not ok:
                    self._total_dropped += 1

        # Clean up dead sockets
        if dead_clients:
            for cid in dead_clients:
                await self.unregister(cid)

    def stats(self) -> dict:
        total_queued = sum(c.send_queue.qsize() for c in self._clients.values())
        return {
            "active_connections": len(self._clients),
            "total_broadcasts": self._total_broadcasts,
            "total_dropped": self._total_dropped,
            "current_queued_frames": total_queued,
            "clients": [
                {
                    "client_id": c.client_id,
                    "subscriptions": list(c.subscriptions),
                    "messages_sent": c.messages_sent,
                    "messages_dropped": c.messages_dropped,
                    "queue_depth": c.send_queue.qsize(),
                    "connected_duration_sec": round(time.time() - c.connected_at, 1),
                }
                for c in self._clients.values()
            ],
        }


# Global singleton hub
ws_hub = WebSocketHub()
