#!/usr/bin/env python3
"""
Tests for config.py module.
"""

import pytest
import os
from unittest.mock import patch
from tools.config import Config, config


class TestConfig:
    """Test cases for Config class."""
    
    def test_config_initialization_with_env_vars(self):
        """Test config initialization with environment variables."""
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test-api-key',
            'GITHUB_TOKEN': 'test-github-token',
            'DRY_RUN': 'true'
        }):
            test_config = Config()
            assert test_config.gemini_api_key == 'test-api-key'
            assert test_config.github_token == 'test-github-token'
            assert test_config.dry_run is True
    
    def test_config_initialization_without_env_vars(self):
        """Test config initialization without environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            test_config = Config()
            assert test_config.gemini_api_key is None
            assert test_config.github_token is None
            assert test_config.dry_run is False
    
    def test_validate_with_api_key(self):
        """Test validation when API key is present."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            test_config = Config()
            assert test_config.validate() is True
    
    def test_validate_without_api_key(self):
        """Test validation when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            test_config = Config()
            assert test_config.validate() is False
    
    def test_get_gemini_api_key_success(self):
        """Test getting API key when present."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            test_config = Config()
            assert test_config.get_gemini_api_key() == 'test-key'
    
    def test_get_gemini_api_key_failure(self):
        """Test getting API key when missing."""
        with patch.dict(os.environ, {}, clear=True):
            test_config = Config()
            with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is required"):
                test_config.get_gemini_api_key()
    
    def test_dry_run_parsing(self):
        """Test dry run flag parsing."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('false', False),
            ('False', False),
            ('anything_else', False),
            ('', False)
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {'DRY_RUN': env_value}):
                test_config = Config()
                assert test_config.dry_run == expected


class TestGlobalConfig:
    """Test cases for global config instance."""
    
    def test_global_config_exists(self):
        """Test that global config instance exists."""
        assert config is not None
        assert isinstance(config, Config)