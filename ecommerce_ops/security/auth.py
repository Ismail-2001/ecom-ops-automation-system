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

    API_KEY_PATHS = {
        "/api/shopify/webhooks",
    }

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start_time = time.time()

        request_id = str(time.time_ns())
        request.state.request_id = request_id

        if self._is_public_path(request.url.path):
            response = await call_next(request)
            self._log_request(request, response, start_time)
            return response

        api_key = request.headers.get("X-API-Key")
        auth_header = request.headers.get("Authorization")

        user = None
        api_key_id = None

        if api_key:
            try:
                api_key_obj = await role_manager.validate_api_key(api_key)
                if api_key_obj:
                    user = await role_manager.get_user(api_key_obj.user_id)
                    api_key_id = api_key_obj.id
                else:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid API key"},
                    )
            except Exception:
                logger.debug("RBAC tables not available, skipping API key validation")
        elif auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                api_key_obj = await role_manager.validate_api_key(token)
                if api_key_obj:
                    user = await role_manager.get_user(api_key_obj.user_id)
                    api_key_id = api_key_obj.id
            except Exception:
                logger.debug("RBAC tables not available, skipping Bearer token validation")

        request.state.user = user
        request.state.api_key_id = api_key_id
        request.state.user_id = user.id if user else None

        response = await call_next(request)
        self._log_request(request, response, start_time)

        return response

    def _is_public_path(self, path: str) -> bool:
        if path in self.PUBLIC_PATHS:
            return True
        if path.startswith("/static/") or path.endswith((".js", ".css", ".ico")):
            return True
        return False

    def _log_request(
        self,
        request: Request,
        response: Response,
        start_time: float,
    ):
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "Request: %s %s -> %d (%.1fms) [user=%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            getattr(request.state, "user_id", "anonymous"),
        )


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> Optional[User]:
    """Dependency for requiring authentication."""
    if not credentials:
        return None

    api_key_obj = await role_manager.validate_api_key(credentials.credentials)
    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = await role_manager.get_user(api_key_obj.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


def require_permission(permission: Permission):
    """Dependency factory for requiring specific permission."""

    async def dependency(user: Optional[User] = Depends(require_auth)) -> User:
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

    async def dependency(user: Optional[User] = Depends(require_auth)) -> User:
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")

        if user.role != role and user.role != Role.SUPER_ADMIN:
            raise HTTPException(
                status_code=403,
                detail=f"Role required: {role.value}",
            )

        return user

    return dependency


async def require_admin(user: Optional[User] = Depends(require_auth)) -> User:
    """Dependency for requiring admin role."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> Optional[User]:
    """Dependency for getting current user (optional auth)."""
    if not credentials:
        return None

    api_key_obj = await role_manager.validate_api_key(credentials.credentials)
    if not api_key_obj:
        return None

    return await role_manager.get_user(api_key_obj.user_id)


async def get_access_context(request: Request) -> AccessContext:
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
