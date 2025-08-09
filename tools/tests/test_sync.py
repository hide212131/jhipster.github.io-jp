"""
Test suite for sync functionality

Part of EPIC: JP自動同期・Gemini翻訳パイプライン導入（トラック用）
"""

import pytest
import sys
from pathlib import Path

# Add tools directory to path
sys.path.append(str(Path(__file__).parent.parent))

from common.config import get_config, validate_config

def test_get_config():
    """Test configuration loading."""
    config = get_config()
    assert isinstance(config, dict)
    assert "upstream_repo" in config
    assert config["upstream_repo"] == "jhipster/jhipster.github.io"

def test_validate_config():
    """Test configuration validation."""
    # Test with missing required config
    config = {"upstream_repo": "test"}
    assert not validate_config(config)
    
    # Test with valid config
    config = {
        "gemini_api_key": "test_key",
        "github_token": "test_token"
    }
    assert validate_config(config)

if __name__ == "__main__":
    pytest.main([__file__])