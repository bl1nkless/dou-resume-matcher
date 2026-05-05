import hashlib
import math
from collections.abc import Sequence
from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.orm import Session

from resume_hunt.config import get_settings
from resume_hunt.db.models import ChunkEmbedding, Document, DocumentChunk

EMBEDDING_DIMENSIONS = 384
DETERMINISTIC_MODEL_NAME = "deterministic-hash-384"


class EmbeddingService:
    def __init__(self, backend: str | None = None, model_name: str | None = None) -> None:
        settings = get_settings()
        self.requested_backend = backend or settings.embedding_backend
        self.model_name = model_name or settings.embedding_model_name
        self._sentence_model: object | None = None
        self.backend = self._resolve_backend()

    @property
    def storage_model_name(self) -> str:
        if self.backend == "sentence_transformers":
            return self.model_name
        return DETERMINISTIC_MODEL_NAME

    def embed(self, text: str) -> list[float]:
        if self.backend == "sentence_transformers":
            return self._embed_sentence_transformers(text)
        return deterministic_embedding(text)

    def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        if self.backend == "sentence_transformers":
            return [self._normalize(vector) for vector in self._sentence_model_encode(texts)]
        return [deterministic_embedding(text) for text in texts]

    def _resolve_backend(self) -> str:
        if self.requested_backend == "deterministic":
            return "deterministic"
        if self.requested_backend not in {"auto", "sentence_transformers"}:
            return "deterministic"
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._sentence_model = SentenceTransformer(self.model_name)
            return "sentence_transformers"
        except Exception:
            if self.requested_backend == "sentence_transformers":
                raise
            return "deterministic"

    def _sentence_model_encode(self, texts: Sequence[str]) -> list[list[float]]:
        if self._sentence_model is None:
            raise RuntimeError("Sentence transformer backend is not initialized")
        encoded = self._sentence_model.encode(list(texts), normalize_embeddings=True)
        return [list(vector) for vector in encoded]

    def _embed_sentence_transformers(self, text: str) -> list[float]:
        return self._sentence_model_encode([text])[0]

    @staticmethod
    def _normalize(vector: Sequence[float]) -> list[float]:
        values = [float(item) for item in vector[:EMBEDDING_DIMENSIONS]]
        if len(values) < EMBEDDING_DIMENSIONS:
            values.extend([0.0] * (EMBEDDING_DIMENSIONS - len(values)))
        norm = math.sqrt(sum(item * item for item in values)) or 1.0
        return [item / norm for item in values]


def deterministic_embedding(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    vector = [0.0] * dimensions
    tokens = [token for token in _tokenize(text) if token]
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for offset in range(0, len(digest), 2):
            bucket = int.from_bytes(digest[offset : offset + 2], "big") % dimensions
            sign = 1.0 if digest[offset] % 2 == 0 else -1.0
            vector[bucket] += sign
    norm = math.sqrt(sum(item * item for item in vector)) or 1.0
    return [item / norm for item in vector]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right:
        return 0.0
    denominator = math.sqrt(sum(item * item for item in left)) * math.sqrt(
        sum(item * item for item in right)
    )
    if denominator == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=False)) / denominator


def backfill_embeddings(
    session: Session,
    *,
    model_name: str | None = None,
    document_type: str = "all",
    backend: str | None = None,
) -> dict[str, int | str]:
    service = EmbeddingService(backend=backend, model_name=model_name)
    statement = select(DocumentChunk)
    if document_type != "all":
        statement = statement.join(Document, Document.id == DocumentChunk.document_id).where(
            Document.document_type == document_type
        )
    chunks = list(session.scalars(statement))
    created = 0
    skipped = 0
    for chunk in chunks:
        exists = session.get(ChunkEmbedding, (chunk.id, service.storage_model_name))
        if exists is not None:
            skipped += 1
            continue
        session.add(
            ChunkEmbedding(
                chunk_id=chunk.id,
                embedding_model=service.storage_model_name,
                embedding=service.embed(chunk.text),
            )
        )
        created += 1
    session.commit()
    return {
        "backend": service.backend,
        "embedding_model": service.storage_model_name,
        "created": created,
        "skipped": skipped,
    }


def ensure_document_embeddings(
    session: Session,
    *,
    document_ids: Sequence[object],
    service: EmbeddingService | None = None,
) -> dict[str, int | str]:
    embedding_service = service or get_embedding_service()
    chunks = list(
        session.scalars(select(DocumentChunk).where(DocumentChunk.document_id.in_(document_ids)))
    )
    created = 0
    skipped = 0
    for chunk in chunks:
        exists = session.get(ChunkEmbedding, (chunk.id, embedding_service.storage_model_name))
        if exists is not None:
            skipped += 1
            continue
        session.add(
            ChunkEmbedding(
                chunk_id=chunk.id,
                embedding_model=embedding_service.storage_model_name,
                embedding=embedding_service.embed(chunk.text),
            )
        )
        created += 1
    session.flush()
    return {
        "backend": embedding_service.backend,
        "embedding_model": embedding_service.storage_model_name,
        "created": created,
        "skipped": skipped,
    }


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


def _tokenize(text: str) -> list[str]:
    cleaned = "".join(char.lower() if char.isalnum() or char in "+#" else " " for char in text)
    return cleaned.split()
