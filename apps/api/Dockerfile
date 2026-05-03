FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY src ./src

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "resume_hunt.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
