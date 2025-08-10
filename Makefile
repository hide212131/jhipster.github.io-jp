.PHONY: help install dev test format lint clean

# Default target
help:
	@echo "Available commands:"
	@echo "  install  - Install Python dependencies"
	@echo "  dev      - Set up development environment"
	@echo "  test     - Run tests"
	@echo "  format   - Format code with black and isort"
	@echo "  lint     - Run code linting with flake8"
	@echo "  clean    - Clean up cache and temporary files"

# Install dependencies
install:
	pip install -r requirements.txt

# Set up development environment
dev: install
	@echo "Development environment setup complete"
	@echo "Testing main scripts..."
	@python tools/run_sync.py --help
	@python tools/discover_changes.py --help
	@python tools/translate_blockwise.py --help
	@echo "✅ All main scripts respond to --help"

# Run tests
test:
	pytest tools/tests/ -v

# Format code
format:
	black tools/
	isort tools/

# Run linting
lint:
	flake8 tools/ --max-line-length=88 --extend-ignore=E203,W503

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/
	rm -rf tools/.out/