"""Configuration management for LLM translation tools."""

import os
from pathlib import Path
from typing import Any, Dict


class Config:
    """Configuration settings for the translation system."""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.tools_dir = self.base_dir / "tools"
        self.output_dir = self.tools_dir / ".out"

        # LLM Configuration
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = "gemini-1.5-flash"

        # Git Configuration
        self.upstream_remote = "upstream"
        self.origin_remote = "origin"
        self.main_branch = "main"
        self.meta_branch = "translation-meta"

        # Translation Configuration
        self.target_extensions = [".md", ".markdown", ".mdx", ".html", ".adoc"]
        self.exclude_paths = [
            "_site/",
            "node_modules/",
            ".git/",
            "vendor/",
            "__pycache__/",
            "*.pyc",
            ".pytest_cache/",
        ]

        # Processing Configuration
        self.max_concurrent_requests = 8
        self.max_retries = 3
        self.similarity_threshold = 0.98

    def ensure_output_dir(self):
        """Ensure output directory exists."""
        self.output_dir.mkdir(exist_ok=True)

    def get_github_token(self) -> str:
        """Get GitHub token from environment."""
        return os.getenv("GITHUB_TOKEN", "")


# Global configuration instance
config = Config()
