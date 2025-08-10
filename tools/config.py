"""Configuration management for LLM translation pipeline."""

import os
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration class for translation pipeline."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        # Repository settings
        self.upstream_repo = "jhipster/jhipster.github.io"
        self.origin_repo = "hide212131/jhipster.github.io-jp"
        self.meta_branch = "translation-meta"
        
        # Translation settings
        self.target_extensions = {".md", ".markdown", ".mdx", ".html", ".adoc"}
        self.excluded_paths = {
            "_site/", "node_modules/", ".git/", "vendor/",
            ".github/", "static/", "build/"
        }
        self.excluded_extensions = {
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
            ".yml", ".yaml", ".json", ".css", ".scss", ".xml"
        }
        
        # LLM settings
        self.max_concurrent_requests = 8
        self.retry_max_attempts = 3
        self.retry_delay = 1.0
        
        # Output settings
        self.output_dir = Path("tools/.out")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.gemini_api_key:
            print("Warning: GEMINI_API_KEY not set")
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "upstream_repo": self.upstream_repo,
            "origin_repo": self.origin_repo,
            "meta_branch": self.meta_branch,
            "target_extensions": list(self.target_extensions),
            "excluded_paths": list(self.excluded_paths),
            "excluded_extensions": list(self.excluded_extensions),
            "max_concurrent_requests": self.max_concurrent_requests,
            "retry_max_attempts": self.retry_max_attempts,
            "retry_delay": self.retry_delay,
        }


# Global config instance
config = Config()