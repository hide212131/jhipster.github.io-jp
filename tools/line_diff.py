#!/usr/bin/env python3
"""
Line-by-line diff utilities for JHipster translation tools.
Provides functions to analyze and process line-level changes.
"""

import difflib
from typing import List, NamedTuple, Optional
from enum import Enum


class LineChangeType(Enum):
    """Types of line changes."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class LineChange(NamedTuple):
    """Represents a line change."""
    line_number: int
    change_type: LineChangeType
    old_content: Optional[str]
    new_content: Optional[str]


class LineDiffProcessor:
    """Processes line-by-line differences between files."""
    
    def __init__(self):
        """Initialize line diff processor."""
        pass
    
    def compare_files(self, old_content: str, new_content: str) -> List[LineChange]:
        """Compare two file contents and return line changes."""
        old_lines = old_content.splitlines() if old_content else []
        new_lines = new_content.splitlines() if new_content else []
        
        changes = []
        differ = difflib.unified_diff(
            old_lines, new_lines, 
            lineterm='', n=0
        )
        
        # Skip the header lines
        diff_lines = list(differ)[2:]
        
        line_num = 1
        for line in diff_lines:
            if line.startswith('@@'):
                # Parse line number from hunk header
                match = re.search(r'-(\d+)', line)
                if match:
                    line_num = int(match.group(1))
            elif line.startswith('-'):
                changes.append(LineChange(
                    line_number=line_num,
                    change_type=LineChangeType.REMOVED,
                    old_content=line[1:],
                    new_content=None
                ))
                line_num += 1
            elif line.startswith('+'):
                changes.append(LineChange(
                    line_number=line_num,
                    change_type=LineChangeType.ADDED,
                    old_content=None,
                    new_content=line[1:]
                ))
            else:
                line_num += 1
        
        return changes
    
    def get_modified_lines(self, old_content: str, new_content: str) -> List[str]:
        """Get list of lines that have been modified."""
        old_lines = old_content.splitlines() if old_content else []
        new_lines = new_content.splitlines() if new_content else []
        
        modified_lines = []
        for line in difflib.unified_diff(old_lines, new_lines, lineterm=''):
            if line.startswith('+') and not line.startswith('+++'):
                modified_lines.append(line[1:])
        
        return modified_lines
    
    def extract_translation_candidates(self, changes: List[LineChange]) -> List[str]:
        """Extract lines that are candidates for translation."""
        candidates = []
        for change in changes:
            if change.change_type == LineChangeType.ADDED and change.new_content:
                # Only consider non-empty lines that contain actual content
                content = change.new_content.strip()
                if content and not self._is_code_line(content):
                    candidates.append(content)
        
        return candidates
    
    def _is_code_line(self, line: str) -> bool:
        """Check if a line appears to be code rather than prose."""
        # Simple heuristics to identify code lines
        code_indicators = [
            line.strip().startswith('```'),
            line.strip().startswith('#'),
            line.strip().startswith('import '),
            line.strip().startswith('from '),
            '=' in line and not line.strip().startswith('title:'),
            '{' in line and '}' in line,
        ]
        
        return any(code_indicators)


# Required import for regex
import re