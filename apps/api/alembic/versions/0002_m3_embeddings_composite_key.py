"""m3 embeddings composite key and vector index

Revision ID: 0002_m3_embeddings_composite_key
Revises: 0001_initial_schema
Create Date: 2026-05-10
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_m3_embeddings_composite_key"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("chunk_embeddings_pkey", "chunk_embeddings", type_="primary")
    op.create_primary_key(
        "chunk_embeddings_pkey",
        "chunk_embeddings",
        ["chunk_id", "embedding_model"],
    )
    op.create_index(
        "idx_chunk_embeddings_model",
        "chunk_embeddings",
        ["embedding_model"],
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_vector "
        "ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_chunk_embeddings_vector")
    op.drop_index("idx_chunk_embeddings_model", table_name="chunk_embeddings")
    op.drop_constraint("chunk_embeddings_pkey", "chunk_embeddings", type_="primary")
    op.create_primary_key("chunk_embeddings_pkey", "chunk_embeddings", ["chunk_id"])
