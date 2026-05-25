import time
import hashlib
import logging
from typing import Optional

from redis.exceptions import ConnectionError, TimeoutError
from ecommerce_ops.memory.cache import cache
from ecommerce_ops.infra.circuit_breaker import CircuitBreakerOpenError

logger = logging.getLogger("ecommerce_ops.infra.rate_limiter")

WINDOW_SECONDS = 60


async def check_rate_limit(
    key: str, max_requests: int, window: int = WINDOW_SECONDS
) -> tuple[bool, int]:
    client = await cache.get_client()
    if client is None:
        return True, 0

    redis_key = f"ratelimit:{hashlib.sha256(key.encode()).hexdigest()}"
    now = time.time()
    cutoff = now - window

    try:
        pipe = client.pipeline()
        pipe.zremrangebyscore(redis_key, "-inf", cutoff)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {str(now): now})
        pipe.expire(redis_key, window * 2)
        _, count, *_ = await pipe.execute()
        count = int(count)

        if count >= max_requests:
            return False, count

        return True, count + 1
    except (ConnectionError, TimeoutError, CircuitBreakerOpenError) as e:
        logger.warning("Rate limiter unavailable (allowing request): %s", e)
        return True, 0
