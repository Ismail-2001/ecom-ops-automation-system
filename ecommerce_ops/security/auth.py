"""
Authentication Middleware
FastAPI middleware for authentication and authorization.
"""

import logging
import time
from typing import Any, Callable, Optional, Set

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from ecommerce_ops.security.models import (
    AccessContext,
    Permission,
    Role,
    SecurityEvent,
    User,
)
from ecommerce_ops.security.role_manager import role_manager

logger = logging.getLogger("ecommerce_ops.security.auth")

# Security scheme
security = HTTPBearer(auto_error=False)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for request authentication and logging."""

    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/live",
        "/ready",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    # Paths that require API key
    API_KEY_PATHS = {
        "/api/shopify/webhooks",
    }

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start_time = time.time()

        # Add request ID
        request_id = str(time.time_ns())
        request.state.request_id = request_id

        # Check if path is public
        if self._is_public_path(request.url.path):
            response = await call_next(request)
            self._log_request(request, response, start_time)
            return response

        # Extract authentication info
        api_key = request.headers.get("X-API-Key")
        auth_header = request.headers.get("Authorization")

        # Validate authentication
        user = None
        api_key_id = None

        if api_key:
            # API key authentication
            api_key_obj = role_manager.validate_api_key(api_key)
            if api_key_obj:
                user = role_manager.get_user(api_key_obj.user_id)
                api_key_id = api_key_obj.id
            else:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid API key"},
                )
        elif auth_header and auth_header.startswith("Bearer "):
            # Bearer token authentication
            token = auth_header[7:]
            # In production: validate JWT token
            # For now, use API key validation
            api_key_obj = role_manager.validate_api_key(token)
            if api_key_obj:
                user = role_manager.get_user(api_key_obj.user_id)
                api_key_id = api_key_obj.id

        if not user and not self._is_public_path(request.url.path):
            # Allow requests without auth for now (development mode)
            # In production, uncomment the following:
            # return JSONResponse(
            #     status_code=401,
            #     content={"detail": "Authentication required"},
            # )
            pass

        # Store auth context in request state
        request.state.user = user
        request.state.api_key_id = api_key_id
        request.state.user_id = user.id if user else None

        # Process request
        response = await call_next(request)

        # Log request
        self._log_request(request, response, start_time)

        return response

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public."""
        # Exact match
        if path in self.PUBLIC_PATHS:
            return True

        # Check for static files
        if path.startswith("/static/") or path.endswith((".js", ".css", ".ico")):
            return True

        return False

    def _log_request(
        self,
        request: Request,
        response: Response,
        start_time: float,
    ):
        """Log request details."""
        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            "Request: %s %s -> %d (%.1fms) [user=%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            getattr(request.state, "user_id", "anonymous"),
        )


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> Optional[User]:
    """Dependency for requiring authentication."""
    if not credentials:
        return None

    # Validate token
    api_key_obj = role_manager.validate_api_key(credentials.credentials)
    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = role_manager.get_user(api_key_obj.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


def require_permission(permission: Permission):
    """Dependency factory for requiring specific permission."""

    def dependency(user: Optional[User] = Depends(require_auth)) -> User:
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")

        result = role_manager.check_permission(user, permission)
        if not result.allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission.value}",
            )

        return user

    return dependency


def require_role(role: Role):
    """Dependency factory for requiring specific role."""

    def dependency(user: Optional[User] = Depends(require_auth)) -> User:
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")

        if user.role != role and user.role != Role.SUPER_ADMIN:
            raise HTTPException(
                status_code=403,
                detail=f"Role required: {role.value}",
            )

        return user

    return dependency


def require_admin(user: Optional[User] = Depends(require_auth)) -> User:
    """Dependency for requiring admin role."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> Optional[User]:
    """Dependency for getting current user (optional auth)."""
    if not credentials:
        return None

    api_key_obj = role_manager.validate_api_key(credentials.credentials)
    if not api_key_obj:
        return None

    return role_manager.get_user(api_key_obj.user_id)


def get_access_context(request: Request) -> AccessContext:
    """Get access context from request."""
    user = getattr(request.state, "user", None)
    api_key_id = getattr(request.state, "api_key_id", None)

    return AccessContext(
        user_id=user.id if user else None,
        api_key_id=api_key_id,
        role=user.role if user else None,
        permissions=role_manager.get_user_permissions(user) if user else set(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
