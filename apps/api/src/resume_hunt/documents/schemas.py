import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TextDocumentRequest(BaseModel):
    text: str = Field(min_length=20)
    source_url: str | None = None


class DocumentResponse(BaseModel):
    id: uuid.UUID
    document_type: str
    source_url: str | None
    language: str | None
    object_storage_uri: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
