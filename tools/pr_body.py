#!/usr/bin/env python3
"""
PR body generation utilities for JHipster translation tools.
Generates pull request descriptions and commit messages.
"""

from typing import List, Dict
from datetime import datetime
from tools.discover_changes import FileChange


class PRBodyGenerator:
    """Generates PR descriptions and commit messages."""
    
    def __init__(self):
        """Initialize PR body generator."""
        pass
    
    def generate_pr_title(self, changes: List[FileChange], change_summary: Dict[str, int]) -> str:
        """Generate PR title based on changes."""
        total_files = len(changes)
        
        if total_files == 1:
            change = changes[0]
            action = self._get_action_word(change.change_type)
            return f"Translation: {action} {change.file_path}"
        
        return f"Translation: Update {total_files} files from upstream"
    
    def generate_pr_body(self, changes: List[FileChange], change_summary: Dict[str, int]) -> str:
        """Generate detailed PR body."""
        timestamp = datetime.now().isoformat()
        
        body_parts = [
            "## 🌍 Translation Update",
            "",
            f"**Generated at:** {timestamp}",
            "",
            "### 📊 Summary",
            f"- **Total files changed:** {len(changes)}",
            f"- **Added:** {change_summary.get('added', 0)} files",
            f"- **Modified:** {change_summary.get('modified', 0)} files", 
            f"- **Deleted:** {change_summary.get('deleted', 0)} files",
            "",
            "### 📝 Changed Files",
        ]
        
        # Group changes by type
        for change_type in ['added', 'modified', 'deleted']:
            files_of_type = [c for c in changes if c.change_type == change_type]
            if files_of_type:
                body_parts.append(f"\n#### {change_type.title()} Files")
                for change in files_of_type:
                    body_parts.append(f"- `{change.file_path}`")
        
        body_parts.extend([
            "",
            "### 🔄 Translation Process",
            "This PR was generated automatically from upstream changes.",
            "The following process was applied:",
            "",
            "1. 🔍 Detected changes from upstream repository",
            "2. 📝 Extracted translatable content",
            "3. 🌐 Applied automatic translation",
            "4. ✅ Validated translation quality",
            "5. 📋 Generated this pull request",
            "",
            "### ⚠️ Review Required",
            "Please review the translations for:",
            "- Technical accuracy",
            "- Cultural appropriateness", 
            "- Consistency with existing translations",
            "",
            "---",
            "*This PR was generated automatically by the JHipster translation system.*"
        ])
        
        return "\n".join(body_parts)
    
    def generate_commit_message(self, changes: List[FileChange]) -> str:
        """Generate commit message for changes."""
        if len(changes) == 1:
            change = changes[0]
            action = self._get_action_word(change.change_type)
            return f"feat(translation): {action} {change.file_path}"
        
        # Group by change type for summary
        summary_parts = []
        change_counts = {}
        for change in changes:
            change_counts[change.change_type] = change_counts.get(change.change_type, 0) + 1
        
        for change_type, count in change_counts.items():
            if count > 0:
                action = self._get_action_word(change_type)
                summary_parts.append(f"{action} {count} file{'s' if count > 1 else ''}")
        
        summary = ", ".join(summary_parts)
        return f"feat(translation): {summary}"
    
    def _get_action_word(self, change_type: str) -> str:
        """Get appropriate action word for change type."""
        action_map = {
            'added': 'add',
            'modified': 'update', 
            'deleted': 'remove'
        }
        return action_map.get(change_type, 'update')
    
    def generate_branch_name(self, changes: List[FileChange]) -> str:
        """Generate branch name for the changes."""
        timestamp = datetime.now().strftime("%Y%m%d")
        
        if len(changes) == 1:
            change = changes[0]
            # Sanitize file path for branch name
            file_name = change.file_path.replace('/', '-').replace('.', '-')
            return f"translation/{timestamp}-{file_name}"
        
        return f"translation/{timestamp}-batch-update"
    
    def generate_file_summary(self, file_change: FileChange) -> str:
        """Generate summary for a single file change."""
        lines = []
        lines.append(f"**File:** `{file_change.file_path}`")
        lines.append(f"**Change Type:** {file_change.change_type.title()}")
        
        if file_change.old_content and file_change.new_content:
            old_lines = len(file_change.old_content.splitlines())
            new_lines = len(file_change.new_content.splitlines())
            lines.append(f"**Lines:** {old_lines} → {new_lines}")
        
        return "\n".join(lines)