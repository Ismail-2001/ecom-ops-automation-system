import logging
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    JSON,
    Text,
    Index,
    ForeignKey,
    select,
    text,
    func,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from ecommerce_ops.config import settings, Environment

logger = logging.getLogger("ecommerce_ops.db")

db_url = settings.DATABASE_URL

is_sqlite = "sqlite" in db_url
if settings.ENV == Environment.PRODUCTION and is_sqlite:
    raise RuntimeError(
        "SQLite is not supported in production. Set DATABASE_URL to a PostgreSQL connection string."
    )

engine_kwargs = {
    "echo": False,
    "future": True,
}

if is_sqlite:
    engine_kwargs["connect_args"] = {"timeout": 15}
else:
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600

engine = create_async_engine(db_url, **engine_kwargs)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class ApprovalAction(Base):
    __tablename__ = "approval_actions"

    id = Column(String, primary_key=True)
    agent = Column(String, nullable=False, index=True)
    action_type = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False, index=True)
    risk_level = Column(String, default="low", nullable=False, index=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    requires_hitl = Column(Boolean, default=True, nullable=False)
    shadow_mode = Column(Boolean, default=True, nullable=False)

    payload = Column(JSON, nullable=False)
    evidence = Column(JSON, nullable=False)
    impact = Column(JSON, nullable=False)

    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String, nullable=True)
    operator_notes = Column(String, nullable=True)


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(String, ForeignKey("approval_actions.id"), nullable=True)
    timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)
    agent = Column(String, nullable=False, index=True)
    action_type = Column(String, nullable=False, index=True)
    decision = Column(String, nullable=False, index=True)
    operator = Column(String, nullable=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    financial_impact = Column(Float, nullable=True)
    details = Column(JSON, nullable=True)


class AgentStatus(Base):
    __tablename__ = "agent_status"

    agent_id = Column(String, primary_key=True)
    status = Column(String, default="active", nullable=False)
    streak = Column(Integer, default=0, nullable=False)
    autonomy_level = Column(String, default="supervised", nullable=False)
    total_decisions = Column(Integer, default=0, nullable=False)
    total_approvals = Column(Integer, default=0, nullable=False)
    total_rejections = Column(Integer, default=0, nullable=False)
    avg_confidence = Column(Float, default=0.0, nullable=False)


class StoreSettings(Base):
    __tablename__ = "store_settings"

    id = Column(Integer, primary_key=True, default=1)
    shadow_mode = Column(Boolean, default=True, nullable=False)
    fraud_threshold = Column(Integer, default=70, nullable=False)
    po_limit = Column(Float, default=1000.0, nullable=False)
    pricing_limit = Column(Float, default=5.0, nullable=False)
    reviews_rating_threshold = Column(Integer, default=4, nullable=False)


# ── RBAC Models (Persistent) ──────────────────────────────

class RBACUser(Base):
    __tablename__ = "rbac_users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    role = Column(String, nullable=False, default="viewer", index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    permissions = Column(JSON, default=list, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("idx_rbac_users_role_active", "role", "is_active"),
    )


class RBACApiKey(Base):
    __tablename__ = "rbac_api_keys"

    id = Column(String, primary_key=True)
    key_hash = Column(String, unique=True, nullable=False, index=True)
    key_prefix = Column(String, nullable=False)
    name = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("rbac_users.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    permissions = Column(JSON, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)


# ── Security Audit Log (Persistent) ───────────────────────

class SecurityAuditLog(Base):
    __tablename__ = "security_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    resource = Column(String, nullable=False, index=True)
    resource_id = Column(String, nullable=True)
    user_id = Column(String, ForeignKey("rbac_users.id"), nullable=True, index=True)
    user_email = Column(String, nullable=True)
    api_key_id = Column(String, ForeignKey("rbac_api_keys.id"), nullable=True)
    role = Column(String, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    details = Column(JSON, default=dict, nullable=False)
    risk_level = Column(String, nullable=False, default="low", index=True)
    timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_security_audit_type_time", "event_type", "timestamp"),
        Index("idx_security_audit_risk", "risk_level", "timestamp"),
    )


# Async Generator for DB sessions
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Database initialization helper
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        result = await session.execute(select(StoreSettings).where(StoreSettings.id == 1))
        db_settings = result.scalar_one_or_none()
        if not db_settings:
            session.add(StoreSettings(
                id=1,
                shadow_mode=settings.SHADOW_MODE,
                fraud_threshold=70,
                po_limit=settings.GLOBAL_PO_LIMIT,
                pricing_limit=settings.GLOBAL_PRICE_CHANGE_LIMIT_PERCENT,
                reviews_rating_threshold=4
            ))
            logger.info("Initialized default store settings")

        agents = ["FraudAgent", "InventoryAgent", "PricingAgent", "ReviewsAgent", "MarketingAgent"]
        for agent_name in agents:
            res = await session.execute(select(AgentStatus).where(AgentStatus.agent_id == agent_name))
            agent_status = res.scalar_one_or_none()
            if not agent_status:
                session.add(AgentStatus(
                    agent_id=agent_name,
                    status="active",
                    streak=0,
                    autonomy_level="shadow" if settings.SHADOW_MODE else "supervised",
                    total_decisions=0,
                    total_approvals=0,
                    total_rejections=0,
                    avg_confidence=0.0
                ))
                logger.info("Initialized agent status for %s", agent_name)

        result = await session.execute(select(RBACUser).where(RBACUser.role == "super_admin"))
        if not result.scalar_one_or_none():
            import uuid
            admin = RBACUser(
                id=str(uuid.uuid4()),
                email="admin@example.com",
                name="Admin",
                role="super_admin",
                is_active=True,
                permissions=[],
                metadata_json={"is_default_admin": True},
            )
            session.add(admin)
            logger.info("Seeded default admin user")

        await session.commit()
