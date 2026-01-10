.PHONY: install lint lint-fix test type-check all clean venv

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

all: lint type-check test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
