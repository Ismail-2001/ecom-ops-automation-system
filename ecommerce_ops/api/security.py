"""
Security API Routes
Endpoints for RBAC, API keys, and security management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ecommerce_ops.security.audit import audit_logger
from ecommerce_ops.security.auth import require_admin, require_auth
from ecommerce_ops.security.models import (
    APIKey,
    Permission,
    Role,
    User,
)
from ecommerce_ops.security.role_manager import role_manager

logger = logging.getLogger("ecommerce_ops.api.security")

router = APIRouter(prefix="/security", tags=["security"])


class UserCreateRequest(BaseModel):
    email: str
    name: Optional[str] = None
    role: Role = Role.VIEWER
    permissions: Optional[List[Permission]] = None


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[Permission]] = None


class APIKeyCreateRequest(BaseModel):
    name: str
    role: Role = Role.VIEWER
    expires_days: int = 90
    permissions: Optional[List[Permission]] = None


class PermissionCheckRequest(BaseModel):
    permissions: List[Permission]


# ── Users ──────────────────────────────────────────────────


@router.post("/users")
async def create_user(req: UserCreateRequest, admin: User = Depends(require_admin)):
    """Create a new user."""
    try:
        user = role_manager.create_user(
            email=req.email,
            name=req.name,
            role=req.role,
            permissions=set(req.permissions) if req.permissions else None,
        )

        audit_logger.log_event(
            event_type="user_management",
            action="create_user",
            resource="user",
            resource_id=user.id,
            user_id=admin.id,
            success=True,
            details={"email": req.email, "role": req.role.value},
        )

        return {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "created_at": user.created_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users")
async def list_users(
    role: Optional[Role] = None,
    is_active: Optional[bool] = None,
    admin: User = Depends(require_admin),
):
    """List users."""
    users = role_manager.list_users(role=role, is_active=is_active)
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
        "total": len(users),
    }


@router.get("/users/{user_id}")
async def get_user(user_id: str, admin: User = Depends(require_admin)):
    """Get user details."""
    user = role_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "is_active": user.is_active,
        "permissions": [p.value for p in user.permissions],
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "login_count": user.login_count,
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    req: UserUpdateRequest,
    admin: User = Depends(require_admin),
):
    """Update user."""
    success = role_manager.update_user(
        user_id=user_id,
        name=req.name,
        role=req.role,
        is_active=req.is_active,
        permissions=set(req.permissions) if req.permissions else None,
    )

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    audit_logger.log_event(
        event_type="user_management",
        action="update_user",
        resource="user",
        resource_id=user_id,
        user_id=admin.id,
        success=True,
        details=req.model_dump(exclude_none=True),
    )

    return {"updated": True}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: User = Depends(require_admin)):
    """Delete user."""
    success = role_manager.delete_user(user_id)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    audit_logger.log_event(
        event_type="user_management",
        action="delete_user",
        resource="user",
        resource_id=user_id,
        user_id=admin.id,
        success=True,
    )

    return {"deleted": True}


# ── API Keys ───────────────────────────────────────────────


@router.post("/api-keys")
async def create_api_key(
    req: APIKeyCreateRequest,
    admin: User = Depends(require_admin),
):
    """Create API key."""
    api_key = role_manager.create_api_key(
        user_id=admin.id,
        name=req.name,
        role=req.role,
        expires_days=req.expires_days,
        permissions=set(req.permissions) if req.permissions else None,
    )

    audit_logger.log_event(
        event_type="api_key_management",
        action="create_api_key",
        resource="api_key",
        resource_id=api_key.id,
        user_id=admin.id,
        success=True,
        details={"name": req.name, "role": req.role.value},
    )

    return {
        "id": api_key.id,
        "key": api_key.key,  # Only shown once!
        "name": api_key.name,
        "role": api_key.role.value,
        "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
        "created_at": api_key.created_at.isoformat(),
    }


@router.get("/api-keys")
async def list_api_keys(
    user_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: User = Depends(require_admin),
):
    """List API keys."""
    keys = role_manager.list_api_keys(user_id=user_id, is_active=is_active)
    return {
        "api_keys": [
            {
                "id": k.id,
                "name": k.name,
                "user_id": k.user_id,
                "role": k.role.value,
                "is_active": k.is_active,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "last_used": k.last_used.isoformat() if k.last_used else None,
                "usage_count": k.usage_count,
                "created_at": k.created_at.isoformat(),
            }
            for k in keys
        ],
        "total": len(keys),
    }


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: str, admin: User = Depends(require_admin)):
    """Revoke API key."""
    success = role_manager.revoke_api_key(key_id)

    if not success:
        raise HTTPException(status_code=404, detail="API key not found")

    audit_logger.log_event(
        event_type="api_key_management",
        action="revoke_api_key",
        resource="api_key",
        resource_id=key_id,
        user_id=admin.id,
        success=True,
    )

    return {"revoked": True}


# ── Roles ──────────────────────────────────────────────────


@router.get("/roles")
async def list_roles(admin: User = Depends(require_admin)):
    """List all roles."""
    roles = role_manager.list_roles()
    return {
        "roles": [
            {
                "name": r.name.value,
                "display_name": r.display_name,
                "description": r.description,
                "permissions_count": len(r.permissions),
                "is_system": r.is_system,
            }
            for r in roles
        ],
    }


@router.get("/roles/{role_name}/permissions")
async def get_role_permissions(role_name: str, admin: User = Depends(require_admin)):
    """Get permissions for a role."""
    try:
        role = Role(role_name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    role_def = role_manager.get_role(role)
    if not role_def:
        raise HTTPException(status_code=404, detail="Role not found")

    return {
        "role": role_name,
        "permissions": [p.value for p in role_def.permissions],
    }


# ── Permission Checks ─────────────────────────────────────


@router.post("/check-permissions")
async def check_permissions(
    req: PermissionCheckRequest,
    user: User = Depends(require_auth),
):
    """Check if current user has specific permissions."""
    result = role_manager.check_permissions(user, set(req.permissions))
    return {
        "allowed": result.allowed,
        "role": result.role.value if result.role else None,
        "missing_permissions": [p.value for p in result.missing_permissions],
    }


@router.get("/my-permissions")
async def get_my_permissions(user: User = Depends(require_auth)):
    """Get current user's permissions."""
    permissions = role_manager.get_user_permissions(user)
    return {
        "user_id": user.id,
        "role": user.role.value,
        "permissions": [p.value for p in permissions],
    }


# ── Security Summary ───────────────────────────────────────


@router.get("/audit/summary")
async def get_audit_summary(
    hours: int = Query(24, ge=1, le=168),
    admin: User = Depends(require_admin),
):
    """Get security audit summary."""
    return audit_logger.get_security_summary(hours=hours)


@router.get("/audit/logs")
async def get_audit_logs(
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    admin: User = Depends(require_admin),
):
    """Get audit logs."""
    entries = audit_logger.get_entries(
        event_type=event_type,
        user_id=user_id,
        limit=limit,
    )
    return {
        "entries": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "action": e.action,
                "resource": e.resource,
                "resource_id": e.resource_id,
                "user_id": e.user_id,
                "success": e.success,
                "risk_level": e.risk_level,
            }
            for e in entries
        ],
        "total": len(entries),
    }


# ── Health ─────────────────────────────────────────────────


@router.get("/health")
async def security_health():
    """Health check for security service."""
    return {
        "status": "healthy",
        "rbac": "enabled",
        "audit_logging": "enabled",
        "rate_limiting": "enabled",
        "timestamp": datetime.utcnow().isoformat(),
    }
