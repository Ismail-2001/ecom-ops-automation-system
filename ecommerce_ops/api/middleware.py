import uuid
import time
import json
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from ecommerce_ops.config import settings, Environment
from ecommerce_ops.infra.rate_limiter import check_rate_limit
from ecommerce_ops.memory.cache import cache, _get_ttl
from ecommerce_ops.security.hardening import (
    SecurityHeadersMiddleware,
    InputSanitizationMiddleware,
)
from ecommerce_ops.api.metrics import (
    METRIC_HTTP_REQUESTS, METRIC_HTTP_DURATION, METRIC_RATE_LIMIT_REJECTED,
)

logger = logging.getLogger("ecommerce_ops.api.middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start
        METRIC_HTTP_REQUESTS.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
        METRIC_HTTP_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(
            "Request started: %s %s [%s]", request.method, request.url.path, request_id
        )
        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start
        logger.info(
            "Request completed: %s %s -> %s [%s] (%.3fs)",
            request.method, request.url.path, response.status_code, request_id, duration,
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if settings.ENV != Environment.PRODUCTION:
            return await call_next(request)

        forwarded = request.headers.get("X-Forwarded-For", "")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (
            request.client.host if request.client else "unknown"
        )
        allowed, count = await check_rate_limit(client_ip, settings.RATE_LIMIT_PER_MINUTE)

        if not allowed:
            METRIC_RATE_LIMIT_REJECTED.inc()
            logger.warning("Rate limit exceeded for %s (%d req/min)", client_ip, count)
            return Response(
                status_code=429,
                content='{"detail":"Rate limit exceeded. Try again later."}',
                media_type="application/json",
                headers={"X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE)},
            )

        return await call_next(request)


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method != "GET":
            return await call_next(request)

        ttl = _get_ttl(request.url.path)
        if ttl == 0:
            return await call_next(request)

        cached = await cache.get_cached_response(request.method, request.url.path, request.url.query)
        if cached is not None:
            status_code, body = cached
            return Response(
                content=json.dumps(body),
                status_code=status_code,
                media_type="application/json",
                headers={"X-Cache": "HIT"},
            )

        response = await call_next(request)

        if response.status_code == 200 and response.media_type == "application/json":
            try:
                body = json.loads(response.body)
                await cache.set_cached_response(
                    request.method, request.url.path, request.url.query, response.status_code, body
                )
            except (RuntimeError, json.JSONDecodeError):
                pass

        response.headers["X-Cache"] = "MISS"
        return response


def setup_middleware(app: FastAPI):
    allowed_origins = settings.CORS_ORIGINS
    if not allowed_origins:
        allowed_origins = ["http://localhost:3000", "http://localhost:5173"]

    app.add_middleware(InputSanitizationMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(ResponseCacheMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
