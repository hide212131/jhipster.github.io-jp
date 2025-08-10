#!/usr/bin/env python3
"""
Placeholder processing utilities for JHipster translation tools.
Handles placeholders in translation content to preserve code blocks, links, etc.
"""

import re
from typing import Dict, List, Tuple


class PlaceholderProcessor:
    """Handles placeholder replacement in translation content."""
    
    # Patterns that should be preserved during translation
    PRESERVE_PATTERNS = [
        (r'```[\s\S]*?```', 'CODE_BLOCK'),  # Code blocks
        (r'`[^`]+`', 'INLINE_CODE'),  # Inline code
        (r'\[([^\]]+)\]\(([^)]+)\)', 'LINK'),  # Markdown links
        (r'!\[([^\]]*)\]\(([^)]+)\)', 'IMAGE'),  # Images
        (r'\{[^}]+\}', 'VARIABLE'),  # Variables/placeholders
        (r'<[^>]+>', 'HTML_TAG'),  # HTML tags
    ]
    
    def __init__(self):
        """Initialize placeholder processor."""
        self.placeholders: Dict[str, str] = {}
        self.counter = 0
    
    def _generate_placeholder(self, placeholder_type: str) -> str:
        """Generate a unique placeholder."""
        self.counter += 1
        return f"__PLACEHOLDER_{placeholder_type}_{self.counter}__"
    
    def preserve_content(self, text: str) -> str:
        """Replace preservable content with placeholders."""
        self.placeholders.clear()
        self.counter = 0
        
        for pattern, placeholder_type in self.PRESERVE_PATTERNS:
            def replacer(match):
                placeholder = self._generate_placeholder(placeholder_type)
                self.placeholders[placeholder] = match.group(0)
                return placeholder
            
            text = re.sub(pattern, replacer, text)
        
        return text
    
    def restore_content(self, text: str) -> str:
        """Restore placeholders with original content."""
        for placeholder, original in self.placeholders.items():
            text = text.replace(placeholder, original)
        return text
    
    def process_for_translation(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Prepare text for translation by preserving special content."""
        processed_text = self.preserve_content(text)
        return processed_text, self.placeholders.copy()
    
    def restore_after_translation(self, translated_text: str, placeholders: Dict[str, str]) -> str:
        """Restore placeholders in translated text."""
        for placeholder, original in placeholders.items():
            translated_text = translated_text.replace(placeholder, original)
        return translated_text