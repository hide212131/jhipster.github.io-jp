#!/usr/bin/env python3
"""
Development mode filtering utilities for jp sync tool.

Provides filtering capabilities for development mode operations:
- Filter by commit (before specified commit)  
- Limit number of items to process
- Filter by file paths
"""

import re
import subprocess
from typing import List, Optional, Dict, Any
from pathlib import Path


class DevFilter:
    """Handles filtering logic for development mode sync operations."""
    
    def __init__(self, before: Optional[str] = None, limit: Optional[int] = None, 
                 paths: Optional[List[str]] = None):
        """
        Initialize development filter.
        
        Args:
            before: Commit hash/reference to filter commits before
            limit: Maximum number of items to process
            paths: List of file paths to filter by
        """
        self.before = before
        self.limit = limit
        self.paths = paths or []
        
    def filter_commits(self, commits: List[str]) -> List[str]:
        """
        Filter commits based on --before option.
        
        Args:
            commits: List of commit hashes
            
        Returns:
            Filtered list of commits
        """
        if not self.before:
            return commits
            
        try:
            # First try to get commits before the specified commit
            cmd = ['git', 'rev-list', f'{self.before}^', '--']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            before_commits = set(result.stdout.strip().split('\n') if result.stdout.strip() else [])
            
            # Filter commits that are before the specified commit
            filtered = [commit for commit in commits if commit in before_commits]
            return filtered
            
        except subprocess.CalledProcessError:
            # Fallback: try to get commit ancestry using merge-base or other methods
            try:
                # Check if the specified commit exists at all
                check_cmd = ['git', 'rev-parse', '--verify', f'{self.before}^{{commit}}']
                subprocess.run(check_cmd, capture_output=True, text=True, check=True)
                
                # If it exists but rev-list failed, it might be a shallow repo
                # In this case, filter by commit order in the provided list
                if self.before in commits:
                    before_index = commits.index(self.before)
                    return commits[before_index + 1:]  # Return commits after the specified one
                else:
                    print(f"Warning: Commit {self.before} not found in provided commit list")
                    return commits
                    
            except subprocess.CalledProcessError:
                print(f"Warning: Could not find commit {self.before}, returning all commits")
                return commits
    
    def filter_paths(self, files: List[str]) -> List[str]:
        """
        Filter files based on --paths option.
        
        Args:
            files: List of file paths
            
        Returns:
            Filtered list of files matching path patterns
        """
        if not self.paths:
            return files
            
        filtered_files = []
        for file_path in files:
            for pattern in self.paths:
                # Support glob-like patterns
                if self._matches_pattern(file_path, pattern):
                    filtered_files.append(file_path)
                    break
                    
        return filtered_files
    
    def apply_limit(self, items: List[Any]) -> List[Any]:
        """
        Apply limit to list of items.
        
        Args:
            items: List of items to limit
            
        Returns:
            Limited list of items
        """
        if self.limit is None:
            return items
        return items[:self.limit]
    
    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """
        Check if file path matches the given pattern.
        
        Args:
            file_path: File path to check
            pattern: Pattern to match against
            
        Returns:
            True if path matches pattern
        """
        # Convert glob-like pattern to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        return bool(re.match(regex_pattern, file_path))
    
    def get_untranslated_files(self, base_path: str = '.') -> List[str]:
        """
        Get list of files that need translation (placeholder implementation).
        
        Args:
            base_path: Base directory to search
            
        Returns:
            List of files needing translation
        """
        # This is a placeholder implementation
        # In a real scenario, this would identify untranslated files
        # based on project-specific criteria
        
        try:
            # Find markdown files as an example
            cmd = ['find', base_path, '-name', '*.md', '-type', 'f']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return [f for f in files if f]  # Filter out empty strings
        except subprocess.CalledProcessError:
            return []
    
    def apply_all_filters(self, commits: List[str] = None, files: List[str] = None) -> Dict[str, List[str]]:
        """
        Apply all configured filters.
        
        Args:
            commits: List of commits to filter
            files: List of files to filter
            
        Returns:
            Dictionary with filtered commits and files
        """
        result = {}
        
        if commits is not None:
            filtered_commits = self.filter_commits(commits)
            filtered_commits = self.apply_limit(filtered_commits)
            result['commits'] = filtered_commits
        
        if files is not None:
            filtered_files = self.filter_paths(files)
            filtered_files = self.apply_limit(filtered_files)
            result['files'] = filtered_files
        
        return result