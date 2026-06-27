"""
Security Headers and Rate Limiting
Middleware for security hardening.
"""

import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

logger = logging.getLogger("ecommerce_ops.security.hardening")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""

    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
    }

    # CORS headers (configured per-app)
    CORS_HEADERS = {
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key",
        "Access-Control-Max-Age": "86400",
    }

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Handle preflight requests
        if request.method == "OPTIONS":
            return Response(
                status_code=200,
                headers=self.CORS_HEADERS,
            )

        # Process request
        response = await call_next(request)

        # Add security headers
        for header, value in self.SECURITY_HEADERS.items():
            response.headers[header] = value

        # Add CORS headers
        origin = request.headers.get("origin")
        if origin:
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

        # Rate limit storage
        self._minute_counts: Dict[str, list] = defaultdict(list)
        self._hour_counts: Dict[str, list] = defaultdict(list)
        self._blocked: Dict[str, datetime] = {}

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Get client identifier
        client_id = self._get_client_id(request)

        # Check if blocked
        if self._is_blocked(client_id):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": self._get_block_remaining(client_id),
                },
                headers={"Retry-After": str(self._get_block_remaining(client_id))},
            )

        # Check rate limits
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

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self._get_remaining(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = self._get_reset_time(client_id)

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier."""
        # Use API key if available
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{api_key[:16]}"

        # Use IP address
        return request.client.host if request.client else "unknown"

    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limits."""
        now = time.time()

        # Clean old entries
        self._minute_counts[client_id] = [
            t for t in self._minute_counts[client_id]
            if now - t < 60
        ]
        self._hour_counts[client_id] = [
            t for t in self._hour_counts[client_id]
            if now - t < 3600
        ]

        # Check minute limit
        if len(self._minute_counts[client_id]) >= self.requests_per_minute:
            return False

        # Check hour limit
        if len(self._hour_counts[client_id]) >= self.requests_per_hour:
            return False

        # Record request
        self._minute_counts[client_id].append(now)
        self._hour_counts[client_id].append(now)

        return True

    def _get_remaining(self, client_id: str) -> int:
        """Get remaining requests in current window."""
        return max(0, self.requests_per_minute - len(self._minute_counts[client_id]))

    def _get_reset_time(self, client_id: str) -> str:
        """Get reset time for rate limit window."""
        if self._minute_counts[client_id]:
            oldest = min(self._minute_counts[client_id])
            reset_at = int(oldest + 60)
            return str(reset_at)
        return str(int(time.time() + 60))

    def _is_blocked(self, client_id: str) -> bool:
        """Check if client is blocked."""
        if client_id in self._blocked:
            if datetime.utcnow() < self._blocked[client_id]:
                return True
            else:
                del self._blocked[client_id]
        return False

    def _block_client(self, client_id: str):
        """Block client for rate limit violation."""
        self._blocked[client_id] = datetime.utcnow() + timedelta(minutes=5)
        logger.warning("Rate limit exceeded for client: %s", client_id)

    def _get_block_remaining(self, client_id: str) -> int:
        """Get remaining block time in seconds."""
        if client_id in self._blocked:
            remaining = (self._blocked[client_id] - datetime.utcnow()).total_seconds()
            return max(0, int(remaining))
        return 0


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware for input sanitization."""

    # Dangerous patterns
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
        # Check URL for dangerous patterns
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

        # Check headers for dangerous patterns
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

        # Log request
        logger.info(
            "Request started: %s %s from %s",
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
        )

        # Process request
        response = await call_next(request)

        # Log response
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "Request completed: %s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response
