from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from resume_hunt.analyses.extraction import TRANSFERABLE_SKILLS, extract_skills
from resume_hunt.db.models import ChunkEmbedding, DocumentChunk
from resume_hunt.ml_gateway.embeddings import (
    EmbeddingService,
    cosine_similarity,
    ensure_document_embeddings,
    get_embedding_service,
)


@dataclass(frozen=True)
class RetrievedEvidence:
    chunk_id: UUID
    chunk: str
    similarity: float
    evidence_type: str
    skill_overlap: float
    confidence: float
    reason: str


def build_retrieved_evidence(
    session: Session,
    *,
    resume_document_id: UUID,
    vacancy_document_id: UUID,
    requirement_text: str,
    normalized_skill: str | None,
    candidate_skills: dict[str, dict],
    embedding_service: EmbeddingService | None = None,
    limit: int = 3,
) -> tuple[list[RetrievedEvidence], dict[str, int | str]]:
    service = embedding_service or get_embedding_service()
    embedding_meta = ensure_document_embeddings(
        session,
        document_ids=[resume_document_id, vacancy_document_id],
        service=service,
    )
    query_vector = service.embed(requirement_text)
    rows = session.execute(
        select(DocumentChunk, ChunkEmbedding)
        .join(ChunkEmbedding, ChunkEmbedding.chunk_id == DocumentChunk.id)
        .where(DocumentChunk.document_id == resume_document_id)
        .where(ChunkEmbedding.embedding_model == service.storage_model_name)
    ).all()
    ranked: list[RetrievedEvidence] = []
    for chunk, embedding in rows:
        similarity = cosine_similarity(query_vector, embedding.embedding or [])
        skill_overlap = _skill_overlap(chunk.text, normalized_skill, candidate_skills)
        evidence_type = _classify_evidence(similarity, skill_overlap, normalized_skill, candidate_skills)
        section_strength = _section_strength(chunk.chunk_type)
        confidence = max(
            0.0,
            min(
                1.0,
                0.45 * max(similarity, 0.0)
                + 0.30 * skill_overlap
                + 0.15 * section_strength
                + 0.10,
            ),
        )
        ranked.append(
            RetrievedEvidence(
                chunk_id=chunk.id,
                chunk=chunk.text,
                similarity=round(similarity, 4),
                evidence_type=evidence_type,
                skill_overlap=round(skill_overlap, 4),
                confidence=round(confidence, 4),
                reason=_reason(evidence_type, normalized_skill, similarity, skill_overlap),
            )
        )
    ranked.sort(key=lambda item: (item.confidence, item.similarity), reverse=True)
    return ranked[:limit], embedding_meta


def _skill_overlap(
    chunk_text: str,
    normalized_skill: str | None,
    candidate_skills: dict[str, dict],
) -> float:
    if not normalized_skill:
        return 0.0
    chunk_skills = {skill.canonical_name for skill in extract_skills(chunk_text)}
    if normalized_skill in chunk_skills:
        return 1.0
    if normalized_skill in candidate_skills and normalized_skill.lower() in chunk_text.lower():
        return 0.9
    transferable = TRANSFERABLE_SKILLS.get(normalized_skill, set())
    if chunk_skills.intersection(transferable):
        return 0.65
    if any(skill.lower() in chunk_text.lower() for skill in transferable):
        return 0.55
    return 0.0


def _classify_evidence(
    similarity: float,
    skill_overlap: float,
    normalized_skill: str | None,
    candidate_skills: dict[str, dict],
) -> str:
    if skill_overlap >= 0.9:
        return "direct"
    if skill_overlap >= 0.55:
        return "transferable"
    if normalized_skill and normalized_skill in candidate_skills and similarity >= 0.12:
        return "weak"
    if similarity >= 0.28:
        return "weak"
    return "missing"


def _section_strength(chunk_type: str) -> float:
    if "experience" in chunk_type:
        return 1.0
    if "project" in chunk_type:
        return 0.85
    if "skill" in chunk_type:
        return 0.65
    return 0.7


def _reason(
    evidence_type: str,
    normalized_skill: str | None,
    similarity: float,
    skill_overlap: float,
) -> str:
    skill = normalized_skill or "the requirement"
    if evidence_type == "direct":
        return f"Retrieved chunk directly overlaps with {skill}."
    if evidence_type == "transferable":
        return f"Retrieved chunk has transferable evidence for {skill}."
    if evidence_type == "weak":
        return f"Retrieved chunk is semantically related to {skill}, but evidence is not direct."
    return f"No reliable retrieved chunk for {skill}; best similarity was {similarity:.2f}."
