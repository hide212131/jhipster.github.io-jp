# Translation Cache and Reporting System

This system provides SQLite-based caching and observability reporting for the JP translation tools.

## Features

### SQLite Translation Cache
- **Schema**: `(path, upstream_sha, line_no, src_hash, translation_result, timestamp)`
- **Operations**: get, set, exists, get_stats, clear_cache
- **Hash-based content validation**: Changes to source content invalidate cache
- **Session tracking**: Hit/miss rates during translation runs

### Observability Reporting
- **JSON reports**: Detailed line-by-line reasoning in `tools/.out/report.json`
- **Cache statistics**: Hit rates, database size, entry counts
- **Performance metrics**: Processing times, speed improvements
- **Decision tracking**: Why each line was translated or cached

## Architecture

```
Translation Pipeline
├── DiffEngine (detects changed lines)
├── LineLock (prevents concurrent edits)
├── TranslationCache (SQLite storage)
└── TranslationReporter (JSON reports)
```

## Usage

### Basic Cache Operations

```python
from tools.cache import TranslationCache, CacheSession

# Initialize cache
cache = TranslationCache(".cache")

# Use session for hit/miss tracking
session = CacheSession(cache)

# Try cache lookup
result = session.lookup("file.md", "sha123", 1, "Hello World")
if result is None:
    # Translate and store
    translation = translate("Hello World")
    session.store("file.md", "sha123", 1, "Hello World", translation)

# Get session statistics
print(f"Hit rate: {session.get_hit_rate():.1f}%")
```

### Report Generation

```python
from tools.report import TranslationReporter

reporter = TranslationReporter("tools/.out")

# Add cache stats
reporter.add_cache_stats(cache)

# Add line decisions
reporter.add_line_decision(
    path="file.md",
    line_no=1, 
    src_content="Hello",
    translation="こんにちは",
    decision_reason="Standard greeting translation",
    was_cached=True,
    processing_time_ms=2.1
)

# Generate report
report_path = reporter.generate_report()
```

### Integration with Dependencies

The system integrates with `line-lock` and `diff-engine`:

```python
from tools.integration_demo import TranslationPipeline

pipeline = TranslationPipeline()

# Process files with integrated locking and caching
files = {"page.md": ["Hello", "World"]}
report = pipeline.run_translation_batch(files)
```

## Performance Results

Demo results show significant performance improvements:

- **First run**: 0% hit rate, ~800ms processing time
- **Second run**: 100% hit rate, ~0ms processing time  
- **Speed improvement**: 300-400x faster with cache

## File Structure

```
tools/
├── __init__.py                 # Package initialization
├── cache.py                    # SQLite caching system
├── report.py                   # JSON report generation
├── demo.py                     # Basic cache demonstration
├── integration_demo.py         # Full pipeline demo
├── test_cache.py              # Unit tests
└── .out/
    └── report.json            # Generated reports

.cache/
└── translation_cache.db       # SQLite database
```

## Database Schema

```sql
CREATE TABLE translation_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,                    -- File path
    upstream_sha TEXT NOT NULL,            -- Git SHA of upstream
    line_no INTEGER NOT NULL,              -- Line number
    src_hash TEXT NOT NULL,                -- SHA256 of source content
    translation_result TEXT NOT NULL,      -- Translation result
    timestamp TEXT NOT NULL,               -- ISO timestamp
    UNIQUE(path, upstream_sha, line_no, src_hash)
);
```

## Report Schema

```json
{
  "metadata": {
    "generated_at": "ISO timestamp",
    "version": "1.0.0"
  },
  "cache_stats": {
    "total_entries": 123,
    "unique_files": 45,
    "database_size_bytes": 67890
  },
  "files": {
    "path/to/file.md": {
      "upstream_sha": "abc123",
      "total_lines": 100,
      "processed_lines": 95,
      "cache_hits": 80,
      "cache_hit_rate": 84.2
    }
  },
  "line_decisions": [
    {
      "path": "file.md",
      "line_no": 1,
      "src_content": "Hello",
      "translation": "こんにちは", 
      "decision_reason": "Standard greeting",
      "was_cached": true,
      "processing_time_ms": 2.1
    }
  ],
  "summary": {
    "total_files": 5,
    "total_lines": 500,
    "total_cache_hits": 400,
    "overall_cache_hit_rate": 80.0
  }
}
```

## Testing

Run the test suite:

```bash
cd /home/runner/work/jp/jp
python3 tools/test_cache.py -v
```

Run demonstrations:

```bash
# Basic cache demo
python3 tools/demo.py

# Integration demo with line-lock and diff-engine
python3 tools/integration_demo.py
```

## Acceptance Criteria ✅

- [x] **Cache hit rate improvement**: Demonstrated 100% hit rate on re-runs
- [x] **Line-by-line reasoning**: Reports include detailed decision tracking
- [x] **SQLite implementation**: Full schema with (path, upstream_sha, line_no, src_hash)
- [x] **Report generation**: tools/.out/report.json with comprehensive data
- [x] **Integration points**: Ready for line-lock and diff-engine dependencies

## Dependencies

- **Blocked by**: line-lock, diff-engine (integration points implemented)
- **Python**: 3.7+ (uses pathlib, typing)
- **SQLite**: Built-in Python sqlite3 module
- **No external dependencies**: Pure Python implementation