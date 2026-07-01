"""
Role Management Service (PostgreSQL-backed)
Manages roles, users, and permission checks with persistent storage.
"""

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ecommerce_ops.models.db import RBACUser, RBACApiKey, async_session_factory
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


def _hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256 for secure storage."""
    return hashlib.sha256(key.encode()).hexdigest()


class RoleManager:
    """Manages roles, users, and permissions with PostgreSQL persistence."""

    def __init__(self):
        self._roles: Dict[str, RoleDefinition] = {
            role.value: defn for role, defn in DEFAULT_ROLES.items()
        }

    # ── Role Management (in-memory, rarely changes) ────────

    def get_role(self, role) -> Optional[RoleDefinition]:
        if isinstance(role, Role):
            return self._roles.get(role.value)
        return self._roles.get(str(role))

    def list_roles(self) -> List[RoleDefinition]:
        return list(self._roles.values())

    def create_role(
        self,
        name: str,
        display_name: str,
        description: str,
        permissions: Set[Permission],
    ) -> RoleDefinition:
        if name in self._roles:
            raise ValueError(f"Role {name} already exists")
        role_enum = Role(name) if name in {r.value for r in Role} else None
        definition = RoleDefinition(
            name=role_enum if role_enum else Role.VIEWER,
            display_name=display_name,
            description=description,
            permissions=permissions,
            is_system=False,
        )
        self._roles[name] = definition
        logger.info("Created role: %s", name)
        return definition

    def update_role_permissions(self, role, permissions: Set[Permission]) -> bool:
        key = role.value if isinstance(role, Role) else str(role)
        definition = self._roles.get(key)
        if not definition:
            return False
        if definition.is_system:
            logger.warning("Cannot modify system role: %s", role)
            return False
        definition.permissions = permissions
        definition.updated_at = datetime.utcnow()
        return True

    def delete_role(self, role) -> bool:
        key = role.value if isinstance(role, Role) else str(role)
        definition = self._roles.get(key)
        if not definition:
            return False
        if definition.is_system:
            return False
        del self._roles[key]
        return True

    # ── User Management (PostgreSQL) ──────────────────────

    async def create_user(
        self,
        email: str,
        name: Optional[str] = None,
        role: Role = Role.VIEWER,
        permissions: Optional[Set[Permission]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> User:
        async with async_session_factory() as session:
            # Check duplicate email
            existing = await session.execute(
                select(RBACUser).where(RBACUser.email == email)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"User with email {email} already exists")

            user_id = str(uuid.uuid4())
            db_user = RBACUser(
                id=user_id,
                email=email,
                name=name,
                role=role.value,
                is_active=True,
                permissions=[p.value for p in (permissions or set())],
                metadata_json=metadata or {},
            )
            session.add(db_user)
            await session.commit()

            logger.info("Created user: %s (email=%s, role=%s)", user_id, email, role)
            return User(
                id=user_id,
                email=email,
                name=name,
                role=role,
                permissions=permissions or set(),
                metadata=metadata or {},
            )

    async def get_user(self, user_id: str) -> Optional[User]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(RBACUser).where(RBACUser.id == user_id)
            )
            db_user = result.scalar_one_or_none()
            if not db_user:
                return None
            return self._db_to_user(db_user)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(RBACUser).where(RBACUser.email == email)
            )
            db_user = result.scalar_one_or_none()
            if not db_user:
                return None
            return self._db_to_user(db_user)

    async def list_users(
        self,
        role: Optional[Role] = None,
        is_active: Optional[bool] = None,
    ) -> List[User]:
        async with async_session_factory() as session:
            stmt = select(RBACUser)
            if role:
                stmt = stmt.where(RBACUser.role == role.value)
            if is_active is not None:
                stmt = stmt.where(RBACUser.is_active == is_active)
            result = await session.execute(stmt.order_by(RBACUser.created_at.desc()))
            return [self._db_to_user(u) for u in result.scalars().all()]

    async def update_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        role: Optional[Role] = None,
        is_active: Optional[bool] = None,
        permissions: Optional[Set[Permission]] = None,
    ) -> bool:
        async with async_session_factory() as session:
            result = await session.execute(
                select(RBACUser).where(RBACUser.id == user_id)
            )
            db_user = result.scalar_one_or_none()
            if not db_user:
                return False

            if name is not None:
                db_user.name = name
            if role is not None:
                db_user.role = role.value
            if is_active is not None:
                db_user.is_active = is_active
            if permissions is not None:
                db_user.permissions = [p.value for p in permissions]
            db_user.updated_at = datetime.utcnow()

            await session.commit()
            logger.info("Updated user: %s", user_id)
            return True

    async def delete_user(self, user_id: str) -> bool:
        async with async_session_factory() as session:
            result = await session.execute(
                select(RBACUser).where(RBACUser.id == user_id)
            )
            db_user = result.scalar_one_or_none()
            if not db_user:
                return False
            await session.delete(db_user)
            await session.commit()
            logger.info("Deleted user: %s", user_id)
            return True

    async def record_login(self, user_id: str) -> bool:
        async with async_session_factory() as session:
            result = await session.execute(
                select(RBACUser).where(RBACUser.id == user_id)
            )
            db_user = result.scalar_one_or_none()
            if not db_user:
                return False
            db_user.last_login = datetime.utcnow()
            db_user.login_count = (db_user.login_count or 0) + 1
            await session.commit()
            return True

    # ── Permission Checks ──────────────────────────────────

    def check_permission(self, user: User, permission: Permission) -> PermissionCheck:
        if not user.is_active:
            return PermissionCheck(
                allowed=False,
                reason="User account is inactive",
                role=user.role,
            )
        role_def = self._roles.get(user.role)
        if role_def and permission in role_def.permissions:
            return PermissionCheck(allowed=True, role=user.role)
        if permission in user.permissions:
            return PermissionCheck(allowed=True, role=user.role)
        return PermissionCheck(
            allowed=False,
            reason=f"Permission {permission.value} not granted",
            role=user.role,
            missing_permissions=[permission],
        )

    def check_permissions(self, user: User, permissions: Set[Permission]) -> PermissionCheck:
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
        permissions: Set[Permission] = set()
        role_def = self._roles.get(user.role)
        if role_def:
            permissions.update(role_def.permissions)
        permissions.update(user.permissions)
        return permissions

    # ── API Key Management (PostgreSQL) ────────────────────

    async def create_api_key(
        self,
        user_id: str,
        name: str,
        role: Role,
        expires_days: Optional[int] = 90,
        permissions: Optional[Set[Permission]] = None,
    ) -> APIKey:
        async with async_session_factory() as session:
            result = await session.execute(
                select(RBACUser).where(RBACUser.id == user_id)
            )
            if not result.scalar_one_or_none():
                raise ValueError(f"User {user_id} not found")

            key_id = str(uuid.uuid4())
            raw_key = f"eops_{secrets.token_urlsafe(32)}"
            key_hash = _hash_api_key(raw_key)
            key_prefix = raw_key[:12] + "..."

            expires_at = None
            if expires_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)

            db_key = RBACApiKey(
                id=key_id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                name=name,
                user_id=user_id,
                role=role.value,
                permissions=[p.value for p in (permissions or set())],
                is_active=True,
                expires_at=expires_at,
            )
            session.add(db_key)
            await session.commit()

            logger.info("Created API key: %s for user %s", key_id, user_id)
            return APIKey(
                id=key_id,
                key=raw_key,
                name=name,
                user_id=user_id,
                role=role,
                permissions=permissions or set(),
                expires_at=expires_at,
            )

    async def validate_api_key(self, key: str) -> Optional[APIKey]:
        key_hash = _hash_api_key(key)
        async with async_session_factory() as session:
            result = await session.execute(
                select(RBACApiKey).where(
                    RBACApiKey.key_hash == key_hash,
                    RBACApiKey.is_active == True,
                )
            )
            db_key = result.scalar_one_or_none()
            if not db_key:
                return None
            if db_key.expires_at and datetime.utcnow() > db_key.expires_at:
                return None

            db_key.last_used = datetime.utcnow()
            db_key.usage_count = (db_key.usage_count or 0) + 1
            await session.commit()

            return APIKey(
                id=db_key.id,
                key=key,
                name=db_key.name,
                user_id=db_key.user_id,
                role=Role(db_key.role),
                permissions={Permission(p) for p in (db_key.permissions or [])},
                is_active=db_key.is_active,
                expires_at=db_key.expires_at,
                last_used=db_key.last_used,
                usage_count=db_key.usage_count,
            )

    async def revoke_api_key(self, key_id: str) -> bool:
        async with async_session_factory() as session:
            result = await session.execute(
                select(RBACApiKey).where(RBACApiKey.id == key_id)
            )
            db_key = result.scalar_one_or_none()
            if not db_key:
                return False
            db_key.is_active = False
            await session.commit()
            logger.info("Revoked API key: %s", key_id)
            return True

    async def list_api_keys(
        self,
        user_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[APIKey]:
        async with async_session_factory() as session:
            stmt = select(RBACApiKey)
            if user_id:
                stmt = stmt.where(RBACApiKey.user_id == user_id)
            if is_active is not None:
                stmt = stmt.where(RBACApiKey.is_active == is_active)
            result = await session.execute(stmt.order_by(RBACApiKey.created_at.desc()))
            return [
                APIKey(
                    id=k.id,
                    key=k.key_prefix,
                    name=k.name,
                    user_id=k.user_id,
                    role=Role(k.role),
                    permissions={Permission(p) for p in (k.permissions or [])},
                    is_active=k.is_active,
                    expires_at=k.expires_at,
                    last_used=k.last_used,
                    usage_count=k.usage_count,
                )
                for k in result.scalars().all()
            ]

    # ── Initialization ─────────────────────────────────────

    async def create_default_admin(
        self,
        email: str = "admin@example.com",
        password: Optional[str] = None,
    ) -> User:
        existing = await self.get_user_by_email(email)
        if existing:
            return existing
        return await self.create_user(
            email=email,
            name="Admin",
            role=Role.SUPER_ADMIN,
            metadata={"is_default_admin": True},
        )

    # ── Helpers ────────────────────────────────────────────

    def _db_to_user(self, db_user: RBACUser) -> User:
        return User(
            id=db_user.id,
            email=db_user.email,
            name=db_user.name,
            role=Role(db_user.role),
            is_active=db_user.is_active,
            permissions={Permission(p) for p in (db_user.permissions or [])},
            metadata=db_user.metadata_json or {},
            created_at=db_user.created_at,
            last_login=db_user.last_login,
            login_count=db_user.login_count or 0,
        )


# Singleton
role_manager = RoleManager()
