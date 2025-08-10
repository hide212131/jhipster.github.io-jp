# Makefile for JHipster.github.io-jp tools development

.PHONY: help dev test format lint clean install

# Default target
help:
	@echo "JHipster.github.io-jp Tools Development"
	@echo "======================================"
	@echo ""
	@echo "Available commands:"
	@echo "  make help     - Show this help message"
	@echo "  make install  - Install Python dependencies"
	@echo "  make dev      - Setup development environment"
	@echo "  make test     - Run tests"
	@echo "  make format   - Format code with black"
	@echo "  make lint     - Run linting with flake8"
	@echo "  make clean    - Clean temporary files"
	@echo ""
	@echo "CLI commands:"
	@echo "  python cli.py --help       - Show CLI help"
	@echo "  python cli.py status       - Show repository status"
	@echo "  python cli.py translate    - Translation commands"
	@echo "  python cli.py sync         - Sync translations"
	@echo "  python cli.py validate     - Validate translations"

# Install Python dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

# Setup development environment
dev: install
	@echo "Setting up development environment..."
	@echo "Checking Python installation..."
	@python --version
	@echo "Checking CLI functionality..."
	@python cli.py --help
	@echo "Development environment ready!"

# Run tests
test:
	@echo "Running tests..."
	@if [ -d "tests" ]; then \
		python -m pytest tests/ -v; \
	else \
		echo "No tests directory found. Creating placeholder..."; \
		mkdir -p tests; \
		echo "# Tests for JHipster.github.io-jp tools" > tests/__init__.py; \
		echo "Tests directory created. Add your tests here."; \
	fi

# Format code with black
format:
	@echo "Formatting code with black..."
	@if command -v black >/dev/null 2>&1; then \
		black *.py; \
	else \
		echo "black not installed. Run 'make install' first."; \
	fi

# Run linting with flake8
lint:
	@echo "Running linting with flake8..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 *.py --max-line-length=88 --extend-ignore=E203,W503; \
	else \
		echo "flake8 not installed. Run 'make install' first."; \
	fi

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Cleanup completed."