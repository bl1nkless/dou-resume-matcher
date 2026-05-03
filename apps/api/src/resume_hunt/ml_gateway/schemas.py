from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str


class LLMRequest(BaseModel):
    task: str
    messages: list[LLMMessage]
    response_format: str = "text"


class LLMResponse(BaseModel):
    provider: str
    model: str | None
    content: str
    raw: dict | None = None


class LLMStatusResponse(BaseModel):
    provider: str
    model: str | None
    available: bool
    detail: str
