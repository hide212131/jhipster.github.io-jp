"""
Configuration management for JP translation pipeline

Part of EPIC: JP自動同期・Gemini翻訳パイプライン導入（トラック用）
"""

import os
from pathlib import Path
from typing import Dict, Any

# Default configuration
DEFAULT_CONFIG = {
    "upstream_repo": "jhipster/jhipster.github.io",
    "target_repo": "jhipster/jp", 
    "gemini_model": "gemini-pro",
    "translation_batch_size": 10,
    "max_retries": 3,
    "log_level": "INFO"
}

def get_config() -> Dict[str, Any]:
    """Get configuration from environment variables and defaults."""
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables if present
    config["gemini_api_key"] = os.getenv("GEMINI_API_KEY")
    config["github_token"] = os.getenv("GITHUB_TOKEN")
    config["upstream_repo"] = os.getenv("UPSTREAM_REPO", config["upstream_repo"])
    config["target_repo"] = os.getenv("TARGET_REPO", config["target_repo"])
    
    return config

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate required configuration parameters."""
    required_keys = ["gemini_api_key", "github_token"]
    
    for key in required_keys:
        if not config.get(key):
            print(f"❌ Missing required configuration: {key}")
            return False
    
    return True