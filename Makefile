.PHONY: help setup up down test lint boundaries api web check

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Install backend (editable, with dev extras) and frontend dependencies
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

up: ## Start Postgres
	docker compose up -d

down: ## Stop Postgres
	docker compose down

test: ## Run the invariant and chaos suites
	cd backend && pytest -q

lint: ## Format check and type check
	cd backend && ruff check . && mypy src

boundaries: ## Enforce module boundaries (ADR 0002) — the check that keeps extraction possible
	cd backend && lint-imports

api: ## Run the API with reload
	cd backend && uvicorn guild.api.main:app --reload

web: ## Run the frontend dev server
	cd frontend && npm run dev

check: lint boundaries test ## Everything CI runs
