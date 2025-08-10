#!/usr/bin/env python3
"""
Tests for file_filters.py module.
"""

import pytest
from tools.file_filters import FileFilters


class TestFileFilters:
    """Test cases for FileFilters class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.filters = FileFilters()
    
    def test_is_translatable_markdown_files(self):
        """Test that markdown files are considered translatable."""
        test_cases = [
            ('docs/test.md', True),
            ('pages/sample.md', True),
            ('README.md', True),
            ('docs/subdirectory/file.mdx', True),
        ]
        
        for file_path, expected in test_cases:
            assert self.filters.is_translatable(file_path) == expected
    
    def test_should_ignore_system_files(self):
        """Test that system files are ignored."""
        test_cases = [
            ('node_modules/package/file.js', True),
            ('build/output.html', True),
            ('.git/config', True),
            ('.github/workflows/ci.yml', True),
            ('__pycache__/module.pyc', True),
            ('src/component.ts', True),
            ('package.json', True),
        ]
        
        for file_path, expected in test_cases:
            assert self.filters.should_ignore(file_path) == expected
    
    def test_should_not_ignore_translatable_files(self):
        """Test that translatable files are not ignored."""
        test_cases = [
            'docs/guide.md',
            'pages/tutorial.mdx',
            'README.md',
        ]
        
        for file_path in test_cases:
            assert self.filters.should_ignore(file_path) is False
    
    def test_filter_files(self):
        """Test filtering of file lists."""
        input_files = [
            'docs/guide.md',           # Should be included
            'src/component.ts',        # Should be excluded
            'pages/tutorial.mdx',      # Should be included
            'node_modules/dep.js',     # Should be excluded
            'build/output.html',       # Should be excluded
            'README.md',               # Should be included
        ]
        
        expected_output = [
            'docs/guide.md',
            'pages/tutorial.mdx',
            'README.md',
        ]
        
        result = self.filters.filter_files(input_files)
        assert result == expected_output
    
    def test_categorize_files(self):
        """Test file categorization."""
        input_files = [
            'docs/guide.md',           # translatable
            'src/component.ts',        # ignored
            'pages/tutorial.mdx',      # translatable
            'node_modules/dep.js',     # ignored
            'some_other_file.txt',     # other
        ]
        
        result = self.filters.categorize_files(input_files)
        
        assert 'docs/guide.md' in result['translatable']
        assert 'pages/tutorial.mdx' in result['translatable']
        assert 'src/component.ts' in result['ignored']
        assert 'node_modules/dep.js' in result['ignored']
        assert 'some_other_file.txt' in result['other']
    
    def test_edge_cases(self):
        """Test edge cases for file filtering."""
        # Empty file path
        assert self.filters.is_translatable('') is False
        
        # Root level files
        assert self.filters.is_translatable('test.md') is True
        
        # Files with multiple extensions
        assert self.filters.is_translatable('file.backup.md') is True