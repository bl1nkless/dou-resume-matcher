from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from resume_hunt.analyses.routes import router as analyses_router
from resume_hunt.auth.routes import router as auth_router
from resume_hunt.candidates.routes import router as candidates_router
from resume_hunt.config import get_settings
from resume_hunt.db.session import SessionLocal
from resume_hunt.documents.routes import router as documents_router
from resume_hunt.jobs.routes import router as jobs_router
from resume_hunt.ml_gateway.routes import router as ml_router

settings = get_settings()

app = FastAPI(
    title="DOU Job Search Copilot API",
    version="0.1.0",
    description="ML-first backend for CV, vacancy, evidence, scoring, and recommendation flows.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(candidates_router)
app.include_router(jobs_router)
app.include_router(analyses_router)
app.include_router(ml_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    database_status = "ok"
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except Exception:
        database_status = "unavailable"

    return {
        "service": "resume-hunt-api",
        "status": "ok",
        "environment": settings.app_env,
        "database": database_status,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.ollama_model if settings.llm_provider == "ollama" else "",
        "embedding_model": settings.embedding_model_name,
        "mlflow_tracking_uri": settings.mlflow_tracking_uri,
    }
