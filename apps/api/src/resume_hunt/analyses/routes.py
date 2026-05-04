from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from resume_hunt.analyses.schemas import (
    AnalysisCreateRequest,
    AnalysisFeedbackRequest,
    AnalysisReportResponse,
    AnalysisRunResponse,
    EvidenceMapResponse,
    FeedbackEventResponse,
    GapReportResponse,
    RecommendationResponse,
)
from resume_hunt.analyses.service import (
    create_analysis_run,
    create_feedback_event,
    get_analysis_report,
    list_evidence,
    list_gaps,
    list_recommendations,
)
from resume_hunt.auth.dependencies import get_current_user
from resume_hunt.db.models import User
from resume_hunt.db.session import get_db

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisRunResponse, status_code=status.HTTP_201_CREATED)
def create_analysis(
    payload: AnalysisCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> AnalysisRunResponse:
    return create_analysis_run(
        session,
        user_id=current_user.id,
        candidate_profile_id=payload.candidate_profile_id,
        job_id=payload.job_id,
    )


@router.get("/{analysis_id}", response_model=AnalysisReportResponse)
def read_analysis(
    analysis_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> dict:
    return get_analysis_report(session, user_id=current_user.id, analysis_id=analysis_id)


@router.get("/{analysis_id}/evidence", response_model=list[EvidenceMapResponse])
def read_evidence(
    analysis_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list:
    return list_evidence(session, user_id=current_user.id, analysis_id=analysis_id)


@router.get("/{analysis_id}/gaps", response_model=list[GapReportResponse])
def read_gaps(
    analysis_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list:
    return list_gaps(session, user_id=current_user.id, analysis_id=analysis_id)


@router.get("/{analysis_id}/recommendations", response_model=list[RecommendationResponse])
def read_recommendations(
    analysis_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list:
    return list_recommendations(session, user_id=current_user.id, analysis_id=analysis_id)


@router.post("/{analysis_id}/feedback", response_model=FeedbackEventResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    analysis_id: UUID,
    payload: AnalysisFeedbackRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> FeedbackEventResponse:
    return create_feedback_event(
        session,
        user_id=current_user.id,
        analysis_id=analysis_id,
        event_type=payload.event_type,
        event_value=payload.event_value,
    )
