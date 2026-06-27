"""
Role Management Service
Manages roles, users, and permission checks.
"""

import logging
import secrets
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from ecommerce_ops.security.models import (
    APIKey,
    DEFAULT_ROLES,
    Permission,
    PermissionCheck,
    Role,
    RoleDefinition,
    User,
)

logger = logging.getLogger("ecommerce_ops.security.role_manager")


class RoleManager:
    """Manages roles, users, and permissions."""

    def __init__(self):
        self._roles: Dict[Role, RoleDefinition] = dict(DEFAULT_ROLES)
        self._users: Dict[str, User] = {}
        self._api_keys: Dict[str, APIKey] = {}

    # ── Role Management ────────────────────────────────────

    def get_role(self, role: Role) -> Optional[RoleDefinition]:
        """Get role definition."""
        return self._roles.get(role)

    def list_roles(self) -> List[RoleDefinition]:
        """List all roles."""
        return list(self._roles.values())

    def create_role(
        self,
        name: str,
        display_name: str,
        description: str,
        permissions: Set[Permission],
    ) -> RoleDefinition:
        """Create a custom role."""
        role = Role(name)
        if role in self._roles:
            raise ValueError(f"Role {name} already exists")

        definition = RoleDefinition(
            name=role,
            display_name=display_name,
            description=description,
            permissions=permissions,
            is_system=False,
        )

        self._roles[role] = definition
        logger.info("Created role: %s", name)
        return definition

    def update_role_permissions(
        self,
        role: Role,
        permissions: Set[Permission],
    ) -> bool:
        """Update role permissions."""
        definition = self._roles.get(role)
        if not definition:
            return False

        if definition.is_system:
            logger.warning("Cannot modify system role: %s", role)
            return False

        definition.permissions = permissions
        definition.updated_at = datetime.utcnow()
        logger.info("Updated permissions for role: %s", role)
        return True

    def delete_role(self, role: Role) -> bool:
        """Delete a custom role."""
        definition = self._roles.get(role)
        if not definition:
            return False

        if definition.is_system:
            logger.warning("Cannot delete system role: %s", role)
            return False

        del self._roles[role]
        logger.info("Deleted role: %s", role)
        return True

    # ── User Management ────────────────────────────────────

    def create_user(
        self,
        email: str,
        name: Optional[str] = None,
        role: Role = Role.VIEWER,
        permissions: Optional[Set[Permission]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> User:
        """Create a new user."""
        user_id = str(uuid.uuid4())

        # Check if email already exists
        for user in self._users.values():
            if user.email == email:
                raise ValueError(f"User with email {email} already exists")

        user = User(
            id=user_id,
            email=email,
            name=name,
            role=role,
            permissions=permissions or set(),
            metadata=metadata or {},
        )

        self._users[user_id] = user
        logger.info("Created user: %s (email=%s, role=%s)", user_id, email, role)
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    def list_users(
        self,
        role: Optional[Role] = None,
        is_active: Optional[bool] = None,
    ) -> List[User]:
        """List users with filters."""
        users = list(self._users.values())

        if role:
            users = [u for u in users if u.role == role]
        if is_active is not None:
            users = [u for u in users if u.is_active == is_active]

        return users

    def update_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        role: Optional[Role] = None,
        is_active: Optional[bool] = None,
        permissions: Optional[Set[Permission]] = None,
    ) -> bool:
        """Update user."""
        user = self._users.get(user_id)
        if not user:
            return False

        if name is not None:
            user.name = name
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        if permissions is not None:
            user.permissions = permissions

        logger.info("Updated user: %s", user_id)
        return True

    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        if user_id not in self._users:
            return False

        del self._users[user_id]
        logger.info("Deleted user: %s", user_id)
        return True

    def record_login(self, user_id: str) -> bool:
        """Record user login."""
        user = self._users.get(user_id)
        if not user:
            return False

        user.last_login = datetime.utcnow()
        user.login_count += 1
        return True

    # ── Permission Checks ──────────────────────────────────

    def check_permission(
        self,
        user: User,
        permission: Permission,
    ) -> PermissionCheck:
        """Check if user has a specific permission."""
        if not user.is_active:
            return PermissionCheck(
                allowed=False,
                reason="User account is inactive",
                role=user.role,
            )

        # Check role permissions
        role_def = self._roles.get(user.role)
        if role_def and permission in role_def.permissions:
            return PermissionCheck(allowed=True, role=user.role)

        # Check user-specific permissions
        if permission in user.permissions:
            return PermissionCheck(allowed=True, role=user.role)

        return PermissionCheck(
            allowed=False,
            reason=f"Permission {permission.value} not granted",
            role=user.role,
            missing_permissions=[permission],
        )

    def check_permissions(
        self,
        user: User,
        permissions: Set[Permission],
    ) -> PermissionCheck:
        """Check if user has all specified permissions."""
        missing = []

        for permission in permissions:
            result = self.check_permission(user, permission)
            if not result.allowed:
                missing.extend(result.missing_permissions)

        if missing:
            return PermissionCheck(
                allowed=False,
                reason=f"Missing {len(missing)} permissions",
                role=user.role,
                missing_permissions=missing,
            )

        return PermissionCheck(allowed=True, role=user.role)

    def get_user_permissions(self, user: User) -> Set[Permission]:
        """Get all permissions for a user."""
        permissions = set()

        # Add role permissions
        role_def = self._roles.get(user.role)
        if role_def:
            permissions.update(role_def.permissions)

        # Add user-specific permissions
        permissions.update(user.permissions)

        return permissions

    # ── API Key Management ─────────────────────────────────

    def create_api_key(
        self,
        user_id: str,
        name: str,
        role: Role,
        expires_days: Optional[int] = 90,
        permissions: Optional[Set[Permission]] = None,
    ) -> APIKey:
        """Create an API key for a user."""
        user = self._users.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        key_id = str(uuid.uuid4())
        key_value = f"eops_{secrets.token_urlsafe(32)}"

        expires_at = None
        if expires_days:
            from datetime import timedelta
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        api_key = APIKey(
            id=key_id,
            key=key_value,
            name=name,
            user_id=user_id,
            role=role,
            permissions=permissions or set(),
            expires_at=expires_at,
        )

        self._api_keys[key_id] = api_key
        logger.info("Created API key: %s for user %s", key_id, user_id)
        return api_key

    def validate_api_key(self, key: str) -> Optional[APIKey]:
        """Validate an API key."""
        for api_key in self._api_keys.values():
            if api_key.key == key and api_key.is_active:
                if not api_key.is_expired:
                    api_key.last_used = datetime.utcnow()
                    api_key.usage_count += 1
                    return api_key
        return None

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        api_key = self._api_keys.get(key_id)
        if not api_key:
            return False

        api_key.is_active = False
        logger.info("Revoked API key: %s", key_id)
        return True

    def list_api_keys(
        self,
        user_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[APIKey]:
        """List API keys with filters."""
        keys = list(self._api_keys.values())

        if user_id:
            keys = [k for k in keys if k.user_id == user_id]
        if is_active is not None:
            keys = [k for k in keys if k.is_active == is_active]

        return keys

    # ── Initialization ─────────────────────────────────────

    def create_default_admin(
        self,
        email: str = "admin@example.com",
        password: Optional[str] = None,
    ) -> User:
        """Create default admin user."""
        admin = self.create_user(
            email=email,
            name="Admin",
            role=Role.SUPER_ADMIN,
            metadata={"is_default_admin": True},
        )
        logger.info("Created default admin user: %s", admin.id)
        return admin


# Singleton
role_manager = RoleManager()
