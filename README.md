# DOU Job Search Copilot

ML-first job search copilot for Ukrainian IT candidates. The MVP starts with one CV and one DOU vacancy, then builds toward reusable parsing, matching, ranking, evaluation, and grounded recommendations.

## Current Milestone

M2: rules-baseline structured extraction and single-vacancy fit analysis.

Included now:

- FastAPI backend skeleton with `/health`
- M1 auth and ingestion endpoints for users, CV documents, candidate profiles, and vacancies
- Rules-baseline CV/vacancy extraction for seniority, skills, work format, domain, and requirements
- Document chunk and extracted-skill records created during CV/vacancy ingestion
- `/analyses` endpoints that store score components, evidence maps, gap reports, verdicts, and grounded recommendations
- `POST /analyses/{id}/feedback` for feedback events that can become validated weak labels later
- Ollama/Qwen-ready LLM gateway scaffold under `/ml/llm/*`
- Next.js frontend shell that calls the backend health endpoint
- Workspace panel for registration/login, pasted CV, pasted vacancy, profile creation, and fit analysis
- Docker Compose for PostgreSQL + pgvector, Redis, MinIO, MLflow, API, and web
- Alembic migration setup with the initial product/ML schema
- DVC directory placeholder and a sample dataset file
- Monorepo layout matching `spec_1_dou_job_search_copilot.md`

## Local Development

1. Copy environment variables:

```bash
cp .env.example .env
```

2. Start infrastructure and apps:

```bash
docker compose up --build
```

3. Run database migrations:

```bash
docker compose run --rm api alembic upgrade head
```

4. Open:

- Web: http://localhost:3000
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- MLflow: http://localhost:5000
- MinIO console: http://localhost:9001

## Repository Layout

```text
apps/
  web/       Next.js frontend
  api/       FastAPI backend
ml/          pipelines, experiments, datasets, models, taxonomy
infra/       docker, migrations, deployment assets
docs/        architecture, API, evaluation docs
scripts/     operational and ML scripts
```

## Next Steps

Next, replace or augment the rules baseline with neural structured extraction for CVs and vacancies. The intended local default is:

```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
```

Then run:

```bash
ollama pull qwen2.5:7b
```

## Validation

Useful local checks:

```bash
make compose-check
make api-test
cd apps/web && npm run build
```
