from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://resume_hunt:resume_hunt@localhost:5432/resume_hunt"
    database_url_sync: str = Field(
        default="postgresql+psycopg://resume_hunt:resume_hunt@localhost:5432/resume_hunt",
        alias="DATABASE_URL_SYNC",
    )
    redis_url: str = "redis://localhost:6379/0"
    object_storage_endpoint: str = "http://localhost:9000"
    object_storage_bucket: str = "resume-hunt-dev"
    object_storage_access_key: str = "minioadmin"
    object_storage_secret_key: str = "minioadmin"
    llm_provider: str = "disabled"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    mlflow_tracking_uri: str = "http://localhost:5000"
    jwt_secret: str = "change-me-in-local-env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
