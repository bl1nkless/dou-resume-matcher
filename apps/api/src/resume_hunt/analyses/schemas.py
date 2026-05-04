import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AnalysisCreateRequest(BaseModel):
    candidate_profile_id: uuid.UUID
    job_id: uuid.UUID


class AnalysisFeedbackRequest(BaseModel):
    event_type: str = Field(pattern="^(verdict_rating|recommendation_rating|gap_quality|free_text)$")
    event_value: dict = Field(default_factory=dict)


class FeedbackEventResponse(BaseModel):
    id: uuid.UUID
    analysis_run_id: uuid.UUID | None
    event_type: str
    event_value: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceMapResponse(BaseModel):
    id: uuid.UUID
    requirement_text: str
    requirement_type: str | None
    requirement_priority: str | None
    evidence_chunks: dict
    evidence_level: str
    confidence: float

    model_config = {"from_attributes": True}


class GapReportResponse(BaseModel):
    id: uuid.UUID
    gap_text: str
    gap_type: str
    severity: float
    reason: str
    recommended_action: str | None

    model_config = {"from_attributes": True}


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    recommendation_type: str
    content_json: dict
    llm_model: str | None
    prompt_version: str | None
    guardrail_status: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisRunResponse(BaseModel):
    id: uuid.UUID
    candidate_profile_id: uuid.UUID
    job_id: uuid.UUID
    status: str
    model_version: str | None
    feature_json: dict | None
    score_json: dict | None
    verdict: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class AnalysisReportResponse(AnalysisRunResponse):
    evidence: list[EvidenceMapResponse]
    gaps: list[GapReportResponse]
    recommendations: list[RecommendationResponse]
