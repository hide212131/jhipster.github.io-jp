"""
Tests for configuration module.
"""

import os

# Add tools to path for testing
import sys
import tempfile
from pathlib import Path

import pytest

tools_path = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(tools_path))

from config import Config


class TestConfig:
    """Test cases for Config class."""

    def test_config_initialization(self):
        """Test config initialization with default values."""
        config = Config()

        assert config.get("git.default_branch") == "main"
        assert config.get("git.remote_name") == "origin"
        assert config.get("sync.batch_size") == 100
        assert config.get("logging.level") == "INFO"

    def test_config_get_with_default(self):
        """Test getting configuration values with defaults."""
        config = Config()

        # Existing key
        assert config.get("git.default_branch") == "main"

        # Non-existing key with default
        assert config.get("nonexistent.key", "default_value") == "default_value"

        # Non-existing key without default
        assert config.get("nonexistent.key") is None

    def test_config_set_value(self):
        """Test setting configuration values."""
        config = Config()

        # Set new value
        config.set("test.key", "test_value")
        assert config.get("test.key") == "test_value"

        # Override existing value
        config.set("git.default_branch", "develop")
        assert config.get("git.default_branch") == "develop"

    def test_config_nested_keys(self):
        """Test nested key handling."""
        config = Config()

        # Set nested value
        config.set("new.nested.key", "nested_value")
        assert config.get("new.nested.key") == "nested_value"

        # Test intermediate keys are created
        assert isinstance(config.get("new"), dict)
        assert isinstance(config.get("new.nested"), dict)

    def test_config_env_variables(self):
        """Test environment variable handling."""
        config = Config()

        # Set test environment variable
        test_var = "TEST_CONFIG_VAR"
        test_value = "test_env_value"
        os.environ[test_var] = test_value

        try:
            assert config.get_env(test_var) == test_value
            assert config.get_env("NONEXISTENT_VAR", "default") == "default"
            assert config.get_env("NONEXISTENT_VAR") is None
        finally:
            # Clean up
            del os.environ[test_var]

    def test_config_with_file(self):
        """Test config initialization with file."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name

        try:
            # Test with existing but empty file
            config = Config(config_file)
            assert (
                config.get("git.default_branch") == "main"
            )  # Default should still work
        finally:
            # Clean up
            os.unlink(config_file)

    def test_config_file_not_exists(self):
        """Test config with non-existent file."""
        config = Config("/nonexistent/config.json")

        # Should still work with defaults
        assert config.get("git.default_branch") == "main"
