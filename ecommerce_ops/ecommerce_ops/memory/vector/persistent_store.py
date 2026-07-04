"""
Persistent Vector Store - PostgreSQL-backed with pgvector.
Requires PostgreSQL with pgvector extension for production use.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Float, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ecommerce_ops.models import Base

logger = logging.getLogger("ecommerce_ops.memory.vector.persistent")


class VectorMemory(Base):
    """Persistent vector memory entry in PostgreSQL with pgvector."""
    __tablename__ = "vector_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    memory_type = Column(String(50), nullable=False, index=True)
    importance = Column(Float, default=0.5, nullable=False)
    embedding = Column(Text, nullable=False)  # JSON-serialized list
    metadata_json = Column(JSONB, default={})
    session_id = Column(String(100), index=True, nullable=True)
    agent_id = Column(String(100), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    access_count = Column(Float, default=0)
    last_decay_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_vector_memories_importance", "importance"),
        Index("idx_vector_memories_created", "created_at"),
        Index("idx_vector_memories_agent", "agent_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "metadata": self.metadata_json or {},
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
            "access_count": self.access_count,
        }


class PersistentVectorStore:
    """
    PostgreSQL-backed vector store with pgvector for cosine similarity search.
    Requires PostgreSQL with pgvector extension.
    """

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._pgvector_available = False

    async def initialize(self):
        """Check pgvector availability. Logs error if unavailable."""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                )
                if result.fetchone():
                    self._pgvector_available = True
                    logger.info("pgvector extension detected - native vector search enabled")
                else:
                    logger.error("pgvector NOT installed - vector memory will degrade")
        except Exception as e:
            logger.error("pgvector check failed: %s - vector memory will degrade", e)

    async def store(
        self,
        content: str,
        embedding: List[float],
        memory_type: str = "episodic",
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> str:
        memory_id = str(uuid.uuid4())

        async with self.session_factory() as session:
            entry = VectorMemory(
                id=uuid.UUID(memory_id),
                content=content,
                memory_type=memory_type,
                importance=importance,
                embedding=json.dumps(embedding),
                metadata_json=metadata or {},
                session_id=session_id,
                agent_id=agent_id,
            )
            session.add(entry)
            await session.commit()

        logger.info("Stored memory %s (type=%s, importance=%.2f)", memory_id, memory_type, importance)
        return memory_id

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        min_similarity: float = 0.5,
        memory_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        async with self.session_factory() as session:
            conditions = []
            params: dict = {
                "query_embedding": json.dumps(query_embedding),
                "min_similarity": min_similarity,
                "top_k": top_k,
            }

            if memory_type:
                conditions.append("memory_type = :memory_type")
                params["memory_type"] = memory_type
            if agent_id:
                conditions.append("agent_id = :agent_id")
                params["agent_id"] = agent_id
            if session_id:
                conditions.append("session_id = :session_id")
                params["session_id"] = session_id

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = text(f"""
                SELECT id, content, memory_type, importance, metadata_json,
                       session_id, agent_id, created_at, accessed_at, access_count,
                       1 - (embedding <=> :query_embedding::vector) as similarity
                FROM vector_memories
                WHERE {where_clause}
                  AND 1 - (embedding <=> :query_embedding::vector) >= :min_similarity
                ORDER BY similarity DESC
                LIMIT :top_k
            """)

            result = await session.execute(query, params)
            rows = result.fetchall()

            return [
                {
                    "id": str(row.id),
                    "content": row.content,
                    "memory_type": row.memory_type,
                    "importance": row.importance,
                    "metadata": row.metadata_json,
                    "similarity": float(row.similarity),
                    "session_id": row.session_id,
                    "agent_id": row.agent_id,
                }
                for row in rows
            ]

    async def update_access(self, memory_id: str):
        async with self.session_factory() as session:
            await session.execute(
                text("""
                    UPDATE vector_memories
                    SET access_count = access_count + 1,
                        accessed_at = :now
                    WHERE id = :memory_id
                """),
                {"memory_id": memory_id, "now": datetime.utcnow()},
            )
            await session.commit()

    async def decay_importance(self, decay_rate: float = 0.01):
        async with self.session_factory() as session:
            await session.execute(
                text("""
                    UPDATE vector_memories
                    SET importance = GREATEST(0.01, importance - :decay_rate)
                    WHERE last_decay_at < :threshold
                """),
                {"decay_rate": decay_rate, "threshold": datetime.utcnow() - timedelta(days=1)},
            )
            await session.commit()

    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            result = await session.execute(
                text("SELECT * FROM vector_memories WHERE id = :memory_id"),
                {"memory_id": memory_id},
            )
            row = result.fetchone()
            if row:
                return {
                    "id": str(row.id),
                    "content": row.content,
                    "memory_type": row.memory_type,
                    "importance": row.importance,
                    "metadata": row.metadata_json,
                }
        return None

    async def delete_memory(self, memory_id: str) -> bool:
        async with self.session_factory() as session:
            await session.execute(
                text("DELETE FROM vector_memories WHERE id = :memory_id"),
                {"memory_id": memory_id},
            )
            await session.commit()
        return True

    async def get_stats(self) -> Dict[str, Any]:
        async with self.session_factory() as session:
            result = await session.execute(
                text("SELECT COUNT(*) as total, AVG(importance) as avg_importance FROM vector_memories")
            )
            row = result.fetchone()
            return {
                "total_memories": row.total if row else 0,
                "avg_importance": float(row.avg_importance) if row and row.avg_importance else 0,
                "backend": "pgvector",
            }
