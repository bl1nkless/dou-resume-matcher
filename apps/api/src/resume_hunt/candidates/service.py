from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from resume_hunt.analyses.extraction import parse_resume
from resume_hunt.db.models import CandidateProfile, Document


def create_candidate_profile(
    session: Session,
    *,
    user_id: UUID,
    resume_document_id: UUID | None,
    target_role: str | None,
) -> CandidateProfile:
    source_document = None
    if resume_document_id:
        source_document = session.get(Document, resume_document_id)
        if source_document is None or source_document.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume document not found")
        if source_document.document_type != "resume":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Candidate profile source must be a resume document",
            )

    parsed_resume = parse_resume(source_document.raw_text if source_document else "", target_role=target_role)
    profile_json = {
        "source": "m1_manual_profile",
        "resume_document_id": str(resume_document_id) if resume_document_id else None,
        "extraction_status": "m2_rules_baseline",
        "raw_text_preview": source_document.raw_text[:480] if source_document else None,
        **parsed_resume,
    }
    profile = CandidateProfile(
        user_id=user_id,
        target_role=parsed_resume["target_role"] or target_role,
        estimated_seniority=parsed_resume["estimated_seniority"],
        positioning=parsed_resume["positioning"],
        profile_json=profile_json,
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def get_candidate_profile(session: Session, *, user_id: UUID, profile_id: UUID) -> CandidateProfile:
    profile = session.get(CandidateProfile, profile_id)
    if profile is None or profile.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found")
    return profile
