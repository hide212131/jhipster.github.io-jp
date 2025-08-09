# Makefile for pipeline tools development and CI

.PHONY: help dev install test lint format clean build ci

# Default target
.DEFAULT_GOAL := help

# Python executable
PYTHON := python3
PIP := $(PYTHON) -m pip

# Virtual environment
VENV := .venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

help: ## Show this help message
	@echo "Available targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Development workflow:"
	@echo "  1. make dev      # Setup development environment"
	@echo "  2. make test     # Run tests"
	@echo "  3. make lint     # Check code style"
	@echo "  4. make format   # Format code"

dev: install ## Setup development environment
	@echo "✓ Development environment ready!"
	@echo ""
	@echo "You can now run:"
	@echo "  make test                    # Run tests"
	@echo "  python tools/run_sync.py --help  # Test main script"
	@echo "  make lint                    # Check code style"

install: $(VENV) ## Install dependencies
	@echo "Installing dependencies..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	@echo "✓ Dependencies installed"

$(VENV): ## Create virtual environment
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "✓ Virtual environment created"

test: $(VENV) ## Run tests
	@echo "Running tests..."
	$(VENV_PYTHON) -m pytest tests/ -v --cov=tools --cov-report=term-missing
	@echo "✓ Tests completed"

test-quick: $(VENV) ## Run tests without coverage
	@echo "Running quick tests..."
	$(VENV_PYTHON) -m pytest tests/ -v
	@echo "✓ Quick tests completed"

lint: $(VENV) ## Check code style and quality
	@echo "Running linters..."
	$(VENV_PYTHON) -m flake8 tools/ tests/
	$(VENV_PYTHON) -m mypy tools/ --ignore-missing-imports
	$(VENV_PYTHON) -m isort --check-only --diff tools/ tests/
	$(VENV_PYTHON) -m black --check --diff tools/ tests/
	@echo "✓ Linting completed"

format: $(VENV) ## Format code
	@echo "Formatting code..."
	$(VENV_PYTHON) -m isort tools/ tests/
	$(VENV_PYTHON) -m black tools/ tests/
	@echo "✓ Code formatted"

clean: ## Clean up generated files
	@echo "Cleaning up..."
	rm -rf $(VENV)
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleanup completed"

build: install lint test ## Full build pipeline
	@echo "✓ Build completed successfully"

ci: ## CI pipeline (build + additional checks)
	@echo "Running CI pipeline..."
	make build
	@echo "✓ CI pipeline completed"

# Jekyll site targets (existing functionality)
jekyll-install: ## Install Jekyll dependencies
	bundle install

jekyll-serve: ## Start Jekyll development server
	bundle exec jekyll serve

jekyll-build: ## Build Jekyll site
	bundle exec jekyll build

# Docker targets
docker-up: ## Start Docker development environment  
	docker-compose up

docker-down: ## Stop Docker development environment
	docker-compose down

# Utility targets
check-python: ## Check Python version
	@echo "Python version:"
	$(PYTHON) --version
	@echo "Python path:"
	which $(PYTHON)

run-sync-help: $(VENV) ## Test run_sync.py help
	$(VENV_PYTHON) tools/run_sync.py --help

run-sync-check: $(VENV) ## Test run_sync.py environment check
	$(VENV_PYTHON) tools/run_sync.py check

# Development shortcuts
deps: install ## Alias for install
setup: dev ## Alias for dev
tests: test ## Alias for test