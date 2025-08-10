"""Placeholder protection and restoration for translation."""

import re
from typing import Dict, List, Tuple


class PlaceholderProtector:
    """Protect and restore placeholders during translation."""
    
    def __init__(self):
        """Initialize placeholder patterns."""
        self.placeholders: Dict[str, str] = {}
        self.counter = 0
        
        # Patterns to protect (order matters)
        self.patterns = [
            # Code fences (highest priority)
            (r"```[\s\S]*?```", "CODE_FENCE"),
            # Inline code
            (r"`[^`\n]+`", "INLINE_CODE"), 
            # URLs in markdown links (before plain URLs)
            (r"\[([^\]]*)\]\(([^)]+)\)", "MARKDOWN_LINK"),
            # HTML tags and attributes (before plain URLs to capture URLs in attributes)
            (r"<[^>]+>", "HTML_TAG"),
            # Plain URLs (after HTML tags to avoid conflicts)
            (r"https?://[^\s\)]+", "URL"),
            # Footnote references
            (r"\[\^[^\]]+\]", "FOOTNOTE"),
            # Table separators and alignment
            (r"\|[\s:|-]+\|", "TABLE_SEP"),
            # Trailing double spaces (markdown line breaks)
            (r"  $", "TRAILING_SPACES"),
        ]
    
    def protect(self, text: str) -> str:
        """Protect placeholders in text."""
        self.placeholders.clear()
        self.counter = 0
        
        protected_text = text
        
        for pattern, placeholder_type in self.patterns:
            protected_text = self._protect_pattern(
                protected_text, pattern, placeholder_type
            )
        
        return protected_text
    
    def restore(self, text: str) -> str:
        """Restore placeholders in text."""
        restored_text = text
        
        # Multiple passes to handle nested placeholders
        max_passes = 10  # Prevent infinite loops
        for pass_num in range(max_passes):
            initial_text = restored_text
            
            # Sort by placeholder key in reverse order to handle nested placeholders
            # (restore outer placeholders before inner ones)
            for placeholder_key in sorted(self.placeholders.keys(), reverse=True):
                original_value = self.placeholders[placeholder_key]
                restored_text = restored_text.replace(placeholder_key, original_value)
            
            # If no changes were made in this pass, we're done
            if restored_text == initial_text:
                break
        
        return restored_text
    
    def _protect_pattern(self, text: str, pattern: str, placeholder_type: str) -> str:
        """Protect specific pattern with placeholders."""
        def replace_match(match):
            self.counter += 1
            placeholder_key = f"__PLACEHOLDER_{placeholder_type}_{self.counter}__"
            self.placeholders[placeholder_key] = match.group(0)
            return placeholder_key
        
        return re.sub(pattern, replace_match, text, flags=re.MULTILINE)
    
    def is_code_fence_line(self, line: str) -> bool:
        """Check if line is part of code fence."""
        stripped = line.strip()
        return stripped.startswith("```") or stripped.startswith("~~~")
    
    def protect_code_fences(self, lines: List[str]) -> List[str]:
        """Protect entire code fence blocks."""
        protected_lines = []
        in_code_fence = False
        
        for line in lines:
            if self.is_code_fence_line(line):
                in_code_fence = not in_code_fence
                # Protect the fence line itself
                self.counter += 1
                placeholder_key = f"__PLACEHOLDER_FENCE_LINE_{self.counter}__"
                self.placeholders[placeholder_key] = line
                protected_lines.append(placeholder_key)
            elif in_code_fence:
                # Protect content inside fence
                self.counter += 1
                placeholder_key = f"__PLACEHOLDER_FENCE_CONTENT_{self.counter}__"
                self.placeholders[placeholder_key] = line
                protected_lines.append(placeholder_key)
            else:
                protected_lines.append(line)
        
        return protected_lines
    
    def get_stats(self) -> Dict[str, int]:
        """Get protection statistics."""
        stats = {}
        for key in self.placeholders:
            placeholder_type = key.split("_")[2]  # Extract type from key
            stats[placeholder_type] = stats.get(placeholder_type, 0) + 1
        return stats