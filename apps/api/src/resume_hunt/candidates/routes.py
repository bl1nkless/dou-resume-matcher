from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from resume_hunt.auth.dependencies import get_current_user
from resume_hunt.candidates.schemas import CandidateProfileCreateRequest, CandidateProfileResponse
from resume_hunt.candidates.service import create_candidate_profile, get_candidate_profile
from resume_hunt.db.models import User
from resume_hunt.db.session import get_db

router = APIRouter(prefix="/candidate-profiles", tags=["candidate-profiles"])


@router.post("", response_model=CandidateProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: CandidateProfileCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> CandidateProfileResponse:
    return create_candidate_profile(
        session,
        user_id=current_user.id,
        resume_document_id=payload.resume_document_id,
        target_role=payload.target_role,
    )


@router.get("/{profile_id}", response_model=CandidateProfileResponse)
def read_profile(
    profile_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> CandidateProfileResponse:
    return get_candidate_profile(session, user_id=current_user.id, profile_id=profile_id)
