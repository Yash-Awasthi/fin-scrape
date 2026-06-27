# WorldFin developer commands. See PLAN.md.
# Python tasks run via uv pinned to 3.13 (spacy has no 3.14 wheel yet) with the
# server + dev groups so FastAPI/asyncpg/ruff are present.
.DEFAULT_GOAL := help
PY := uv run -p 3.13 --group server --group dev
COMPOSE := docker compose

# New (WorldFin) code only — pre-existing finscrape source isn't ruff-format clean,
# so formatting is scoped to avoid a noisy whole-repo reformat.
NEW_DIRS := server worker finscrape/scrapers/world finscrape/ingestors \
	tests/server tests/test_world_phase2.py tests/test_worker_phase3.py \
	tests/test_correlate_phase4.py

.PHONY: help up down logs seed demo test lint fmt fmt-check selfcheck

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up: ## Start the stack (postgres + api) and wait for health
	$(COMPOSE) up -d --build
	@echo "API → http://localhost:8000   docs → http://localhost:8000/docs"

down: ## Stop the stack (keep volumes)
	$(COMPOSE) down

logs: ## Tail api + postgres logs
	$(COMPOSE) logs -f api postgres

seed: ## Load demo data (placeholder until Phase 11 seed script lands)
	@echo "seed: not implemented yet — Phase 11. Use POST /api/events for now."

demo: up ## Bring up the full demo (Phase 11 will populate it)
	@echo "demo: stack up. Full seeded walkthrough arrives in Phase 11 (docs/DEMO.md)."

test: ## Run the test suite (pytest)
	$(PY) pytest -q

lint: ## Lint new WorldFin code with ruff (pre-existing finscrape debt is out of scope)
	$(PY) ruff check $(NEW_DIRS)

fmt: ## Auto-format new WorldFin code
	$(PY) ruff format $(NEW_DIRS)

fmt-check: ## Check formatting of new WorldFin code (CI gate)
	$(PY) ruff format --check $(NEW_DIRS)

selfcheck: ## Docker-free Phase 0 checks (settings/schemas/migration SQL)
	$(PY) python -m tests.server.selfcheck
