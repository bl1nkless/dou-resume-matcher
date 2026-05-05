.PHONY: setup up down migrate api-dev api-test seed-taxonomy backfill-embeddings web-dev compose-check local-api local-web

setup:
	cp -n .env.example .env || true

up: setup
	docker compose up --build

down:
	docker compose down

migrate: setup
	docker compose run --rm api alembic upgrade head

api-dev:
	cd apps/api && uv run uvicorn resume_hunt.main:app --reload --app-dir src

api-test:
	cd apps/api && uv run pytest -q

seed-taxonomy:
	cd apps/api && uv run python scripts/seed_taxonomy.py

backfill-embeddings:
	cd apps/api && uv run python scripts/backfill_embeddings.py --backend deterministic

web-dev:
	cd apps/web && npm run dev

local-api: api-dev

local-web: web-dev

compose-check:
	docker compose config --quiet
