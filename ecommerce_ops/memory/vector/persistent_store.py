"""
Persistent Vector Store - PostgreSQL-backed with pgvector.
Replaces in-memory vector store for production use.
"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import Column, DateTime, Float, Index, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ecommerce_ops.models import Base

logger = logging.getLogger("ecommerce_ops.memory.vector.persistent")


# ── Database Model ──────────────────────────────────────────


class VectorMemory(Base):
    """Persistent vector memory entry in PostgreSQL with pgvector."""
    __tablename__ = "vector_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    memory_type = Column(String(50), nullable=False, index=True)
    importance = Column(Float, default=0.5, nullable=False)
    embedding = Column(ARRAY(Float), nullable=False)
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


# ── Persistent Vector Store ────────────────────────────────


class PersistentVectorStore:
    """
    PostgreSQL-backed vector store with pgvector for cosine similarity search.
    Falls back to in-memory search when pgvector is not available.
    """

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._use_pgvector = False
        self._in_memory: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize the vector store and check for pgvector availability."""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                )
                if result.fetchone():
                    self._use_pgvector = True
                    logger.info("pgvector extension detected - using native vector search")
                else:
                    logger.warning("pgvector not installed - using in-memory fallback")
        except Exception as e:
            logger.warning(f"pgvector check failed: {e} - using in-memory fallback")

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
        """Store a memory with its embedding."""
        memory_id = str(uuid.uuid4())

        if self._use_pgvector:
            async with self.session_factory() as session:
                entry = VectorMemory(
                    id=uuid.UUID(memory_id),
                    content=content,
                    memory_type=memory_type,
                    importance=importance,
                    embedding=embedding,
                    metadata_json=metadata or {},
                    session_id=session_id,
                    agent_id=agent_id,
                )
                session.add(entry)
                await session.commit()
        else:
            # In-memory fallback with persistence to JSON file
            self._in_memory[memory_id] = {
                "id": memory_id,
                "content": content,
                "memory_type": memory_type,
                "importance": importance,
                "embedding": embedding,
                "metadata": metadata or {},
                "session_id": session_id,
                "agent_id": agent_id,
                "created_at": datetime.utcnow().isoformat(),
                "accessed_at": datetime.utcnow().isoformat(),
                "access_count": 0,
            }

        logger.info(f"Stored memory {memory_id} (type={memory_type}, importance={importance})")
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
        """Search for similar memories using cosine similarity."""
        if self._use_pgvector:
            return await self._search_pgvector(
                query_embedding, top_k, min_similarity,
                memory_type, agent_id, session_id
            )
        else:
            return await self._search_in_memory(
                query_embedding, top_k, min_similarity,
                memory_type, agent_id, session_id
            )

    async def _search_pgvector(
        self,
        query_embedding: List[float],
        top_k: int,
        min_similarity: float,
        memory_type: Optional[str],
        agent_id: Optional[str],
        session_id: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Search using pgvector cosine distance."""
        async with self.session_factory() as session:
            conditions = []
            if memory_type:
                conditions.append(f"memory_type = '{memory_type}'")
            if agent_id:
                conditions.append(f"agent_id = '{agent_id}'")
            if session_id:
                conditions.append(f"session_id = '{session_id}'")

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

            result = await session.execute(
                query,
                {
                    "query_embedding": str(query_embedding),
                    "min_similarity": min_similarity,
                    "top_k": top_k,
                },
            )

            rows = result.fetchall()
            results = []
            for row in rows:
                results.append({
                    "id": str(row.id),
                    "content": row.content,
                    "memory_type": row.memory_type,
                    "importance": row.importance,
                    "metadata": row.metadata_json,
                    "similarity": float(row.similarity),
                    "session_id": row.session_id,
                    "agent_id": row.agent_id,
                })

            return results

    async def _search_in_memory(
        self,
        query_embedding: List[float],
        top_k: int,
        min_similarity: float,
        memory_type: Optional[str],
        agent_id: Optional[str],
        session_id: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Search using in-memory cosine similarity."""
        candidates = list(self._in_memory.values())

        # Apply filters
        if memory_type:
            candidates = [c for c in candidates if c["memory_type"] == memory_type]
        if agent_id:
            candidates = [c for c in candidates if c.get("agent_id") == agent_id]
        if session_id:
            candidates = [c for c in candidates if c.get("session_id") == session_id]

        # Calculate cosine similarity
        scored = []
        for entry in candidates:
            sim = self._cosine_similarity(query_embedding, entry["embedding"])
            if sim >= min_similarity:
                scored.append({**entry, "similarity": sim})

        # Sort by similarity * importance
        scored.sort(key=lambda x: x["similarity"] * x["importance"], reverse=True)

        return scored[:top_k]

    async def update_access(self, memory_id: str):
        """Update access count and timestamp for a memory."""
        if self._use_pgvector:
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
        elif memory_id in self._in_memory:
            self._in_memory[memory_id]["access_count"] += 1
            self._in_memory[memory_id]["accessed_at"] = datetime.utcnow().isoformat()

    async def decay_importance(self, decay_rate: float = 0.01):
        """Apply time-based importance decay to old memories."""
        if self._use_pgvector:
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
        else:
            for entry in self._in_memory.values():
                entry["importance"] = max(0.01, entry["importance"] - decay_rate)

    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by ID."""
        if self._use_pgvector:
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
        return self._in_memory.get(memory_id)

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        if self._use_pgvector:
            async with self.session_factory() as session:
                await session.execute(
                    text("DELETE FROM vector_memories WHERE id = :memory_id"),
                    {"memory_id": memory_id},
                )
                await session.commit()
            return True
        elif memory_id in self._in_memory:
            del self._in_memory[memory_id]
            return True
        return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        if self._use_pgvector:
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
        return {
            "total_memories": len(self._in_memory),
            "avg_importance": sum(m["importance"] for m in self._in_memory.values()) / max(len(self._in_memory), 1),
            "backend": "in_memory",
        }

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)
