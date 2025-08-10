"""Placeholder protection and restoration utilities."""

import re
from typing import Dict, List, Tuple


class PlaceholderManager:
    """Manage placeholders for protecting special content during translation."""

    def __init__(self):
        self.placeholders: Dict[str, str] = {}
        self.counter = 0

        # Patterns for content that should not be translated
        self.protection_patterns = [
            # URLs in markdown links
            (r"\[([^\]]+)\]\(([^)]+)\)", self._protect_markdown_link),
            # Inline code
            (r"`([^`]+)`", self._protect_inline_code),
            # HTML attributes
            (r'(\w+)="([^"]*)"', self._protect_html_attribute),
            # Table separators and alignment
            (r"\|[\s:-]+\|", self._protect_table_separator),
            # Trailing spaces (2+ spaces for line breaks)
            (r"  +$", self._protect_trailing_spaces),
            # Footnote references
            (r"\[[^\]]+\]:", self._protect_footnote_ref),
        ]

    def _generate_placeholder(self) -> str:
        """Generate unique placeholder."""
        self.counter += 1
        return f"__PLACEHOLDER_{self.counter:04d}__"

    def _protect_markdown_link(self, match: re.Match) -> str:
        """Protect markdown link, only URL part."""
        text, url = match.groups()
        url_placeholder = self._generate_placeholder()
        self.placeholders[url_placeholder] = url
        return f"[{text}]({url_placeholder})"

    def _protect_inline_code(self, match: re.Match) -> str:
        """Protect inline code completely."""
        placeholder = self._generate_placeholder()
        self.placeholders[placeholder] = match.group(0)
        return placeholder

    def _protect_html_attribute(self, match: re.Match) -> str:
        """Protect HTML attribute values."""
        attr_name, attr_value = match.groups()
        placeholder = self._generate_placeholder()
        self.placeholders[placeholder] = attr_value
        return f'{attr_name}="{placeholder}"'

    def _protect_table_separator(self, match: re.Match) -> str:
        """Protect table separator lines."""
        placeholder = self._generate_placeholder()
        self.placeholders[placeholder] = match.group(0)
        return placeholder

    def _protect_trailing_spaces(self, match: re.Match) -> str:
        """Protect trailing spaces."""
        placeholder = self._generate_placeholder()
        self.placeholders[placeholder] = match.group(0)
        return placeholder

    def _protect_footnote_ref(self, match: re.Match) -> str:
        """Protect footnote references."""
        placeholder = self._generate_placeholder()
        self.placeholders[placeholder] = match.group(0)
        return placeholder

    def protect_content(self, text: str) -> str:
        """Protect special content by replacing with placeholders."""
        protected_text = text

        for pattern, handler in self.protection_patterns:
            protected_text = re.sub(
                pattern, handler, protected_text, flags=re.MULTILINE
            )

        return protected_text

    def restore_content(self, text: str) -> str:
        """Restore original content from placeholders."""
        restored_text = text

        # Restore in reverse order to handle nested placeholders
        for placeholder, original in reversed(list(self.placeholders.items())):
            restored_text = restored_text.replace(placeholder, original)

        return restored_text

    def verify_integrity(self, text: str) -> bool:
        """Verify all placeholders are present and intact."""
        for placeholder in self.placeholders:
            if placeholder not in text:
                return False
        return True

    def clear(self):
        """Clear all placeholders."""
        self.placeholders.clear()
        self.counter = 0
