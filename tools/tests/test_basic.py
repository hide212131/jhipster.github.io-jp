"""Basic tests for translation tools."""

import sys
from pathlib import Path

import pytest

# Add tools directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config
from file_filters import FileFilters
from placeholder import PlaceholderManager


def test_config_initialization():
    """Test configuration initialization."""
    assert config.base_dir.exists()
    assert config.tools_dir.exists()
    assert config.target_extensions
    assert config.gemini_model


def test_file_filters():
    """Test file filtering functionality."""
    filters = FileFilters()

    # Test translatable files
    assert filters.is_translatable_file("docs/example.md")
    assert filters.is_translatable_file("pages/test.mdx")
    assert not filters.is_translatable_file("image.png")
    assert not filters.is_translatable_file("node_modules/package.json")


def test_placeholder_manager():
    """Test placeholder protection and restoration."""
    manager = PlaceholderManager()

    text = "Check out [this link](https://example.com) and `some code`"
    protected = manager.protect_content(text)
    restored = manager.restore_content(protected)

    assert restored == text
    assert manager.verify_integrity(protected)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
