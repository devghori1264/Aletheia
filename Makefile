# =============================================================================
# Aletheia - Makefile
# =============================================================================
# Automation commands for development, testing, and deployment
# =============================================================================

.PHONY: help install install-dev test lint format typecheck clean run migrate shell docker-build docker-up docker-down celery docs

# Default Python
PYTHON := python
PIP := pip
MANAGE := $(PYTHON) src/manage.py

# Colors for terminal output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "$(BLUE)Aletheia - Enterprise Deepfake Detection Platform$(NC)"
	@echo ""
	@echo "$(YELLOW)Usage:$(NC)"
	@echo "  make $(GREEN)<command>$(NC)"
	@echo ""
	@echo "$(YELLOW)Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# Installation
# =============================================================================

install: ## Install production dependencies
	$(PIP) install -e .

install-dev: ## Install development dependencies
	$(PIP) install -e ".[dev,docs,ml]"
	pre-commit install

install-all: ## Install all dependencies including production extras
	$(PIP) install -e ".[dev,docs,ml,production]"
	pre-commit install

upgrade-deps: ## Upgrade all dependencies
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -e ".[dev,docs,ml,production]"

# =============================================================================
# Development Server
# =============================================================================

run: ## Run development server
	$(MANAGE) runserver

run-ssl: ## Run development server with HTTPS
	$(MANAGE) runserver_plus --cert-file /tmp/cert.pem

shell: ## Open Django shell
	$(MANAGE) shell_plus --ipython

dbshell: ## Open database shell
	$(MANAGE) dbshell

# =============================================================================
# Database
# =============================================================================

migrate: ## Run database migrations
	$(MANAGE) migrate

makemigrations: ## Create new migrations
	$(MANAGE) makemigrations

migrate-show: ## Show migration status
	$(MANAGE) showmigrations

migrate-reset: ## Reset all migrations (DANGER: destroys data)
	@echo "$(RED)WARNING: This will destroy all data!$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] && \
		$(MANAGE) migrate --fake detection zero && \
		find . -path "*/migrations/*.py" -not -name "__init__.py" -delete

db-seed: ## Seed database with sample data
	$(MANAGE) loaddata fixtures/sample_data.json

db-dump: ## Dump database to JSON
	$(MANAGE) dumpdata --indent 2 > backup.json

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest -m unit

test-integration: ## Run integration tests only
	pytest -m integration

test-e2e: ## Run end-to-end tests only
	pytest -m e2e

test-fast: ## Run tests without slow tests
	pytest -m "not slow"

test-cov: ## Run tests with coverage report
	pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report: htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	ptw --runner "pytest -x"

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linter
	ruff check src tests
	@echo "$(GREEN)Linting passed!$(NC)"

lint-fix: ## Run linter with auto-fix
	ruff check --fix src tests
	@echo "$(GREEN)Linting fixed!$(NC)"

format: ## Format code with black and isort
	black src tests
	isort src tests
	@echo "$(GREEN)Formatting complete!$(NC)"

format-check: ## Check code formatting
	black --check src tests
	isort --check-only src tests

typecheck: ## Run type checker
	mypy src
	@echo "$(GREEN)Type checking passed!$(NC)"

quality: lint typecheck format-check ## Run all quality checks
	@echo "$(GREEN)All quality checks passed!$(NC)"

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

# =============================================================================
# Celery
# =============================================================================

celery: ## Start Celery worker
	celery -A aletheia worker -l INFO

celery-beat: ## Start Celery beat scheduler
	celery -A aletheia beat -l INFO

celery-flower: ## Start Flower monitoring
	celery -A aletheia flower --port=5555

celery-purge: ## Purge all Celery tasks
	celery -A aletheia purge -f

# =============================================================================
# Docker
# =============================================================================

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-shell: ## Open shell in API container
	docker-compose exec api bash

docker-clean: ## Remove all Docker artifacts
	docker-compose down -v --rmi all --remove-orphans

# =============================================================================
# Documentation
# =============================================================================

docs: ## Build documentation
	mkdocs build

docs-serve: ## Serve documentation locally
	mkdocs serve

docs-deploy: ## Deploy documentation to GitHub Pages
	mkdocs gh-deploy

# =============================================================================
# ML Models
# =============================================================================

model-download: ## Download pre-trained models
	$(PYTHON) scripts/download_models.py

model-benchmark: ## Run model benchmark
	$(PYTHON) scripts/benchmark.py

model-train: ## Start model training
	$(PYTHON) scripts/train_model.py

# =============================================================================
# Production
# =============================================================================

collectstatic: ## Collect static files
	$(MANAGE) collectstatic --noinput

prod-check: ## Run production deployment checks
	$(MANAGE) check --deploy

gunicorn: ## Run with Gunicorn
	gunicorn aletheia.wsgi:application \
		--bind 0.0.0.0:8000 \
		--workers 4 \
		--worker-class gthread \
		--threads 2 \
		--access-logfile - \
		--error-logfile -

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean build artifacts
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	rm -rf build/ dist/
	@echo "$(GREEN)Cleaned!$(NC)"

clean-docker: ## Clean Docker artifacts
	docker system prune -af
	docker volume prune -f

# =============================================================================
# Utilities
# =============================================================================

secrets: ## Generate new secret key
	@$(PYTHON) -c "import secrets; print(secrets.token_urlsafe(50))"

env-check: ## Check environment configuration
	$(MANAGE) check
	@echo "$(GREEN)Environment check passed!$(NC)"

superuser: ## Create superuser
	$(MANAGE) createsuperuser

show-urls: ## Show all URL patterns
	$(MANAGE) show_urls

# =============================================================================
# CI/CD
# =============================================================================

ci: install-dev quality test ## Run CI pipeline
	@echo "$(GREEN)CI pipeline passed!$(NC)"

release-patch: ## Create patch release
	bump2version patch
	git push --tags

release-minor: ## Create minor release
	bump2version minor
	git push --tags

release-major: ## Create major release
	bump2version major
	git push --tags
