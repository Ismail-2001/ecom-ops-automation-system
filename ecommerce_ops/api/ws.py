"""
WebSocket Connection Manager with Authentication
Production-grade WS manager with token auth, per-IP limits, rate limiting,
and Redis PubSub for cross-worker broadcast.
"""

import asyncio
import json
import hmac
import logging
import secrets
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from ecommerce_ops.config import settings, Environment

logger = logging.getLogger("ecommerce_ops.api.ws")

# ── Limits ─────────────────────────────────────────────────
MAX_WS_CONNECTIONS = 500
MAX_CONNECTIONS_PER_IP = 5
RATE_LIMIT_MESSAGES = 30  # per minute
RATE_LIMIT_WINDOW = 60.0  # seconds
WS_TICKET_TTL_SECONDS = 60  # short-lived, single-use WS tickets

# ── WebSocket Close Codes (RFC 6455 + custom) ──────────────
CLOSE_NORMAL = 1000
CLOSE_GOING_AWAY = 1001
CLOSE_POLICY_VIOLATION = 1008
CLOSE_TRY_AGAIN_LATER = 1013
CLOSE_AUTH_FAILED = 4001
CLOSE_RATE_LIMITED = 4008
CLOSE_TOO_MANY_CONNECTIONS = 4013


class WSTicketStore:
    """
    In-memory store of short-lived, single-use WebSocket tickets.

    A ticket is a random high-entropy value that the frontend exchanges its
    session for (via the BFF route). It is never reused and expires quickly,
    so a leaked ticket in a proxy/log is not a usable standing credential.
    """

    def __init__(self) -> None:
        self._tickets: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def issue(self, operator: str = "ws-operator") -> str:
        ticket = secrets.token_urlsafe(32)
        async with self._lock:
            self._purge_locked()
            self._tickets[ticket] = time.monotonic() + WS_TICKET_TTL_SECONDS
        return ticket

    async def verify(self, ticket: str) -> Optional[str]:
        """
        Validate and consume a single-use ticket.

        Returns the operator id on success, None on invalid/expired/reused.
        """
        now = time.monotonic()
        async with self._lock:
            expiry = self._tickets.pop(ticket, None)
        if expiry is None or expiry < now:
            return None
        return "ws-operator"

    def _purge_locked(self) -> None:
        now = time.monotonic()
        expired = [t for t, exp in self._tickets.items() if exp < now]
        for t in expired:
            self._tickets.pop(t, None)


ws_ticket_store = WSTicketStore()


class AuthenticatedConnection:
    """Tracks a single authenticated WebSocket connection."""

    __slots__ = ("websocket", "operator", "client_ip", "connected_at", "_message_times")

    def __init__(self, websocket: WebSocket, operator: str, client_ip: str):
        self.websocket = websocket
        self.operator = operator
        self.client_ip = client_ip
        self.connected_at = time.monotonic()
        self._message_times: List[float] = []

    def check_rate_limit(self) -> bool:
        """Returns True if within rate limit, False if exceeded."""
        now = time.monotonic()
        cutoff = now - RATE_LIMIT_WINDOW
        self._message_times = [t for t in self._message_times if t > cutoff]
        if len(self._message_times) >= RATE_LIMIT_MESSAGES:
            return False
        self._message_times.append(now)
        return True

    @property
    def age_seconds(self) -> float:
        return time.monotonic() - self.connected_at


PUBSUB_CHANNEL = "opsiq:ws:broadcast"


