#!/usr/bin/env python3
"""
Placeholder Protection Module

This module provides functionality to protect and restore various markdown/HTML elements
during translation to prevent them from being corrupted.

Supported protection patterns:
- Inline code (backticks)
- URLs
- Footnote IDs
- HTML attributes
- Jekyll variables and tags
- Code blocks
"""

import re
from typing import Dict, List, Tuple


class PlaceholderManager:
    """Manages placeholder protection and restoration for translation."""
    
    def __init__(self):
        self.placeholders: Dict[str, str] = {}
        self.counter = 0
    
    def _generate_placeholder(self) -> str:
        """Generate a unique placeholder token."""
        self.counter += 1
        return f"__PLACEHOLDER_{self.counter:04d}__"
    
    def protect_content(self, text: str) -> str:
        """
        Protect special content by replacing with placeholders.
        
        Args:
            text: Input text to protect
            
        Returns:
            Text with special content replaced by placeholders
        """
        # Reset for each new text
        self.placeholders.clear()
        self.counter = 0
        
        # Protection patterns in order of precedence
        patterns = [
            # Markdown links [text](url) - protect whole links first
            (r'\[[^\]]*\]\([^\)]+\)', 'markdown_link'),
            # Inline code (backticks)
            (r'`[^`\n]+`', 'inline_code'),
            # URLs (http/https) - after links to avoid nested protection
            (r'https?://[^\s\)\]\}]+', 'url'),
            # Footnote references [^id]
            (r'\[\^[^\]]+\]', 'footnote_ref'),
            # Footnote definitions [^id]:
            (r'\[\^[^\]]+\]:', 'footnote_def'),
            # Jekyll variables {{ site.url }}
            (r'\{\{[^}]+\}\}', 'jekyll_var'),
            # Jekyll tags {% tag %}
            (r'\{%[^%]+%\}', 'jekyll_tag'),
            # HTML tags with attributes
            (r'<[^>]+>', 'html_tag'),
            # GitHub issue/PR references #123
            (r'#\d+', 'github_ref'),
            # Version numbers (semantic versioning)
            (r'\bv?\d+\.\d+\.\d+(?:\.\d+)?\b', 'version'),
            # File paths with extensions
            (r'\b[\w\-\.]+\.(md|html|js|css|json|yml|yaml|xml)\b', 'file_path'),
        ]
        
        protected_text = text
        for pattern, pattern_type in patterns:
            protected_text = self._protect_pattern(protected_text, pattern, pattern_type)
        
        return protected_text
    
    def _protect_pattern(self, text: str, pattern: str, pattern_type: str) -> str:
        """Protect content matching a specific pattern."""
        def replace_match(match):
            original = match.group(0)
            placeholder = self._generate_placeholder()
            self.placeholders[placeholder] = original
            return placeholder
        
        return re.sub(pattern, replace_match, text)
    
    def restore_content(self, text: str) -> str:
        """
        Restore protected content by replacing placeholders with original content.
        
        Args:
            text: Text with placeholders
            
        Returns:
            Text with placeholders restored to original content
        """
        restored_text = text
        for placeholder, original in self.placeholders.items():
            restored_text = restored_text.replace(placeholder, original)
        
        return restored_text
    
    def get_placeholder_count(self) -> int:
        """Get the number of active placeholders."""
        return len(self.placeholders)
    
    def validate_restoration(self, original: str, restored: str) -> Tuple[bool, List[str]]:
        """
        Validate that all placeholders were properly restored.
        
        Args:
            original: Original text before protection
            restored: Text after protection and restoration
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check for remaining placeholders
        remaining_placeholders = re.findall(r'__PLACEHOLDER_\d+__', restored)
        if remaining_placeholders:
            issues.append(f"Unrestored placeholders: {remaining_placeholders}")
        
        # Check if we have the same number of special patterns
        for pattern, pattern_type in [
            (r'`[^`\n]+`', 'inline_code'),
            (r'https?://[^\s\)\]\}]+', 'url'),
            (r'\[\^[^\]]+\]', 'footnote'),
            (r'\{\{[^}]+\}\}', 'jekyll_var'),
        ]:
            original_matches = len(re.findall(pattern, original))
            restored_matches = len(re.findall(pattern, restored))
            if original_matches != restored_matches:
                issues.append(f"{pattern_type} count mismatch: {original_matches} -> {restored_matches}")
        
        return len(issues) == 0, issues


def protect_line(line: str) -> Tuple[str, PlaceholderManager]:
    """
    Convenience function to protect a single line.
    
    Args:
        line: Input line to protect
        
    Returns:
        Tuple of (protected_line, placeholder_manager)
    """
    manager = PlaceholderManager()
    protected = manager.protect_content(line)
    return protected, manager


def restore_line(line: str, manager: PlaceholderManager) -> str:
    """
    Convenience function to restore a single line.
    
    Args:
        line: Line with placeholders
        manager: PlaceholderManager used for protection
        
    Returns:
        Restored line
    """
    return manager.restore_content(line)


if __name__ == "__main__":
    # Example usage
    test_lines = [
        "Check out `console.log()` for debugging",
        "Visit https://www.jhipster.tech/ for more info",
        "See footnote reference[^1] and definition[^1]: explanation",
        "Use {{ site.url }} and {% include header.html %}",
        "File path: src/main/resources/config.yml",
        "GitHub issue #123 and version v7.9.3",
    ]
    
    for line in test_lines:
        print(f"Original: {line}")
        protected, manager = protect_line(line)
        print(f"Protected: {protected}")
        restored = restore_line(protected, manager)
        print(f"Restored: {restored}")
        is_valid, issues = manager.validate_restoration(line, restored)
        print(f"Valid: {is_valid}, Issues: {issues}")
        print("-" * 50)