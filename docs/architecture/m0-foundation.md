# M0 Foundation

The first implementation stage creates a runnable monorepo foundation.

## Services

- `web`: Next.js SaaS shell
- `api`: FastAPI API
- `postgres`: PostgreSQL with pgvector
- `redis`: async-job dependency for later milestones
- `minio`: local S3-compatible object storage
- `mlflow`: local experiment tracking
- `ml-worker`: placeholder worker process for future parsing and analysis jobs

## Acceptance Checks

- `GET /health` returns service status
- frontend renders and calls the backend health endpoint
- Alembic can apply the initial migration
- sample dataset exists under `ml/datasets`
