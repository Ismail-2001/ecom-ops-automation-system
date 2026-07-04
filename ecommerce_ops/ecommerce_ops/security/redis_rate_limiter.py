"""
Redis-Backed Rate Limiter
Replaces in-memory rate limiter for horizontal scalability.
"""
import logging
import time
from typing import Optional

logger = logging.getLogger("ecommerce_ops.security.redis_rate_limiter")


class RedisRateLimiter:
    """
    Redis-backed rate limiter using sliding window algorithm.
    Works across multiple instances for horizontal scalability.
    """

    def __init__(self, redis_client, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.redis = redis_client
        self.rpm = requests_per_minute
        self.rph = requests_per_hour
        self._fallback_store = {}  # Fallback when Redis unavailable

    async def check_rate_limit(self, client_id: str) -> dict:
        """
        Check if client is within rate limits.

        Returns:
            dict with keys: allowed, remaining_minute, remaining_hour, retry_after
        """
        try:
            now = time.time()
            minute_key = f"ratelimit:{client_id}:minute"
            hour_key = f"ratelimit:{client_id}:hour"

            pipe = self.redis.pipeline()

            # Sliding window for minute
            pipe.zremrangebyscore(minute_key, 0, now - 60)
            pipe.zadd(minute_key, {str(now): now})
            pipe.zcard(minute_key)
            pipe.expire(minute_key, 60)

            # Sliding window for hour
            pipe.zremrangebyscore(hour_key, 0, now - 3600)
            pipe.zadd(hour_key, {str(now): now})
            pipe.zcard(hour_key)
            pipe.expire(hour_key, 3600)

            results = await pipe.execute()

            minute_count = results[2]
            hour_count = results[5]

            remaining_minute = max(0, self.rpm - minute_count)
            remaining_hour = max(0, self.rph - hour_count)

            allowed = minute_count <= self.rpm and hour_count <= self.rph

            retry_after = 0
            if not allowed:
                if minute_count > self.rpm:
                    retry_after = 60
                elif hour_count > self.rph:
                    retry_after = 3600

            return {
                "allowed": allowed,
                "remaining_minute": remaining_minute,
                "remaining_hour": remaining_hour,
                "retry_after": retry_after,
                "limit_minute": self.rpm,
                "limit_hour": self.rph,
            }

        except Exception as e:
            logger.warning(f"Redis rate limit check failed: {e}, using fallback")
            return self._fallback_check(client_id)

    async def is_rate_limited(self, client_id: str) -> bool:
        """Simple check if client is rate limited."""
        result = await self.check_rate_limit(client_id)
        return not result["allowed"]

    async def get_usage(self, client_id: str) -> dict:
        """Get current usage for a client."""
        try:
            now = time.time()
            minute_key = f"ratelimit:{client_id}:minute"
            hour_key = f"ratelimit:{client_id}:hour"

            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(minute_key, 0, now - 60)
            pipe.zcard(minute_key)
            pipe.zremrangebyscore(hour_key, 0, now - 3600)
            pipe.zcard(hour_key)

            results = await pipe.execute()

            return {
                "used_minute": results[1],
                "used_hour": results[3],
                "remaining_minute": max(0, self.rpm - results[1]),
                "remaining_hour": max(0, self.rph - results[3]),
            }

        except Exception as e:
            logger.warning(f"Redis usage check failed: {e}")
            return {"used_minute": 0, "used_hour": 0, "remaining_minute": self.rpm, "remaining_hour": self.rph}

    async def reset(self, client_id: str):
        """Reset rate limit for a client."""
        try:
            minute_key = f"ratelimit:{client_id}:minute"
            hour_key = f"ratelimit:{client_id}:hour"
            await self.redis.delete(minute_key, hour_key)
        except Exception as e:
            logger.warning(f"Redis reset failed: {e}")

    def _fallback_check(self, client_id: str) -> dict:
        """Fallback rate limiting when Redis is unavailable."""
        now = time.time()
        if client_id not in self._fallback_store:
            self._fallback_store[client_id] = {"minute": [], "hour": []}

        store = self._fallback_store[client_id]

        # Clean old entries
        store["minute"] = [t for t in store["minute"] if t > now - 60]
        store["hour"] = [t for t in store["hour"] if t > now - 3600]

        minute_count = len(store["minute"])
        hour_count = len(store["hour"])

        allowed = minute_count < self.rpm and hour_count < self.rph

        if allowed:
            store["minute"].append(now)
            store["hour"].append(now)

        return {
            "allowed": allowed,
            "remaining_minute": max(0, self.rpm - minute_count - (1 if allowed else 0)),
            "remaining_hour": max(0, self.rph - hour_count - (1 if allowed else 0)),
            "retry_after": 60 if minute_count >= self.rpm else (3600 if hour_count >= self.rph else 0),
            "limit_minute": self.rpm,
            "limit_hour": self.rph,
        }
