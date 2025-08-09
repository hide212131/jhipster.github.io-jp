# JHipster Translation Tools Makefile
# Provides development and CI automation commands

.PHONY: help dev ci install test lint format clean

# Default target
help: ## Show this help message
	@echo "JHipster Translation Tools"
	@echo "========================="
	@echo ""
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make dev              # Start development environment"
	@echo "  make test             # Run all tests"
	@echo "  make lint             # Check code quality"
	@echo "  make ci               # Run full CI pipeline"

# Development commands
dev: install ## Set up development environment and show help
	@echo "🚀 Development environment ready!"
	@echo ""
	@echo "Quick start:"
	@echo "  python tools/run_sync.py --help"
	@echo "  python tools/run_sync.py --dry-run --debug --limit 5"
	@echo ""
	@echo "Environment variables:"
	@echo "  GEMINI_API_KEY - Required for LLM translation"
	@echo "  DRY_RUN - Set to 'true' to disable actual changes"
	@echo ""

install: ## Install Python dependencies
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

# Testing commands
test: ## Run all tests
	@echo "🧪 Running tests..."
	python -m pytest tests/ -v --cov=tools --cov-report=term-missing

test-unit: ## Run unit tests only
	@echo "🔬 Running unit tests..."
	python -m pytest tests/tools/ -v

test-integration: ## Run integration tests
	@echo "🔗 Running integration tests..."
	python -m pytest tests/integration/ -v -k "not slow"

# Code quality commands
lint: ## Check code quality with linting tools
	@echo "🔍 Checking code quality..."
	flake8 tools/ tests/
	mypy tools/ --ignore-missing-imports
	@echo "✅ Linting passed!"

format: ## Format code with black
	@echo "🎨 Formatting code..."
	black tools/ tests/
	@echo "✅ Code formatted!"

# CI pipeline
ci: install lint test ## Run complete CI pipeline
	@echo "🎯 CI pipeline completed successfully!"

# Utility commands
clean: ## Clean up generated files and caches
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf debug_output/ 2>/dev/null || true
	@echo "✅ Cleanup completed!"

# Tool-specific commands
sync-dry: install ## Run sync with dry-run mode
	@echo "🧪 Running sync in dry-run mode..."
	python tools/run_sync.py --dry-run --debug

sync-dev: install ## Run sync in development mode (limited files)
	@echo "🔧 Running sync in development mode..."
	python tools/run_sync.py --dry-run --debug --limit 3

# Validation commands
validate-env: ## Validate development environment
	@echo "🔍 Validating environment..."
	@python -c "from tools.dev_filter import DevFilter; df = DevFilter(True); checks = df.validate_environment(); exit(0 if all(checks.values()) else 1)"
	@echo "✅ Environment validation passed!"

# Help text for main tools
tool-help: ## Show help for main sync tool
	python tools/run_sync.py --help