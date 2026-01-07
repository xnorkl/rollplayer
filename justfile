# justfile for GM Chatbot
# Run `just --list` to see all available recipes

set dotenv-load
set positional-arguments

# Default recipe - show help
default:
    @just --list

# ============================================================================
# TESTING
# ============================================================================

# Run all tests
test *args:
    uv run pytest {{ args }}

# Run unit tests only
test-unit *args:
    uv run pytest tests/unit -v {{ args }}

# Run integration tests only
test-integration *args:
    uv run pytest tests/integration -v {{ args }}

# Run tests with coverage report
test-cov *args:
    uv run pytest --cov=src/gm_chatbot --cov-report=term-missing --cov-report=html {{ args }}
    @echo "Coverage report: htmlcov/index.html"

# Run tests, stop on first failure
test-fast *args:
    uv run pytest -x -q --tb=line {{ args }}

# Run tests matching a pattern
test-match pattern *args:
    uv run pytest -k "{{ pattern }}" -v {{ args }}

# ============================================================================
# CODE QUALITY
# ============================================================================

# Run linter
lint *args:
    uv run ruff check src tests {{ args }}

# Run linter with auto-fix
lint-fix:
    uv run ruff check src tests --fix

# Format code
format:
    uv run ruff format src tests

# Check formatting without changes
format-check:
    uv run ruff format src tests --check

# Run type checker
typecheck:
    uv run ty check src

# Run all quality checks
check: format-check lint typecheck test
    @echo "[+] All quality checks passed"

# ============================================================================
# DEVELOPMENT
# ============================================================================

# Start development server
dev:
    uv run uvicorn gm_chatbot.api.app:app --reload --host 0.0.0.0 --port 8000

# Start development server with debug logging
dev-debug:
    LOG_LEVEL=debug uv run uvicorn gm_chatbot.api.app:app --reload --host 0.0.0.0 --port 8000

# Open Python REPL with project loaded
shell:
    uv run python -i -c "from gm_chatbot.lib import *; from gm_chatbot.models import *; print('GM Chatbot shell ready')"

# Run a one-off Python command
run *args:
    uv run python {{ args }}

# ============================================================================
# DATA MANAGEMENT
# ============================================================================

# Reset local data (WARNING: destructive)
db-reset:
    rm -rf data/campaigns data/players data/rules
    mkdir -p data/campaigns data/players data/rules
    @echo "Data directories reset"

# Seed development data
db-seed:
    uv run python scripts/seed_data.py
    @echo "Development data seeded"

# Backup current data
db-backup:
    #!/usr/bin/env bash
    timestamp=$(date +%Y%m%d_%H%M%S)
    mkdir -p backups
    tar -czf "backups/data_${timestamp}.tar.gz" data/
    echo "Backup created: backups/data_${timestamp}.tar.gz"

# ============================================================================
# CI / RELEASE
# ============================================================================

# Run full CI pipeline locally
ci: check test-cov
    @echo "[+] All CI checks passed"

# Run CI with integration tests
ci-full: check test-cov test-integration
    @echo "[+] Full CI pipeline passed"

# Build container image
build:
    docker build -t gm-chatbot:local .

# ============================================================================
# DEPENDENCIES
# ============================================================================

# Install/sync dependencies
deps:
    uv sync

# Update dependencies
deps-update:
    uv lock --upgrade
    uv sync

# Add a new dependency
deps-add *args:
    uv add {{ args }}

# Add a new dev dependency
deps-add-dev *args:
    uv add --dev {{ args }}

# ============================================================================
# UTILITIES
# ============================================================================

# Clean build artifacts and caches
clean:
    rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    @echo "Cleaned build artifacts"

# Show project info
info:
    @echo "Python: $(uv run python --version)"
    @echo "UV: $(uv --version)"
    @echo "Project: gm-chatbot"
    @uv run python -c "import gm_chatbot; print(f'Version: {gm_chatbot.__version__}')" 2>/dev/null || echo "Version: dev"

# Generate OpenAPI spec
openapi:
    uv run python -c "from gm_chatbot.api.app import app; import json; print(json.dumps(app.openapi(), indent=2))" > openapi.json
    @echo "OpenAPI spec written to openapi.json"
