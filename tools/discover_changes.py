#!/usr/bin/env python3
"""
Change discovery utilities for JHipster translation tools.
Discovers and analyzes changes between upstream and local repositories.
"""

from typing import List, Dict, NamedTuple, Optional
from pathlib import Path
from tools.git_utils import GitUtils
from tools.file_filters import FileFilters


class FileChange(NamedTuple):
    """Represents a file change."""
    file_path: str
    change_type: str  # 'added', 'modified', 'deleted'
    old_content: Optional[str]
    new_content: Optional[str]


class ChangeDiscoverer:
    """Discovers changes between different git references."""
    
    def __init__(self, repo_path: str = "."):
        """Initialize change discoverer."""
        self.git_utils = GitUtils(repo_path)
        self.file_filters = FileFilters()
    
    def discover_changes(self, base_ref: str = "main", target_ref: str = "HEAD") -> List[FileChange]:
        """Discover all changes between two git references."""
        if not self.git_utils.is_git_repo():
            raise RuntimeError("Not in a git repository")
        
        # Get list of changed files
        changed_files = self.git_utils.get_changed_files(base_ref)
        
        changes = []
        for file_path in changed_files:
            change = self._analyze_file_change(file_path, base_ref, target_ref)
            if change:
                changes.append(change)
        
        return changes
    
    def discover_translatable_changes(self, base_ref: str = "main", target_ref: str = "HEAD") -> List[FileChange]:
        """Discover only changes in translatable files."""
        all_changes = self.discover_changes(base_ref, target_ref)
        return [change for change in all_changes if self.file_filters.is_translatable(change.file_path)]
    
    def _analyze_file_change(self, file_path: str, base_ref: str, target_ref: str) -> Optional[FileChange]:
        """Analyze a specific file change."""
        try:
            # Try to get old content
            try:
                old_content = self.git_utils.get_file_content(file_path, base_ref)
            except RuntimeError:
                old_content = None
            
            # Try to get new content
            try:
                new_content = self.git_utils.get_file_content(file_path, target_ref)
            except RuntimeError:
                # Check if file exists in working directory
                file_obj = Path(self.git_utils.repo_path) / file_path
                if file_obj.exists():
                    new_content = file_obj.read_text(encoding='utf-8')
                else:
                    new_content = None
            
            # Determine change type
            if old_content is None and new_content is not None:
                change_type = "added"
            elif old_content is not None and new_content is None:
                change_type = "deleted"
            elif old_content != new_content:
                change_type = "modified"
            else:
                return None  # No actual change
            
            return FileChange(
                file_path=file_path,
                change_type=change_type,
                old_content=old_content,
                new_content=new_content
            )
        
        except Exception as e:
            print(f"Warning: Could not analyze change for {file_path}: {e}")
            return None
    
    def get_change_summary(self, changes: List[FileChange]) -> Dict[str, int]:
        """Get summary of changes by type."""
        summary = {"added": 0, "modified": 0, "deleted": 0}
        
        for change in changes:
            summary[change.change_type] += 1
        
        return summary
    
    def filter_changes_by_pattern(self, changes: List[FileChange], pattern: str) -> List[FileChange]:
        """Filter changes by file path pattern."""
        import re
        regex = re.compile(pattern)
        return [change for change in changes if regex.search(change.file_path)]
    
    def get_modified_content_lines(self, file_change: FileChange) -> List[str]:
        """Get lines that were modified in a file change."""
        if file_change.change_type != "modified":
            return []
        
        from tools.line_diff import LineDiffProcessor
        diff_processor = LineDiffProcessor()
        
        return diff_processor.get_modified_lines(
            file_change.old_content or "",
            file_change.new_content or ""
        )