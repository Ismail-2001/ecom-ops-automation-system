import asyncio
import logging
from typing import List

from fastapi import WebSocket

logger = logging.getLogger("ecommerce_ops.api.ws")

MAX_WS_CONNECTIONS = 1000


class ConnectionManager:
    def __init__(self):
        self._connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if len(self._connections) >= MAX_WS_CONNECTIONS:
                await websocket.close(code=1013, reason="Too many connections")
                return
            self._connections.append(websocket)
            logger.info("WS client connected. Total: %d", len(self._connections))

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)
                logger.info("WS client disconnected. Total: %d", len(self._connections))

    async def broadcast(self, message: dict):
        async with self._lock:
            dead: List[WebSocket] = []
            for conn in self._connections:
                try:
                    await conn.send_json(message)
                except Exception:
                    dead.append(conn)
            for conn in dead:
                self._connections.remove(conn)


ws_manager = ConnectionManager()
