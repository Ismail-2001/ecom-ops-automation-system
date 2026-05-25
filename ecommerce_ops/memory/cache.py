import json
import hashlib
import logging
from typing import Any, Optional

import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

from ecommerce_ops.config import settings
from ecommerce_ops.infra.retry import async_retry_decorator
from ecommerce_ops.infra.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

logger = logging.getLogger("ecommerce_ops.memory")


CACHE_TTL_BY_PREFIX: dict[str, int] = {
    "/api/analytics": 10,
    "/api/agents/status": 5,
    "/api/settings": 30,
    "/api/approvals": 5,
    "/api/audit": 10,
    "/health": 5,
}


def _cache_key(method: str, path: str, query: str = "") -> str:
    raw = f"{method}:{path}:{query}"
    return f"http_cache:{hashlib.sha256(raw.encode()).hexdigest()}"


def _get_ttl(path: str) -> int:
    for prefix, ttl in CACHE_TTL_BY_PREFIX.items():
        if path.startswith(prefix):
            return ttl
    return 0


class RedisCache:
    _circuit_breaker = CircuitBreaker(
        name="Redis", failure_threshold=3, recovery_timeout=15.0
    )

    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._redis: Optional[redis.Redis] = None

    async def get_client(self) -> Optional[redis.Redis]:
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                    socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                )
                await self._redis.ping()
                logger.info("Initialized Redis client")
            except Exception as e:
                logger.warning("Failed to initialize Redis: %s", e)
                self._redis = None
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        try:
            return await self._circuit_breaker.call(self._get_with_retry, key)
        except CircuitBreakerOpenError:
            logger.warning("Redis circuit open, skipping GET %s", key)
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        try:
            return await self._circuit_breaker.call(self._set_with_retry, key, value, ttl)
        except CircuitBreakerOpenError:
            logger.warning("Redis circuit open, skipping SET %s", key)
            return False

    async def get_cached_response(self, method: str, path: str, query: str = "") -> Optional[tuple[int, dict]]:
        ttl = _get_ttl(path)
        if ttl == 0 or method != "GET":
            return None
        key = _cache_key(method, path, query)
        raw = await self.get(key)
        if raw is None:
            return None
        return raw["status_code"], raw["body"]

    async def set_cached_response(self, method: str, path: str, query: str, status_code: int, body: dict) -> None:
        ttl = _get_ttl(path)
        if ttl == 0 or method != "GET":
            return
        key = _cache_key(method, path, query)
        await self.set(key, {"status_code": status_code, "body": body}, ttl=ttl)

    @async_retry_decorator(
        exceptions=(ConnectionError, TimeoutError, CircuitBreakerOpenError),
        max_attempts=2,
        min_wait=0.5,
        max_wait=2.0,
    )
    async def _get_with_retry(self, key: str) -> Optional[Any]:
        client = await self.get_client()
        if client is None:
            return None
        val = await client.get(key)
        if val:
            return json.loads(val)
        return None

    @async_retry_decorator(
        exceptions=(ConnectionError, TimeoutError, CircuitBreakerOpenError),
        max_attempts=2,
        min_wait=0.5,
        max_wait=2.0,
    )
    async def _set_with_retry(self, key: str, value: Any, ttl: int) -> bool:
        client = await self.get_client()
        if client is None:
            return False
        val_str = json.dumps(value)
        await client.set(key, val_str, ex=ttl)
        return True

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None


cache = RedisCache()
