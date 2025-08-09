"""
Configuration management for pipeline tools.

This module provides configuration handling for various pipeline scripts,
including environment variables, settings, and runtime configuration.
"""

import os
from pathlib import Path
from typing import Any, Dict


class Config:
    """Configuration manager for pipeline tools."""

    def __init__(self, config_file: str = None):
        """Initialize configuration manager.

        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self._load_default_config()
        if config_file and Path(config_file).exists():
            self._load_config_file()

    def _load_default_config(self) -> None:
        """Load default configuration values."""
        self._config = {
            "git": {
                "default_branch": "main",
                "remote_name": "origin",
            },
            "sync": {
                "batch_size": 100,
                "retry_count": 3,
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - " "%(message)s",
            },
        }

    def _load_config_file(self) -> None:
        """Load configuration from file."""
        # Template implementation - extend as needed
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key (supports dot notation like
                'git.default_branch')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_env(self, key: str, default: str = None) -> str:
        """Get environment variable value.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        return os.environ.get(key, default)


# Global configuration instance
config = Config()
