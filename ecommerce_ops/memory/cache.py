import json
import logging
from typing import Any, Optional
import redis.asyncio as redis
from ecommerce_ops.config import settings

logger = logging.getLogger("ecommerce_ops.memory")

class RedisCache:
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._redis: Optional[redis.Redis] = None

    async def get_client(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            logger.info("Initialized Redis client")
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        try:
            client = await self.get_client()
            val = await client.get(key)
            if val:
                return json.loads(val)
            return None
        except Exception as e:
            logger.warning(f"Redis GET error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        try:
            client = await self.get_client()
            val_str = json.dumps(value)
            await client.set(key, val_str, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Redis SET error for {key}: {e}")
            return False
            
    async def close(self):
        if self._redis:
            await self._redis.close()

cache = RedisCache()
