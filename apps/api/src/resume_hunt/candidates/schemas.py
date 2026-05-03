import uuid
from datetime import datetime

from pydantic import BaseModel


class CandidateProfileCreateRequest(BaseModel):
    resume_document_id: uuid.UUID | None = None
    target_role: str | None = None


class CandidateProfileResponse(BaseModel):
    id: uuid.UUID
    target_role: str | None
    estimated_seniority: str | None
    positioning: str | None
    profile_json: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
