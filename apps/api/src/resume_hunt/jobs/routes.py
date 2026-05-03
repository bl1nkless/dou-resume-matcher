from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from resume_hunt.auth.dependencies import get_current_user
from resume_hunt.db.models import User
from resume_hunt.db.session import get_db
from resume_hunt.jobs.schemas import JobFromTextRequest, JobFromUrlRequest, JobResponse
from resume_hunt.jobs.service import create_job_from_text, fetch_vacancy_url

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/from-text", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def from_text(
    payload: JobFromTextRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> JobResponse:
    return create_job_from_text(
        session,
        user_id=current_user.id,
        text=payload.text,
        title=payload.title,
        company_name=payload.company,
        source_url=payload.source_url,
    )


@router.post("/from-url", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def from_url(
    payload: JobFromUrlRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> JobResponse:
    text, title, final_url = await fetch_vacancy_url(payload.url)
    return create_job_from_text(
        session,
        user_id=current_user.id,
        text=text,
        title=title,
        source_url=final_url,
        source="dou_url",
    )
