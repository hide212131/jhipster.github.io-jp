#!/usr/bin/env python3
"""
Configuration management for JHipster translation tools.
Handles environment variables, API keys, and configuration settings.
"""

import os
from typing import Optional


class Config:
    """Configuration class for translation tools."""
    
    def __init__(self):
        """Initialize configuration with environment variables."""
        self.gemini_api_key: Optional[str] = os.getenv('GEMINI_API_KEY')
        self.github_token: Optional[str] = os.getenv('GITHUB_TOKEN')
        self.dry_run: bool = os.getenv('DRY_RUN', 'false').lower() == 'true'
        
    def validate(self) -> bool:
        """Validate required configuration."""
        return self.gemini_api_key is not None
    
    def get_gemini_api_key(self) -> str:
        """Get Gemini API key, raise if not set."""
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        return self.gemini_api_key


# Global configuration instance
config = Config()