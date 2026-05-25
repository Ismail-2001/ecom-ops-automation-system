import os
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    JSON,
    create_engine,
    select
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker

from ecommerce_ops.config import settings

logger = logging.getLogger("ecommerce_ops.db")

# Fallback engine resolution
db_url = settings.DATABASE_URL
# If we don't have asyncpg or postgres running, we'll try a local sqlite database.
if db_url.startswith("postgresql"):
    # Check if aiosqlite is used as a fallback if PostgreSQL connection fails
    pass

# We will create an async connection url
# If we detect that the engine should use SQLite, we format it as sqlite+aiosqlite
is_sqlite = False
if "postgresql" not in db_url:
    is_sqlite = True
    db_url = "sqlite+aiosqlite:///./ecommerce_ops.db"

# Create async engine with connection pooling
try:
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,
    )
except Exception as e:
    logger.warning(f"Failed to create async engine with {db_url}: {e}. Falling back to local SQLite.")
    is_sqlite = True
    db_url = "sqlite+aiosqlite:///./ecommerce_ops.db"
    engine = create_async_engine(db_url, echo=False, future=True)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

class ApprovalAction(Base):
    __tablename__ = "approval_actions"

    id = Column(String, primary_key=True)
    agent = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False) # pending, approved, rejected, executing, executed, failed, expired, shadow
    risk_level = Column(String, default="low", nullable=False) # low, medium, high, critical
    confidence_score = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
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
    action_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    agent = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    decision = Column(String, nullable=False) # approved, rejected, auto-approved, shadow
    operator = Column(String, nullable=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    financial_impact = Column(Float, nullable=True)
    details = Column(JSON, nullable=True)

class AgentStatus(Base):
    __tablename__ = "agent_status"

    agent_id = Column(String, primary_key=True) # FraudAgent, InventoryAgent, etc.
    status = Column(String, default="active", nullable=False) # active, paused
    streak = Column(Integer, default=0, nullable=False) # Consecutive approvals
    autonomy_level = Column(String, default="supervised", nullable=False) # shadow, supervised, autonomous
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
        # SQLite doesn't support pgvector, but we are using native Column(JSON) or custom columns.
        # Create all tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize default settings and agent entries if missing
    async with async_session_factory() as session:
        # Check settings
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
        
        # Check agents status
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
                logger.info(f"Initialized agent status for {agent_name}")
        
        await session.commit()
