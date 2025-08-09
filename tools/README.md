# JP Auto-sync and Gemini Translation Pipeline Tools

This directory contains the automation tools for the JP (Japanese) translation pipeline that syncs content from the upstream English JHipster documentation and translates it using Google's Gemini AI.

## Directory Structure

```
tools/
├── README.md              # This file
├── sync/                  # Upstream synchronization tools
│   ├── sync_upstream.py   # Main sync script
│   └── merge_conflicts.py # Conflict resolution helpers
├── translation/           # Gemini translation tools
│   ├── translate_content.py  # Main translation script
│   ├── gemini_client.py      # Gemini API client
│   └── content_processor.py  # Content processing utilities
├── tests/                 # Test suite
│   ├── test_sync.py
│   └── test_translation.py
└── common/                # Common utilities
    ├── config.py          # Configuration management
    └── utils.py           # Utility functions
```

## Pipeline Overview

1. **Sync Phase**: Fetch changes from upstream English repository
2. **Translation Phase**: Use Gemini AI to translate new/changed content
3. **Validation Phase**: Ensure translation quality and formatting
4. **Integration Phase**: Create PR with translated content

## Configuration

The pipeline uses environment variables and configuration files:

- `GEMINI_API_KEY`: Google AI API key for translation
- `GITHUB_TOKEN`: GitHub token for API operations
- `UPSTREAM_REPO`: Source repository (jhipster/jhipster.github.io)
- `TARGET_REPO`: Target repository (jhipster/jp)

## Usage

See the main Makefile for available commands:

```bash
make help          # Show available commands
make sync          # Sync from upstream
make translate     # Run translation pipeline
make test          # Run tests
```

## Development

This is part of the EPIC issue for tracking the implementation of child issues 2-10.
Individual implementation details are handled in separate child issues.