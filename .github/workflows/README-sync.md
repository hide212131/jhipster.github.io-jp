# LLM Translation Sync Workflow (sync.yml)

This document describes the implementation of the GitHub Actions workflow for automated LLM translation synchronization.

## Overview

The `sync.yml` workflow provides automated translation synchronization from the upstream JHipster documentation (English) to the Japanese translation site using Google Gemini LLM.

## Features

### Triggers
- **Scheduled**: Every Monday at 01:00 UTC (10:00 JST)
- **Manual**: `workflow_dispatch` with optional parameters:
  - `dry_run`: Create draft PR instead of regular PR (for testing)
  - `upstream_ref`: Specify upstream reference (default: upstream/main)

### Security
- Repository check: Only runs on `hide212131/jhipster.github.io-jp` (not on forks)
- Secrets handling: Requires `GEMINI_API_KEY` and uses `GITHUB_TOKEN`
- Proper permissions: `contents: write`, `pull-requests: write`

### Process Flow
1. **Setup**: Checkout, Python 3.12, install dependencies
2. **Git Setup**: Configure git user, add upstream remote, fetch changes
3. **Translation**: Run `run_sync.py --mode ci` with LLM translation
4. **PR Creation**: Create PR only if changes are detected
5. **Artifacts**: Upload results and logs for debugging

## Integration with Existing Infrastructure

### Relationship to sync-upstream.yml
- **Complementary**: sync.yml focuses on LLM translation while sync-upstream.yml handles basic merging
- **Timing**: Runs 1 hour after sync-upstream.yml to avoid conflicts
- **Purpose**: sync-upstream.yml for structural sync, sync.yml for content translation

### Existing Tools Integration
- Uses the complete Python translation pipeline in `tools/` directory
- Leverages `run_sync.py` as the main orchestrator
- Outputs structured JSON results and PR body content
- Follows the specification in `tools/spec.md`

## Configuration Requirements

### Repository Secrets
- `GEMINI_API_KEY`: Google Gemini API key for translation
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

### Dependencies
- Python 3.12 with packages from `tools/requirements.txt`
- Git for repository operations
- GitHub CLI for PR creation

## Dry Run Support

When `dry_run` is set to `true` via manual trigger:
- Creates draft PR instead of regular PR
- Allows testing without affecting main workflow
- Useful for validating translations before production deployment

## Error Handling

- Validates API key presence before running translation
- Provides detailed error messages and logs
- Uploads artifacts even on failure for debugging
- Graceful handling of no-changes scenarios

## Output Artifacts

### Always Generated
- `sync-results-{run_id}`: Contains all output files from translation process
- Retention: 30 days

### Files in Artifacts
- `sync_results.json`: Main results and statistics
- `pr_body.md`: Generated PR description (if PR created)
- `changes.json`: Detailed change analysis
- Various debug and log files

## Testing and Validation

The workflow has been validated for:
- ✅ Python environment and dependency installation
- ✅ Integration with existing `run_sync.py` script
- ✅ JSON output structure and PR decision logic
- ✅ YAML syntax and GitHub Actions compatibility
- ✅ Error handling and fallback scenarios

## Manual Testing

To test the workflow components locally:
```bash
cd tools
pip install -r requirements.txt
python run_sync.py --mode dev --limit 1 --output .out/test_results.json
```

## Future Enhancements

- Integration with translation quality metrics
- Support for selective file translation
- Enhanced notification system
- Translation memory and caching improvements