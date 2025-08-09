#!/usr/bin/env python3
"""
Line-wise translation utilities for JHipster translation tools.
Provides functions to translate content line by line while preserving structure.
"""

from typing import List, Tuple, Dict
from tools.llm import get_translator
from tools.placeholder import PlaceholderProcessor


class LinewiseTranslator:
    """Handles line-by-line translation with structure preservation."""
    
    def __init__(self, use_mock_llm: bool = False):
        """Initialize linewise translator."""
        self.translator = get_translator(use_mock=use_mock_llm)
        self.placeholder_processor = PlaceholderProcessor()
    
    def translate_lines(self, lines: List[str], source_lang: str = "en", target_lang: str = "ja") -> List[str]:
        """Translate a list of lines while preserving structure."""
        if not lines:
            return []
        
        # Process each line to preserve special content
        processed_lines = []
        placeholder_maps = []
        
        for line in lines:
            if self._should_translate_line(line):
                processed_line, placeholders = self.placeholder_processor.process_for_translation(line)
                processed_lines.append(processed_line)
                placeholder_maps.append(placeholders)
            else:
                # Don't translate code blocks, empty lines, etc.
                processed_lines.append(line)
                placeholder_maps.append({})
        
        # Translate processed lines
        translated_lines = []
        for i, (line, placeholders) in enumerate(zip(processed_lines, placeholder_maps)):
            if placeholders or self._should_translate_line(lines[i]):
                try:
                    translated = self.translator.translate_text(line, source_lang, target_lang)
                    # Restore placeholders
                    if placeholders:
                        translated = self.placeholder_processor.restore_after_translation(
                            translated, placeholders
                        )
                    translated_lines.append(translated)
                except Exception as e:
                    print(f"Warning: Translation failed for line: {line[:50]}... Error: {e}")
                    translated_lines.append(lines[i])  # Use original on failure
            else:
                translated_lines.append(lines[i])
        
        return translated_lines
    
    def translate_file_content(self, content: str, source_lang: str = "en", target_lang: str = "ja") -> str:
        """Translate entire file content line by line."""
        lines = content.splitlines()
        translated_lines = self.translate_lines(lines, source_lang, target_lang)
        return '\n'.join(translated_lines)
    
    def _should_translate_line(self, line: str) -> bool:
        """Determine if a line should be translated."""
        stripped = line.strip()
        
        # Don't translate empty lines
        if not stripped:
            return False
        
        # Don't translate code blocks
        if stripped.startswith('```'):
            return False
        
        # Don't translate YAML frontmatter
        if stripped.startswith('---'):
            return False
        
        # Don't translate HTML comments
        if stripped.startswith('<!--') and stripped.endswith('-->'):
            return False
        
        # Don't translate lines that are mostly code
        if self._is_mostly_code(stripped):
            return False
        
        return True
    
    def _is_mostly_code(self, line: str) -> bool:
        """Check if line appears to be mostly code."""
        # Simple heuristics
        code_indicators = [
            line.startswith('#') and not line.startswith('# '),  # Bash comments, not markdown headers
            line.startswith('import '),
            line.startswith('from '),
            '=' in line and '==' not in line and line.count('=') == 1,
            line.startswith('def '),
            line.startswith('class '),
            '{' in line and '}' in line and line.count('{') == line.count('}'),
        ]
        
        return any(code_indicators)
    
    def translate_changed_lines_only(self, 
                                   original_lines: List[str], 
                                   new_lines: List[str],
                                   source_lang: str = "en", 
                                   target_lang: str = "ja") -> List[str]:
        """Translate only the lines that have changed."""
        # This is a simplified implementation
        # In a real scenario, you'd use proper diff algorithms
        
        if len(original_lines) != len(new_lines):
            # If line counts differ, translate all new lines
            return self.translate_lines(new_lines, source_lang, target_lang)
        
        result = []
        for orig, new in zip(original_lines, new_lines):
            if orig != new and self._should_translate_line(new):
                # Line changed, translate it
                translated = self.translator.translate_text(new, source_lang, target_lang)
                result.append(translated)
            else:
                # Line unchanged or shouldn't be translated
                result.append(new)
        
        return result