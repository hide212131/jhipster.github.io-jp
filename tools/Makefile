# LLM Translation Pipeline Makefile

.PHONY: help dev test format lint clean install

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

dev: install ## Set up development environment
	@echo "Setting up development environment..."
	@python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
	@echo "Dependencies installed successfully"
	@echo "Development environment ready!"

test: ## Run tests
	@echo "Running tests..."
	python test_scaffold.py

format: ## Format code with black
	@echo "Formatting code..."
	@python -c "import black" 2>/dev/null && python -m black . --line-length 88 || echo "black not installed, skipping format"

lint: ## Lint code with flake8 and mypy
	@echo "Linting code..."
	@python -c "import flake8" 2>/dev/null && python -m flake8 . --max-line-length 88 --ignore E203,W503 || echo "flake8 not installed, skipping lint"
	@python -c "import mypy" 2>/dev/null && python -m mypy . --ignore-missing-imports || echo "mypy not installed, skipping type check"

clean: ## Clean temporary files
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .out/