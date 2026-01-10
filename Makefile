.PHONY: install lint lint-fix test type-check all clean venv \
        frontend-install frontend-dev frontend-build frontend-lint \
        backend-dev e2e e2e-ui

# ==============================================================================
# Backend commands
# ==============================================================================

venv:
	cd backend && python3 -m venv venv

install: venv
	cd backend && venv/bin/pip install -e ".[dev]"

lint:
	cd backend && venv/bin/ruff check src tests
	cd backend && venv/bin/ruff format --check src tests

lint-fix:
	cd backend && venv/bin/ruff check --fix src tests
	cd backend && venv/bin/ruff format src tests

test:
	cd backend && venv/bin/pytest -v

type-check:
	cd backend && venv/bin/mypy src

backend-dev:
	cd backend && venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# ==============================================================================
# Frontend commands
# ==============================================================================

frontend-install:
	cd frontend && pnpm install

frontend-dev:
	cd frontend && pnpm dev

frontend-build:
	cd frontend && pnpm build

frontend-lint:
	cd frontend && pnpm lint

# ==============================================================================
# E2E Testing (requires both servers)
# ==============================================================================

e2e:
	cd frontend && pnpm test:e2e

e2e-ui:
	cd frontend && pnpm test:e2e:ui

# ==============================================================================
# Combined commands
# ==============================================================================

all: lint type-check test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
