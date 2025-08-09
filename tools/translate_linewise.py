#!/usr/bin/env python3
"""
Line-wise Translation Module

This module provides line-by-line translation functionality with the following features:
- 1 input line → 1 output line guarantee
- Placeholder protection for special content
- Code fence state machine (skip translation inside code blocks)
- Micro-batch L000x=... format processing
- Fallback strategies
- Table handling support
"""

import re
import sys
from typing import List, Dict, Tuple, Optional
from enum import Enum
from .placeholder import PlaceholderManager


class ProcessingState(Enum):
    """States for content processing state machine."""
    NORMAL = "normal"
    CODE_FENCE = "code_fence"
    TABLE = "table"
    YAML_FRONTMATTER = "yaml_frontmatter"


class LinewiseTranslator:
    """Main class for line-wise translation with protection."""
    
    def __init__(self):
        self.state = ProcessingState.NORMAL
        self.code_fence_marker = None
        self.yaml_delimiter_count = 0
        self.translation_enabled = True
        
    def is_code_fence_start(self, line: str) -> Optional[str]:
        """Check if line starts a code fence and return the marker."""
        # Check for ``` or ~~~
        fence_match = re.match(r'^(\s*)(```|~~~)(.*)$', line)
        if fence_match:
            return fence_match.group(2)
        return None
    
    def is_code_fence_end(self, line: str, current_marker: str) -> bool:
        """Check if line ends the current code fence."""
        if current_marker:
            return re.match(rf'^(\s*){re.escape(current_marker)}(\s*)$', line) is not None
        return False
    
    def is_yaml_frontmatter(self, line: str) -> bool:
        """Check if line is YAML frontmatter delimiter."""
        return line.strip() == "---"
    
    def is_table_line(self, line: str) -> bool:
        """Check if line appears to be part of a markdown table."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Check for table separator (|---|---|)
        if re.match(r'^[\s\|]*:?-+:?[\s\|:-]*$', stripped):
            return True
        
        # Check for table row (starts and ends with |, or has multiple |)
        if '|' in stripped and (stripped.startswith('|') or stripped.endswith('|') or stripped.count('|') >= 2):
            return True
        
        return False
    
    def should_translate_line(self, line: str) -> bool:
        """Determine if a line should be translated based on current state."""
        stripped = line.strip()
        
        # Handle YAML frontmatter
        if self.is_yaml_frontmatter(line):
            self.yaml_delimiter_count += 1
            if self.yaml_delimiter_count == 1:
                self.state = ProcessingState.YAML_FRONTMATTER
            elif self.yaml_delimiter_count == 2:
                self.state = ProcessingState.NORMAL
            return False
        
        # Skip if in YAML frontmatter
        if self.state == ProcessingState.YAML_FRONTMATTER:
            return False
        
        # Handle code fences
        if self.state == ProcessingState.CODE_FENCE:
            if self.is_code_fence_end(line, self.code_fence_marker):
                self.state = ProcessingState.NORMAL
                self.code_fence_marker = None
            return False
        else:
            fence_marker = self.is_code_fence_start(line)
            if fence_marker:
                self.state = ProcessingState.CODE_FENCE
                self.code_fence_marker = fence_marker
                return False
        
        # Handle tables
        if self.is_table_line(line):
            self.state = ProcessingState.TABLE
            return False
        elif self.state == ProcessingState.TABLE:
            if stripped == "":
                # Empty line might end table
                self.state = ProcessingState.NORMAL
            elif not self.is_table_line(line):
                # Non-table line ends table
                self.state = ProcessingState.NORMAL
                # This line might be translatable
                return self._is_translatable_content(line)
            else:
                # Still in table
                return False
        
        # Normal content
        return self._is_translatable_content(line)
    
    def _is_translatable_content(self, line: str) -> bool:
        """Check if line contains translatable content."""
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            return False
        
        # Skip HTML comments
        if re.match(r'^\s*<!--.*-->\s*$', stripped):
            return False
        
        # Skip lines that are only special characters/markup
        if re.match(r'^[\s\-=*_#\[\](){}|]*$', stripped):
            return False
        
        # Skip lines that are only URLs
        if re.match(r'^\s*https?://[^\s]+\s*$', stripped):
            return False
        
        return True
    
    def create_microbatch_format(self, lines: List[str]) -> List[str]:
        """Convert lines to L000x=... microbatch format."""
        microbatch_lines = []
        for i, line in enumerate(lines, 1):
            if line.strip():  # Only add non-empty lines
                microbatch_lines.append(f"L{i:04d}={line}")
            else:
                microbatch_lines.append("")  # Preserve empty lines
        return microbatch_lines
    
    def parse_microbatch_format(self, lines: List[str]) -> List[str]:
        """Parse L000x=... format back to regular lines."""
        parsed_lines = []
        for line in lines:
            if line.strip() and line.startswith('L') and '=' in line:
                # Extract content after L000x=
                match = re.match(r'^L\d{4}=(.*)$', line)
                if match:
                    parsed_lines.append(match.group(1))
                else:
                    parsed_lines.append(line)  # Fallback
            elif line.strip() and '[TRANSLATED] L' in line and '=' in line:
                # Handle translated microbatch format
                match = re.search(r'L\d{4}=(.*)$', line)
                if match:
                    parsed_lines.append(match.group(1))
                else:
                    parsed_lines.append(line)  # Fallback
            else:
                parsed_lines.append(line)  # Empty or non-microbatch line
        return parsed_lines
    
    def mock_translate(self, text: str) -> str:
        """
        Mock translation function for testing.
        In real implementation, this would call an actual translation service.
        """
        # Simple mock: add [TRANSLATED] prefix for testing
        # Preserve any placeholders in the text
        if text.strip():
            return f"[TRANSLATED] {text}"
        return text
    
    def translate_line(self, line: str, line_number: int = 0) -> str:
        """
        Translate a single line with protection and state management.
        
        Args:
            line: Input line to translate
            line_number: Optional line number for debugging
            
        Returns:
            Translated line (or original if not translatable)
        """
        # Check if line should be translated
        if not self.should_translate_line(line):
            return line
        
        # Protect special content
        manager = PlaceholderManager()
        protected_line = manager.protect_content(line)
        
        # Translate the protected content
        try:
            translated_line = self.mock_translate(protected_line)
        except Exception as e:
            # Fallback: return original line if translation fails
            print(f"Translation failed for line {line_number}: {e}", file=sys.stderr)
            return line
        
        # Restore protected content
        restored_line = manager.restore_content(translated_line)
        
        # Validate restoration
        is_valid, issues = manager.validate_restoration(line, restored_line)
        if not is_valid:
            print(f"Restoration issues for line {line_number}: {issues}", file=sys.stderr)
            # Fallback: return original line if restoration fails
            return line
        
        return restored_line
    
    def translate_file(self, input_lines: List[str]) -> List[str]:
        """
        Translate an entire file line by line.
        
        Args:
            input_lines: List of input lines
            
        Returns:
            List of translated lines (same length as input)
        """
        # Reset state for new file
        self.state = ProcessingState.NORMAL
        self.yaml_delimiter_count = 0
        self.code_fence_marker = None
        
        output_lines = []
        
        for i, line in enumerate(input_lines):
            translated_line = self.translate_line(line, i + 1)
            output_lines.append(translated_line)
        
        # Ensure output has same number of lines as input
        assert len(output_lines) == len(input_lines), \
            f"Line count mismatch: {len(input_lines)} -> {len(output_lines)}"
        
        return output_lines
    
    def translate_file_with_microbatch(self, input_lines: List[str]) -> List[str]:
        """
        Translate file using microbatch format for better translation context.
        
        Args:
            input_lines: List of input lines
            
        Returns:
            List of translated lines
        """
        # Simpler approach: translate line by line but preserve state
        output_lines = []
        
        # Reset state
        self.state = ProcessingState.NORMAL
        self.yaml_delimiter_count = 0
        self.code_fence_marker = None
        
        for i, line in enumerate(input_lines):
            if self.should_translate_line(line):
                # Protect content
                manager = PlaceholderManager()
                protected_line = manager.protect_content(line)
                
                # Translate
                translated_line = self.mock_translate(protected_line)
                
                # Restore placeholders
                restored_line = manager.restore_content(translated_line)
                
                # Validate restoration
                is_valid, issues = manager.validate_restoration(line, restored_line)
                if not is_valid:
                    print(f"Restoration issues for line {i+1}: {issues}", file=sys.stderr)
                    # Fallback: return original line if restoration fails
                    output_lines.append(line)
                else:
                    output_lines.append(restored_line)
            else:
                output_lines.append(line)  # Non-translatable line
        
        return output_lines


def translate_markdown_file(input_file: str, output_file: str = None) -> None:
    """
    Translate a markdown file line by line.
    
    Args:
        input_file: Path to input markdown file
        output_file: Path to output file (defaults to input_file with .translated suffix)
    """
    if output_file is None:
        output_file = input_file.rsplit('.', 1)[0] + '.translated.md'
    
    translator = LinewiseTranslator()
    
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as f:
        input_lines = f.readlines()
    
    # Remove trailing newlines for processing
    input_lines = [line.rstrip('\n') for line in input_lines]
    
    # Translate
    output_lines = translator.translate_file_with_microbatch(input_lines)
    
    # Write output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in output_lines:
            f.write(line + '\n')
    
    print(f"Translated {len(input_lines)} lines from {input_file} to {output_file}")


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        translate_markdown_file(sys.argv[1])
    else:
        # Test with sample content
        test_content = """---
layout: default
title: Test Page
---

# Test Translation

This is a normal paragraph that should be translated.

```javascript
// This code should not be translated
console.log("hello world");
```

Another paragraph with `inline code` and [link](http://example.com).

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

Final paragraph after table.
""".strip().split('\n')
        
        translator = LinewiseTranslator()
        result = translator.translate_file_with_microbatch(test_content)
        
        print("=== ORIGINAL ===")
        for i, line in enumerate(test_content, 1):
            print(f"{i:2d}: {line}")
        
        print("\n=== TRANSLATED ===")
        for i, line in enumerate(result, 1):
            print(f"{i:2d}: {line}")
        
        print(f"\nLine count: {len(test_content)} -> {len(result)}")