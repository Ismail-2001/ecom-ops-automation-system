"""
Security Headers and Rate Limiting
Middleware for security hardening.
"""

import hmac
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

logger = logging.getLogger("ecommerce_ops.security.hardening")

ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3200",
    "http://localhost:8080",
    "https://ops-iq.dev",
]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' https://fonts.gstatic.com;",
    }

    CORS_HEADERS = {
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key, X-Operator-Id",
        "Access-Control-Max-Age": "86400",
    }

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if request.method == "OPTIONS":
            response = Response(status_code=200, headers=self.CORS_HEADERS)
            origin = request.headers.get("origin", "")
            if origin in ALLOWED_ORIGINS:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
            return response

        response = await call_next(request)

        for header, value in self.SECURITY_HEADERS.items():
            response.headers[header] = value

        origin = request.headers.get("origin", "")
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size

        self._minute_counts: Dict[str, list] = defaultdict(list)
        self._hour_counts: Dict[str, list] = defaultdict(list)
        self._blocked: Dict[str, datetime] = {}

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        client_id = self._get_client_id(request)

        if self._is_blocked(client_id):
            remaining = self._get_block_remaining(client_id)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": remaining,
                },
                headers={"Retry-After": str(remaining)},
            )

        if not self._check_rate_limit(client_id):
            self._block_client(client_id)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": self.requests_per_minute,
                    "window": "1 minute",
                },
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)

        remaining = self._get_remaining(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = self._get_reset_time(client_id)

        return response

    def _get_client_id(self, request: Request) -> str:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{api_key[:16]}"
        return request.client.host if request.client else "unknown"

    def _check_rate_limit(self, client_id: str) -> bool:
        now = time.time()

        self._minute_counts[client_id] = [
            t for t in self._minute_counts[client_id]
            if now - t < 60
        ]
        self._hour_counts[client_id] = [
            t for t in self._hour_counts[client_id]
            if now - t < 3600
        ]

        if len(self._minute_counts[client_id]) >= self.requests_per_minute:
            return False

        if len(self._hour_counts[client_id]) >= self.requests_per_hour:
            return False

        self._minute_counts[client_id].append(now)
        self._hour_counts[client_id].append(now)

        return True

    def _get_remaining(self, client_id: str) -> int:
        return max(0, self.requests_per_minute - len(self._minute_counts[client_id]))

    def _get_reset_time(self, client_id: str) -> str:
        if self._minute_counts[client_id]:
            oldest = min(self._minute_counts[client_id])
            reset_at = int(oldest + 60)
            return str(reset_at)
        return str(int(time.time() + 60))

    def _is_blocked(self, client_id: str) -> bool:
        if client_id in self._blocked:
            if datetime.now(timezone.utc) < self._blocked[client_id]:
                return True
            else:
                del self._blocked[client_id]
        return False

    def _block_client(self, client_id: str):
        self._blocked[client_id] = datetime.now(timezone.utc) + timedelta(minutes=5)
        logger.warning("Rate limit exceeded for client: %s", client_id)

    def _get_block_remaining(self, client_id: str) -> int:
        if client_id in self._blocked:
            remaining = (self._blocked[client_id] - datetime.now(timezone.utc)).total_seconds()
            return max(0, int(remaining))
        return 0


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware for input sanitization."""

    DANGEROUS_PATTERNS = [
        "<script",
        "javascript:",
        "onerror=",
        "onload=",
        "eval(",
        "document.cookie",
        "window.location",
    ]

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        url = str(request.url)
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in url.lower():
                logger.warning(
                    "Blocked request with dangerous pattern: %s from %s",
                    pattern,
                    request.client.host if request.client else "unknown",
                )
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid request"},
                )

        for header_name, header_value in request.headers.items():
            for pattern in self.DANGEROUS_PATTERNS:
                if pattern.lower() in str(header_value).lower():
                    logger.warning(
                        "Blocked request with dangerous header pattern: %s",
                        pattern,
                    )
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid request headers"},
                    )

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start_time = time.time()

        logger.info(
            "Request started: %s %s from %s",
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
        )

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "Request completed: %s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response
