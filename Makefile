# Makefile for JP auto-sync and Gemini translation pipeline

.PHONY: help install test lint clean sync translate build serve

# Default target
help:
	@echo "JP Auto-sync and Gemini Translation Pipeline"
	@echo ""
	@echo "Available targets:"
	@echo "  install     Install all dependencies (Python, Ruby, Node.js)"
	@echo "  test        Run all tests"
	@echo "  lint        Run linters for all code"
	@echo "  clean       Clean build artifacts"
	@echo "  sync        Sync from upstream repository"
	@echo "  translate   Run Gemini translation pipeline"
	@echo "  build       Build the Jekyll site"
	@echo "  serve       Serve the site locally"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Installing Ruby dependencies..."
	bundle install
	@echo "Installing Node.js dependencies..."
	npm install

# Run tests
test:
	@echo "Running Python tests..."
	python -m pytest tools/tests/ -v
	@echo "Running textlint..."
	npx textlint "_posts/**/*.md" "pages/**/*.md"

# Run linters
lint:
	@echo "Running Python linting..."
	python -m flake8 tools/ --max-line-length=120
	@echo "Running textlint for Japanese content..."
	npx textlint "_posts/**/*.md" "pages/**/*.md"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf _site/
	rm -rf .sass-cache/
	rm -rf .jekyll-cache/
	rm -rf node_modules/.cache/

# Sync from upstream repository
sync:
	@echo "Syncing from upstream repository..."
	python tools/sync/sync_upstream.py

# Run Gemini translation pipeline
translate:
	@echo "Running Gemini translation pipeline..."
	python tools/translation/translate_content.py

# Build Jekyll site
build:
	@echo "Building Jekyll site..."
	bundle exec jekyll build

# Serve site locally
serve:
	@echo "Serving site locally..."
	bundle exec jekyll serve

# Build Sass styles
sass:
	@echo "Building Sass styles..."
	npm run sass