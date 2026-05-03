from fastapi import APIRouter, HTTPException, status
from httpx import HTTPError

from resume_hunt.ml_gateway.client import get_llm_client
from resume_hunt.ml_gateway.schemas import LLMRequest, LLMResponse, LLMStatusResponse

router = APIRouter(prefix="/ml", tags=["ml-gateway"])


@router.get("/llm/status", response_model=LLMStatusResponse)
async def llm_status() -> LLMStatusResponse:
    return await get_llm_client().status()


@router.post("/llm/generate", response_model=LLMResponse)
async def llm_generate(payload: LLMRequest) -> LLMResponse:
    try:
        return await get_llm_client().generate(payload)
    except HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM provider request failed: {exc}",
        ) from exc
