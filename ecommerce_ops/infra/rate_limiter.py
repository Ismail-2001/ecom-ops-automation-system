"""
Rate Limiter
Redis-backed sliding window with in-memory token bucket fallback.
"""

import hashlib
import logging
import time
from collections import defaultdict

from redis.exceptions import ConnectionError, TimeoutError

from ecommerce_ops.infra.circuit_breaker import CircuitBreakerOpenError
from ecommerce_ops.memory.cache import cache

logger = logging.getLogger("ecommerce_ops.infra.rate_limiter")

WINDOW_SECONDS = 60

# In-memory fallback: per-client sliding window
_memory_store: dict[str, list[float]] = defaultdict(list)
_memory_block_until: dict[str, float] = {}
MEMORY_MAX_ENTRIES = 10_000


async def check_rate_limit(
    key: str, max_requests: int, window: int = WINDOW_SECONDS
) -> tuple[bool, int]:
    client = await cache.get_client()
    if client is None:
        return _memory_check(key, max_requests, window)

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
        logger.warning("Redis rate limiter unavailable, using in-memory fallback: %s", e)
        return _memory_check(key, max_requests, window)


def _evict_lru():
    """Bound the in-memory store by evicting only the least-recently-active keys.

    A naive cap that clears *all* entries would let a surge of distinct clients
    immediately reset every caller's window, driving an unrestricted traffic
    burst. Evict just the oldest keys until the store is back under the cap so
    active clients keep their state.
    """
    if len(_memory_store) <= MEMORY_MAX_ENTRIES:
        return
    by_recency = sorted(
        _memory_store,
        key=lambda k: _memory_store[k][-1] if _memory_store[k] else 0,
    )
    remove_count = len(_memory_store) - MEMORY_MAX_ENTRIES
    for key in by_recency[:remove_count]:
        _memory_store.pop(key, None)
        _memory_block_until.pop(key, None)


def _memory_check(key: str, max_requests: int, window: int) -> tuple[bool, int]:
    """In-memory sliding window rate limiter (per-process)."""
    now = time.time()
    cutoff = now - window

    # Check block
    block_until = _memory_block_until.get(key, 0)
    if now < block_until:
        return False, max_requests

    # Sliding window
    timestamps = _memory_store[key]
    _memory_store[key] = [t for t in timestamps if t > cutoff]
    count = len(_memory_store[key])

    if count >= max_requests:
        _memory_block_until[key] = now + window
        logger.warning("In-memory rate limit hit for %s", key[:16])
        return False, count

    _memory_store[key].append(now)
    # Keep the store bounded, evicting only stale/least-recent keys. Runs after
    # the append so the entry that pushed us over the cap is what triggers it.
    if len(_memory_store) > MEMORY_MAX_ENTRIES:
        _evict_lru()
    return True, count + 1
