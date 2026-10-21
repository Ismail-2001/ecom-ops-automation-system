"""Add vector_memories table (pgvector-backed agent memory)

Revision ID: 0016
Revises: 0015
Create Date: 2026-08-21

Persistent vector memory for agents. Uses pgvector for cosine similarity
search.

Idempotent: repair migration 0005 already creates ``vector_memories`` (from
the ORM model) plus the ``vector`` extension on fresh databases, so this
revision only fills gaps and never re-creates existing relations.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSIONS = 1536


def _inspector():
    return sa.inspect(op.get_bind())


def upgrade() -> None:
    insp = _inspector()

    if "vector_memories" not in insp.get_table_names():
        op.create_table(
            "vector_memories",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("memory_type", sa.String(50), nullable=False),
            sa.Column(
                "importance", sa.Float(), nullable=False, server_default=sa.text("0.5")
            ),
            sa.Column("embedding", sa.Text(), nullable=True),
            sa.Column("embedding_vec", Vector(EMBEDDING_DIMENSIONS), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("session_id", sa.String(100), nullable=True),
            sa.Column("agent_id", sa.String(100), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("accessed_at", sa.DateTime(), nullable=False),
            sa.Column(
                "access_count", sa.Float(), nullable=False, server_default=sa.text("0")
            ),
            sa.Column("last_decay_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    existing = {ix["name"] for ix in insp.get_indexes("vector_memories")}
    desired = [
        ("ix_vector_memories_memory_type", ["memory_type"]),
        ("ix_vector_memories_session_id", ["session_id"]),
        ("ix_vector_memories_agent_id", ["agent_id"]),
        ("idx_vector_memories_importance", ["importance"]),
        ("idx_vector_memories_created", ["created_at"]),
        ("idx_vector_memories_agent", ["agent_id"]),
    ]
    for name, cols in desired:
        if name not in existing:
            op.create_index(name, "vector_memories", cols)


def downgrade() -> None:
    insp = _inspector()
    if "vector_memories" not in insp.get_table_names():
        return
    existing = {ix["name"] for ix in insp.get_indexes("vector_memories")}
    for name in [
        "idx_vector_memories_agent",
        "idx_vector_memories_created",
        "idx_vector_memories_importance",
        "ix_vector_memories_agent_id",
        "ix_vector_memories_session_id",
        "ix_vector_memories_memory_type",
    ]:
        if name in existing:
            op.drop_index(name, table_name="vector_memories")
    op.drop_table("vector_memories")
