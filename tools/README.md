# JP Repository Tools

Development tools for the JP repository with sync functionality and flexible filtering.

## run_sync.py

Main sync tool with support for both production and development modes.

### Usage

```bash
# Production mode (full sync)
python tools/run_sync.py --mode prod

# Development mode with filters (requires at least one filter)
python tools/run_sync.py --mode dev --limit 5
python tools/run_sync.py --mode dev --before abc123 --limit 10
python tools/run_sync.py --mode dev --paths "*.md" "pages/*"
python tools/run_sync.py --mode dev --before HEAD~10 --limit 5 --paths "*.md"

# Verbose output
python tools/run_sync.py --mode dev --limit 5 --verbose
```

### Options

- `--mode {dev,prod}`: Run mode (default: prod)
  - `prod`: Production mode with full sync
  - `dev`: Development mode with filtering capabilities
- `--before COMMIT`: Filter commits before specified commit (dev mode only)
- `--limit N`: Limit number of items to process (dev mode only) 
- `--paths PATTERN1 PATTERN2...`: Filter by file paths/patterns with wildcard support (dev mode only)
- `--verbose, -v`: Enable verbose output

### Development Mode

Development mode requires at least one filter option (`--before`, `--limit`, or `--paths`).

#### Filters

- **--before**: Filters commits that come before the specified commit
- **--limit**: Limits the number of items (commits/files) to process
- **--paths**: Filters files by path patterns (supports wildcards like `*tips*`, `pages/*`)

#### Examples

```bash
# Process only 5 items
python tools/run_sync.py --mode dev --limit 5

# Filter by paths containing "tips"
python tools/run_sync.py --mode dev --paths "*tips*"

# Multiple path patterns
python tools/run_sync.py --mode dev --paths "*tips*" "*pages*"

# Combined filters
python tools/run_sync.py --mode dev --before abc123 --limit 10 --paths "*.md"
```

## dev_filter.py

Filtering utilities for development mode operations.

### DevFilter Class

Provides filtering capabilities:
- `filter_commits()`: Filter commits by `--before` option
- `filter_paths()`: Filter files by `--paths` patterns  
- `apply_limit()`: Apply `--limit` to any list
- `apply_all_filters()`: Apply all configured filters

### Testing

Run the test script to validate filtering logic:

```bash
python tools/test_dev_filter.py
```

## Requirements

- Python 3.6+
- Git (for commit filtering)

## Error Handling

The tools include comprehensive error handling:
- Validates positive limit values
- Requires at least one filter in dev mode
- Gracefully handles git errors in shallow repositories
- Provides helpful warning messages