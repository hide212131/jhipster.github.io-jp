"""Configuration management for JHipster.github.io-jp tools."""

import os
from typing import Dict, Any, Optional


class Config:
    """Configuration class for managing tool settings."""

    def __init__(self):
        """Initialize configuration with default values."""
        self._config = {
            "repository_root": self._get_repository_root(),
            "source_lang": "en",
            "target_lang": "ja",
            "docs_dir": "docs",
            "output_dir": "docs_ja",
        }

    def _get_repository_root(self) -> str:
        """Get the repository root directory."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(current_dir)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value by key."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value

    def update(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration with dictionary."""
        self._config.update(config_dict)

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()


# Global configuration instance
config = Config()
