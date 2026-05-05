import uuid

from resume_hunt.analyses.retrieval import _classify_evidence
from resume_hunt.db.models import ChunkEmbedding, DocumentChunk
from resume_hunt.ml_gateway.embeddings import (
    DETERMINISTIC_MODEL_NAME,
    EMBEDDING_DIMENSIONS,
    backfill_embeddings,
    cosine_similarity,
    deterministic_embedding,
)
from resume_hunt.taxonomy.service import load_taxonomy_seed, normalize_alias


def test_deterministic_embedding_is_stable_and_384_dimensional() -> None:
    first = deterministic_embedding("Python FastAPI PostgreSQL")
    second = deterministic_embedding("Python FastAPI PostgreSQL")

    assert len(first) == EMBEDDING_DIMENSIONS
    assert first == second
    assert cosine_similarity(first, second) == 1.0


def test_deterministic_embedding_ranks_related_text_higher_than_unrelated_text() -> None:
    query = deterministic_embedding("PostgreSQL database models")
    related = deterministic_embedding("Built PostgreSQL and SQLAlchemy database models")
    unrelated = deterministic_embedding("Designed Figma screens and brand assets")

    assert cosine_similarity(query, related) > cosine_similarity(query, unrelated)


def test_taxonomy_seed_contains_minimum_m3_skills_and_aliases() -> None:
    rows = load_taxonomy_seed()
    by_name = {row["canonical_name"]: row for row in rows}

    assert len(rows) >= 100
    assert {"postgres", "psql"} <= set(by_name["PostgreSQL"]["aliases"])
    assert "drf" in by_name["Django"]["aliases"]
    assert "fast api" in by_name["FastAPI"]["aliases"]


def test_alias_normalization_is_punctuation_tolerant() -> None:
    assert normalize_alias("PostgreSQL") == normalize_alias("postgresql")
    assert normalize_alias("Fast API") == normalize_alias("fast-api")


def test_evidence_classification_covers_direct_transferable_weak_missing() -> None:
    assert _classify_evidence(0.1, 1.0, "Python", {}) == "direct"
    assert _classify_evidence(0.1, 0.65, "Django", {}) == "transferable"
    assert _classify_evidence(0.3, 0.0, "Docker", {}) == "weak"
    assert _classify_evidence(0.05, 0.0, "AWS", {}) == "missing"


def test_backfill_embeddings_skips_existing_chunk_model_pairs() -> None:
    existing_id = uuid.uuid4()
    new_id = uuid.uuid4()
    session = FakeSession(
        [
            DocumentChunk(id=existing_id, document_id=uuid.uuid4(), chunk_type="resume_chunk", text="Python"),
            DocumentChunk(id=new_id, document_id=uuid.uuid4(), chunk_type="resume_chunk", text="Django"),
        ],
        existing_keys={(existing_id, DETERMINISTIC_MODEL_NAME)},
    )

    result = backfill_embeddings(session, backend="deterministic")

    assert result["created"] == 1
    assert result["skipped"] == 1
    assert len(session.added) == 1
    assert session.added[0].chunk_id == new_id


class FakeSession:
    def __init__(self, chunks: list[DocumentChunk], existing_keys: set[tuple[uuid.UUID, str]]) -> None:
        self.chunks = chunks
        self.existing_keys = existing_keys
        self.added: list[ChunkEmbedding] = []

    def scalars(self, statement: object) -> list[DocumentChunk]:
        return self.chunks

    def get(self, model: object, key: tuple[uuid.UUID, str]) -> ChunkEmbedding | None:
        if key in self.existing_keys:
            return ChunkEmbedding(chunk_id=key[0], embedding_model=key[1], embedding=[0.0] * 384)
        return None

    def add(self, item: ChunkEmbedding) -> None:
        self.added.append(item)

    def commit(self) -> None:
        return None
