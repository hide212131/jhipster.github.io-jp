# JHipster.github.io-jp Tools

Development tools and utilities for the JHipster.github.io-jp project.

## Setup

### Quick Start

```bash
cd tools/
make dev
```

This will install all dependencies and set up the development environment.

## Available Commands

### Make Commands

- `make help` - Show available commands
- `make install` - Install Python dependencies
- `make dev` - Setup development environment
- `make test` - Run tests
- `make format` - Format code with black
- `make lint` - Run linting with flake8
- `make clean` - Clean temporary files

### CLI Commands

The main CLI tool provides various development and translation management commands:

```bash
# Show help
python cli.py --help

# Show repository status
python cli.py status

# Translation management (to be implemented)
python cli.py translate

# Synchronize translations (to be implemented)
python cli.py sync

# Validate translations (to be implemented)
python cli.py validate
```

## Project Structure

```
tools/
├── __init__.py         # Package initialization
├── cli.py              # Main CLI entry point
├── config.py           # Configuration management
├── git_utils.py        # Git utility functions
├── requirements.txt    # Python dependencies
├── Makefile           # Development commands
├── README.md          # This file
└── tests/             # Test directory (created by make test)
```

## Development

1. Set up the development environment:
   ```bash
   make dev
   ```

2. Format code before committing:
   ```bash
   make format
   ```

3. Run linting:
   ```bash
   make lint
   ```

4. Run tests:
   ```bash
   make test
   ```

## Dependencies

- Python 3.8+
- click - CLI framework
- pyyaml - YAML processing
- gitpython - Git operations
- black - Code formatting
- flake8 - Code linting
- pytest - Testing framework
- requests - HTTP library