import asyncio
import logging
from functools import wraps
from typing import TypeVar, Callable, Any

T = TypeVar("T")

logger = logging.getLogger("ecommerce_ops.utils")


async def retry_async(
    func: Callable[..., Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[..., Any]:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        last_exc = None
        delay = base_delay
        for attempt in range(1, max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                last_exc = e
                if attempt < max_retries:
                    logger.warning(
                        "Retry %d/%d for %s after error: %s",
                        attempt, max_retries, func.__name__, e,
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff
        raise last_exc
    return wrapper
