#!/usr/bin/env python3
"""
File filtering utilities for JHipster translation tools.
Provides functions to filter and categorize files for translation.
"""

import re
from pathlib import Path
from typing import List, Set


class FileFilters:
    """File filtering and categorization utilities."""
    
    # File patterns that should be translated
    TRANSLATABLE_PATTERNS = [
        r'\.md$',
        r'\.mdx$',
        r'docs/.*\.md$',
        r'pages/.*\.md$',
    ]
    
    # File patterns that should be ignored
    IGNORE_PATTERNS = [
        r'node_modules/',
        r'build/',
        r'\.git/',
        r'\.github/',
        r'__pycache__/',
        r'\.py$',
        r'\.js$',
        r'\.ts$',
        r'\.json$',
        r'\.yml$',
        r'\.yaml$',
    ]
    
    def __init__(self):
        """Initialize file filters."""
        self.translatable_regex = [re.compile(pattern) for pattern in self.TRANSLATABLE_PATTERNS]
        self.ignore_regex = [re.compile(pattern) for pattern in self.IGNORE_PATTERNS]
    
    def is_translatable(self, file_path: str) -> bool:
        """Check if file should be translated."""
        if self.should_ignore(file_path):
            return False
        
        return any(pattern.search(file_path) for pattern in self.translatable_regex)
    
    def should_ignore(self, file_path: str) -> bool:
        """Check if file should be ignored."""
        return any(pattern.search(file_path) for pattern in self.ignore_regex)
    
    def filter_files(self, file_paths: List[str]) -> List[str]:
        """Filter list of files to only translatable ones."""
        return [path for path in file_paths if self.is_translatable(path)]
    
    def categorize_files(self, file_paths: List[str]) -> dict:
        """Categorize files into translatable, ignored, and other."""
        result = {
            'translatable': [],
            'ignored': [],
            'other': []
        }
        
        for path in file_paths:
            if self.should_ignore(path):
                result['ignored'].append(path)
            elif self.is_translatable(path):
                result['translatable'].append(path)
            else:
                result['other'].append(path)
        
        return result