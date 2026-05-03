import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class JobFromTextRequest(BaseModel):
    text: str = Field(min_length=40)
    title: str | None = None
    company: str | None = None
    source_url: str | None = None


class JobFromUrlRequest(BaseModel):
    url: str = Field(min_length=12)


class JobResponse(BaseModel):
    id: uuid.UUID
    source: str
    source_url: str | None
    title: str
    seniority: str | None
    domain: str | None
    work_format: str | None
    raw_document_id: uuid.UUID | None
    extracted_json: dict
    first_seen_at: datetime

    model_config = {"from_attributes": True}
