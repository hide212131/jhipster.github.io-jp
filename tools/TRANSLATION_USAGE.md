# Translation System Usage Guide

## Overview

This enhanced translation system provides block-wise translation with SQLite caching, Gemini API integration, and automatic retry/fallback mechanisms.

## Key Features

- **SQLite Caching**: Translations are cached to reduce LLM API calls on re-execution
- **Batch Processing**: Multiple text blocks are translated in parallel for efficiency
- **Retry Logic**: Automatic retry with exponential backoff on failures
- **Fallback**: Graceful fallback to individual translation when batch fails
- **Semantic Change Detection**: Smart detection of when retranslation is needed

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Gemini API key (optional - will use mock mode without it):
```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Usage

### Basic Translation
```bash
python translate_blockwise.py -i input.md -o output.md
```

### With Statistics
```bash
python translate_blockwise.py -i input.md --show-stats
```

### Dry Run (preview what would be translated)
```bash
python translate_blockwise.py -i input.md --dry-run
```

### With Context
```bash
python translate_blockwise.py -i input.md -c "JHipster documentation"
```

## Cache Benefits

The system demonstrates the acceptance criteria:

**First run:**
- LLM calls: 3
- Cache misses: 3
- Translation time: ~0.11 seconds

**Second run (same content):**
- LLM calls: 0
- Cache hits: 3
- Translation time: ~0.00 seconds

## Testing

Run the cache demonstration:
```bash
python test_cache_demo.py
```

Run comprehensive tests:
```bash
python test_translation_system.py
```

## Cache Management

The cache is stored in `tools/.cache/translation_cache.db`. You can:

- View cache statistics with `--show-stats`
- Cache persists across runs automatically
- No manual cache management needed

## Semantic Change Detection

The system can detect when content changes require retranslation:

```python
translator = LLMTranslator()
needs_retranslation = translator.check_semantic_change(
    "You can install JHipster", 
    "You cannot install JHipster"
)
# Returns True - negation change detected
```

## Configuration

Key settings in `config.py`:
- `max_concurrent_requests`: Parallel translation limit (default: 8)
- `retry_max_attempts`: Retry attempts on failure (default: 3)
- `retry_delay`: Base delay between retries (default: 1.0s)

## Mock Mode

Without `GEMINI_API_KEY`, the system runs in mock mode for testing and development, providing placeholder translations while maintaining all caching and batch processing functionality.