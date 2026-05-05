import uuid

from resume_hunt.analyses import service
from resume_hunt.analyses.retrieval import RetrievedEvidence
from resume_hunt.db.models import CandidateProfile, Job


def test_analysis_falls_back_to_rules_when_retrieval_fails(monkeypatch) -> None:
    def fail_retrieval(*args: object, **kwargs: object) -> tuple[list[RetrievedEvidence], dict]:
        raise RuntimeError("embedding backend unavailable")

    monkeypatch.setattr(service, "build_retrieved_evidence", fail_retrieval)
    profile, job = _profile_and_job("Python")

    evidence, gaps, features, scores, verdict = service._run_rules_baseline(object(), uuid.uuid4(), profile, job)

    assert evidence[0].evidence_level == "direct"
    assert evidence[0].evidence_chunks["items"][0]["evidence_type"] == "direct"
    assert features["embedding_backend"] == "rules_only"
    assert scores["overall_score"] > 0
    assert verdict in {"apply_now", "tailor_first", "realistic_stretch", "learning_target", "skip"}
    assert gaps == []


def test_analysis_uses_retrieved_chunk_metadata(monkeypatch) -> None:
    chunk_id = uuid.uuid4()

    def retrieve(*args: object, **kwargs: object) -> tuple[list[RetrievedEvidence], dict]:
        return (
            [
                RetrievedEvidence(
                    chunk_id=chunk_id,
                    chunk="Built FastAPI REST API with PostgreSQL.",
                    similarity=0.71,
                    evidence_type="transferable",
                    skill_overlap=0.65,
                    confidence=0.72,
                    reason="Retrieved chunk has transferable evidence for GraphQL.",
                )
            ],
            {
                "backend": "deterministic",
                "embedding_model": "deterministic-hash-384",
                "created": 2,
                "skipped": 0,
            },
        )

    monkeypatch.setattr(service, "build_retrieved_evidence", retrieve)
    profile, job = _profile_and_job("GraphQL")

    evidence, gaps, features, scores, verdict = service._run_rules_baseline(object(), uuid.uuid4(), profile, job)

    item = evidence[0].evidence_chunks["items"][0]
    assert evidence[0].evidence_level == "transferable"
    assert item["chunk_id"] == str(chunk_id)
    assert item["similarity"] == 0.71
    assert item["skill_overlap"] == 0.65
    assert features["embedding_backend"] == "deterministic"
    assert scores["experience_evidence_score"] > 0
    assert gaps[0].gap_type == "keyword_gap"
    assert verdict in {"tailor_first", "realistic_stretch", "learning_target", "skip"}


def _profile_and_job(requirement: str) -> tuple[CandidateProfile, Job]:
    resume_document_id = uuid.uuid4()
    vacancy_document_id = uuid.uuid4()
    profile = CandidateProfile(
        profile_json={
            "resume_document_id": str(resume_document_id),
            "skills": [
                {
                    "canonical_name": "Python",
                    "evidence_text": "Built Python backend APIs.",
                }
            ],
        },
        estimated_seniority="junior",
        positioning="junior backend developer",
    )
    job = Job(
        raw_document_id=vacancy_document_id,
        seniority="junior",
        extracted_json={
            "raw_requirements": [
                {
                    "text": requirement,
                    "requirement_type": "technical_skill",
                    "priority": "required",
                    "normalized_skill": requirement,
                }
            ]
        },
    )
    return profile, job