class ConnectionManager:
    """WebSocket connection manager with authentication, rate limiting, and Redis PubSub."""

    def __init__(self):
        self._connections: List[AuthenticatedConnection] = []
        self._lock = asyncio.Lock()
        self._ip_counts: Dict[str, int] = defaultdict(int)
        self._redis = None
        self._pubsub_task: Optional[asyncio.Task] = None
        self._pubsub = None

    async def init_redis(self, redis_client):
        """Initialize Redis PubSub for cross-worker broadcasts."""
        self._redis = redis_client
        if self._redis is None:
            return
        try:
            self._pubsub = self._redis.pubsub()
            await self._pubsub.subscribe(PUBSUB_CHANNEL)
            self._pubsub_task = asyncio.create_task(self._pubsub_listener())
            logger.info("WS Redis PubSub initialized (channel=%s)", PUBSUB_CHANNEL)
        except Exception as e:
            logger.warning("WS Redis PubSub init failed (broadcasts will be local-only): %s", e)
            self._redis = None

    async def _pubsub_listener(self):
        """Listen for cross-worker broadcast messages from Redis."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data = json.loads(message["data"])
                    conns_snapshot = []
                    async with self._lock:
                        conns_snapshot = list(self._connections)
                    dead = []
                    for conn in conns_snapshot:
                        try:
                            await conn.websocket.send_json(data)
                        except Exception:
                            dead.append(conn)
                    if dead:
                        async with self._lock:
                            for conn in dead:
                                if conn in self._connections:
                                    self._connections.remove(conn)
                                    self._ip_counts[conn.client_ip] = max(
                                        0, self._ip_counts[conn.client_ip] - 1
                                    )
                except Exception as e:
                    logger.debug("WS pubsub message parse error: %s", e)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning("WS pubsub listener stopped: %s", e)

    async def close_redis(self):
        """Clean up Redis PubSub subscription."""
        if self._pubsub_task:
            self._pubsub_task.cancel()
            try:
                await self._pubsub_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.unsubscribe(PUBSUB_CHANNEL)
            await self._pubsub.close()

    def _get_client_ip(self, websocket: WebSocket) -> str:
        """Extract client IP from WebSocket connection."""
        client = websocket.client
        if client:
            return client.host
        forwarded = websocket.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return "unknown"

    def _verify_token(self, token: Optional[str]) -> Optional[str]:
        """
        Verify WS auth token against a single-use ticket or the API_KEY.
        Returns operator ID if valid, None if invalid.
        """
        if not token:
            return None

        api_key_setting = settings.API_KEY
        if api_key_setting:
            expected_key = api_key_setting.get_secret_value()
            if hmac.compare_digest(token, expected_key):
                return "ws-operator"
            return None

        # Dev mode: accept any token
        if settings.ENV != Environment.PRODUCTION:
            return "dev-ws-operator"

        return None

    async def connect(self, websocket: WebSocket, token: Optional[str] = None) -> Optional[AuthenticatedConnection]:
        """
        Authenticate and accept a WebSocket connection.
        Returns AuthenticatedConnection on success, None on rejection.
        """
        client_ip = self._get_client_ip(websocket)

        # 0. Accept a one-time ticket (single-use, TTL-bounded) OR an API key
        operator: Optional[str] = None
        if token:
            operator = await ws_ticket_store.verify(token) or self._verify_token(token)
        if not operator:
            logger.warning("WS auth rejected from %s: invalid token", client_ip)
            await websocket.accept()
            await websocket.close(code=CLOSE_AUTH_FAILED, reason="Authentication failed")
            return None

        # 2. Check per-IP connection limit
        async with self._lock:
            if self._ip_counts[client_ip] >= MAX_CONNECTIONS_PER_IP:
                logger.warning("WS per-IP limit reached for %s (%d)", client_ip, self._ip_counts[client_ip])
                await websocket.accept()
                await websocket.close(
                    code=CLOSE_TOO_MANY_CONNECTIONS,
                    reason=f"Maximum {MAX_CONNECTIONS_PER_IP} connections per IP",
                )
                return None

            # 3. Check global connection limit
            if len(self._connections) >= MAX_WS_CONNECTIONS:
                logger.warning("WS global limit reached (%d)", len(self._connections))
                await websocket.accept()
                await websocket.close(code=CLOSE_TRY_AGAIN_LATER, reason="Server at capacity")
                return None

        # 4. Accept and register
        await websocket.accept()
        conn = AuthenticatedConnection(websocket, operator, client_ip)
        async with self._lock:
            self._connections.append(conn)
            self._ip_counts[client_ip] += 1

        logger.info(
            "WS client connected: operator=%s ip=%s total=%d",
            operator, client_ip, len(self._connections),
        )
        return conn

    async def disconnect(self, conn: AuthenticatedConnection):
        """Remove a connection from tracking."""
        async with self._lock:
            if conn in self._connections:
                self._connections.remove(conn)
                self._ip_counts[conn.client_ip] = max(0, self._ip_counts[conn.client_ip] - 1)
                if self._ip_counts[conn.client_ip] == 0:
                    del self._ip_counts[conn.client_ip]
                logger.info(
                    "WS client disconnected: operator=%s ip=%s total=%d",
                    conn.operator, conn.client_ip, len(self._connections),
                )

    async def broadcast(self, message: dict):
        """Send a message to all authenticated connections across all workers."""
        if self._redis is not None:
            try:
                await self._redis.publish(PUBSUB_CHANNEL, json.dumps(message))
                return
            except Exception as e:
                logger.debug("Redis publish failed, falling back to local broadcast: %s", e)

        dead: List[AuthenticatedConnection] = []
        async with self._lock:
            conns_snapshot = list(self._connections)

        for conn in conns_snapshot:
            try:
                await conn.websocket.send_json(message)
            except Exception:
                dead.append(conn)

        if dead:
            async with self._lock:
                for conn in dead:
                    if conn in self._connections:
                        self._connections.remove(conn)
                        self._ip_counts[conn.client_ip] = max(
                            0, self._ip_counts[conn.client_ip] - 1
                        )

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    def get_stats(self) -> dict:
        """Return connection statistics (no sensitive data)."""
        return {
            "total_connections": len(self._connections),
            "unique_ips": len(self._ip_counts),
            "max_connections": MAX_WS_CONNECTIONS,
            "max_per_ip": MAX_CONNECTIONS_PER_IP,
        }


ws_manager = ConnectionManager()
