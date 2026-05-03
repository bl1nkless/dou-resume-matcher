from abc import ABC, abstractmethod

import httpx

from resume_hunt.config import Settings, get_settings
from resume_hunt.ml_gateway.schemas import LLMRequest, LLMResponse, LLMStatusResponse


class LLMClient(ABC):
    @abstractmethod
    async def generate(self, payload: LLMRequest) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    async def status(self) -> LLMStatusResponse:
        raise NotImplementedError


class DisabledLLMClient(LLMClient):
    async def generate(self, payload: LLMRequest) -> LLMResponse:
        return LLMResponse(
            provider="disabled",
            model=None,
            content=(
                "LLM provider is disabled. Set LLM_PROVIDER=ollama and run a local model "
                "for neural generation."
            ),
            raw={"task": payload.task},
        )

    async def status(self) -> LLMStatusResponse:
        return LLMStatusResponse(
            provider="disabled",
            model=None,
            available=False,
            detail="Set LLM_PROVIDER=ollama to use local Qwen through Ollama.",
        )


class OllamaLLMClient(LLMClient):
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    async def generate(self, payload: LLMRequest) -> LLMResponse:
        prompt = "\n\n".join(f"{message.role.upper()}:\n{message.content}" for message in payload.messages)
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
        data = response.json()
        return LLMResponse(
            provider="ollama",
            model=self.model,
            content=data.get("response", ""),
            raw={"done": data.get("done"), "total_duration": data.get("total_duration")},
        )

    async def status(self) -> LLMStatusResponse:
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
            except httpx.HTTPError as exc:
                return LLMStatusResponse(
                    provider="ollama",
                    model=self.model,
                    available=False,
                    detail=f"Ollama is not reachable: {exc}",
                )

        models = response.json().get("models", [])
        names = {model.get("name") for model in models}
        available = self.model in names
        detail = "Model is installed" if available else f"Run: ollama pull {self.model}"
        return LLMStatusResponse(provider="ollama", model=self.model, available=available, detail=detail)


def get_llm_client() -> LLMClient:
    settings = get_settings()
    if settings.llm_provider.lower() == "ollama":
        return OllamaLLMClient(settings)
    return DisabledLLMClient()
