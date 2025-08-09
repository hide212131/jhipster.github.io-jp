#!/usr/bin/env python3
"""
Translation alignment verification tool.

This tool verifies the structural alignment between original and translated files,
checking for line count consistency, code fence integrity, and table structure alignment.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any


class AlignmentVerifier:
    """Verifies structural alignment between original and translated files."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def verify_files(self, original_path: str, translated_path: str) -> bool:
        """
        Verify alignment between original and translated files.
        
        Args:
            original_path: Path to the original file
            translated_path: Path to the translated file
            
        Returns:
            True if files are aligned, False otherwise
        """
        try:
            original_content = self._read_file(original_path)
            translated_content = self._read_file(translated_path)
        except FileNotFoundError as e:
            self.errors.append(f"File not found: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading files: {e}")
            return False
        
        # Perform various alignment checks
        self._check_line_count(original_content, translated_content)
        self._check_code_fences(original_content, translated_content)
        self._check_tables(original_content, translated_content)
        self._check_headers(original_content, translated_content)
        self._check_links(original_content, translated_content)
        
        return len(self.errors) == 0
    
    def _read_file(self, file_path: str) -> List[str]:
        """Read file and return lines as list."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    
    def _check_line_count(self, original: List[str], translated: List[str]) -> None:
        """Check if line counts match between files."""
        original_count = len(original)
        translated_count = len(translated)
        
        if original_count != translated_count:
            self.errors.append(
                f"Line count mismatch: original has {original_count} lines, "
                f"translated has {translated_count} lines"
            )
    
    def _check_code_fences(self, original: List[str], translated: List[str]) -> None:
        """Check code fence alignment between files."""
        original_fences = self._extract_code_fences(original)
        translated_fences = self._extract_code_fences(translated)
        
        if len(original_fences) != len(translated_fences):
            self.errors.append(
                f"Code fence count mismatch: original has {len(original_fences)} fences, "
                f"translated has {len(translated_fences)} fences"
            )
            return
        
        # Check fence structure alignment
        for i, (orig_fence, trans_fence) in enumerate(zip(original_fences, translated_fences)):
            orig_start, orig_end, orig_lang = orig_fence
            trans_start, trans_end, trans_lang = trans_fence
            
            if orig_lang != trans_lang:
                self.errors.append(
                    f"Code fence language mismatch at fence {i+1}: "
                    f"original uses '{orig_lang}', translated uses '{trans_lang}' "
                    f"(starting at line {trans_start})"
                )
            
            # Check relative positioning
            if i > 0:
                prev_orig = original_fences[i-1]
                prev_trans = translated_fences[i-1]
                
                orig_gap = orig_start - prev_orig[1]
                trans_gap = trans_start - prev_trans[1]
                
                # Allow some flexibility in gap size but flag major discrepancies
                if abs(orig_gap - trans_gap) > 5:
                    self.warnings.append(
                        f"Large gap difference between code fences {i} and {i+1}: "
                        f"original gap = {orig_gap}, translated gap = {trans_gap} "
                        f"(fence starts at line {trans_start})"
                    )
    
    def _extract_code_fences(self, lines: List[str]) -> List[Tuple[int, int, str]]:
        """Extract code fence positions and languages."""
        fences = []
        in_fence = False
        fence_start = 0
        fence_lang = ""
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith('```'):
                if not in_fence:
                    # Opening fence
                    in_fence = True
                    fence_start = i
                    fence_lang = stripped[3:].strip()
                else:
                    # Closing fence
                    in_fence = False
                    fences.append((fence_start, i, fence_lang))
        
        # Check for unclosed fences
        if in_fence:
            self.errors.append(f"Unclosed code fence starting at line {fence_start}")
        
        return fences
    
    def _check_tables(self, original: List[str], translated: List[str]) -> None:
        """Check table structure alignment."""
        original_tables = self._extract_tables(original)
        translated_tables = self._extract_tables(translated)
        
        if len(original_tables) != len(translated_tables):
            self.errors.append(
                f"Table count mismatch: original has {len(original_tables)} tables, "
                f"translated has {len(translated_tables)} tables"
            )
            return
        
        for i, (orig_table, trans_table) in enumerate(zip(original_tables, translated_tables)):
            orig_start, orig_rows, orig_cols = orig_table
            trans_start, trans_rows, trans_cols = trans_table
            
            if orig_rows != trans_rows:
                self.errors.append(
                    f"Table {i+1} row count mismatch: original has {orig_rows} rows, "
                    f"translated has {trans_rows} rows (starting at line {trans_start})"
                )
            
            if orig_cols != trans_cols:
                self.errors.append(
                    f"Table {i+1} column count mismatch: original has {orig_cols} columns, "
                    f"translated has {trans_cols} columns (starting at line {trans_start})"
                )
    
    def _extract_tables(self, lines: List[str]) -> List[Tuple[int, int, int]]:
        """Extract table information (start_line, row_count, column_count)."""
        tables = []
        in_table = False
        table_start = 0
        table_rows = 0
        table_cols = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check if this looks like a table row
            if '|' in stripped and stripped.count('|') >= 2:
                if not in_table:
                    # Start of new table
                    in_table = True
                    table_start = i
                    table_rows = 1
                    table_cols = stripped.count('|') - 1
                else:
                    # Continue table
                    table_rows += 1
                    current_cols = stripped.count('|') - 1
                    if current_cols != table_cols:
                        # Column count changed, might be a separator row
                        if not re.match(r'^\s*\|[\s\-\|:]+\|\s*$', stripped):
                            # Not a separator, this is an inconsistency
                            table_cols = max(table_cols, current_cols)
            else:
                if in_table:
                    # End of table
                    in_table = False
                    tables.append((table_start, table_rows, table_cols))
        
        # Handle case where file ends with a table
        if in_table:
            tables.append((table_start, table_rows, table_cols))
        
        return tables
    
    def _check_headers(self, original: List[str], translated: List[str]) -> None:
        """Check header structure alignment."""
        original_headers = self._extract_headers(original)
        translated_headers = self._extract_headers(translated)
        
        if len(original_headers) != len(translated_headers):
            self.errors.append(
                f"Header count mismatch: original has {len(original_headers)} headers, "
                f"translated has {len(translated_headers)} headers"
            )
            return
        
        for i, (orig_header, trans_header) in enumerate(zip(original_headers, translated_headers)):
            orig_line, orig_level = orig_header
            trans_line, trans_level = trans_header
            
            if orig_level != trans_level:
                self.errors.append(
                    f"Header {i+1} level mismatch: original is level {orig_level}, "
                    f"translated is level {trans_level} (at line {trans_line})"
                )
    
    def _extract_headers(self, lines: List[str]) -> List[Tuple[int, int]]:
        """Extract header positions and levels."""
        headers = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for ATX-style headers (# ## ### etc.)
            if stripped.startswith('#'):
                level = 0
                for char in stripped:
                    if char == '#':
                        level += 1
                    else:
                        break
                
                if level <= 6 and (len(stripped) == level or stripped[level] == ' '):
                    headers.append((i, level))
        
        return headers
    
    def _check_links(self, original: List[str], translated: List[str]) -> None:
        """Check link structure alignment."""
        original_links = self._count_markdown_links(original)
        translated_links = self._count_markdown_links(translated)
        
        if original_links != translated_links:
            self.warnings.append(
                f"Link count difference: original has {original_links} links, "
                f"translated has {translated_links} links"
            )
    
    def _count_markdown_links(self, lines: List[str]) -> int:
        """Count markdown links in the content."""
        content = ''.join(lines)
        # Match [text](url) and [text][ref] patterns
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)|\[([^\]]+)\]\[([^\]]*)\]'
        return len(re.findall(link_pattern, content))
    
    def generate_report(self) -> str:
        """Generate a detailed verification report."""
        report = []
        
        if not self.errors and not self.warnings:
            report.append("✅ All checks passed! Files are properly aligned.")
            return '\n'.join(report)
        
        if self.errors:
            report.append("❌ ERRORS FOUND:")
            for i, error in enumerate(self.errors, 1):
                report.append(f"  {i}. {error}")
            report.append("")
        
        if self.warnings:
            report.append("⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                report.append(f"  {i}. {warning}")
            report.append("")
        
        if self.errors:
            report.append("🚨 Fix the errors above before proceeding with the translation.")
        
        return '\n'.join(report)


def main():
    """Main entry point for the verification tool."""
    parser = argparse.ArgumentParser(
        description='Verify structural alignment between original and translated files'
    )
    parser.add_argument(
        'original',
        help='Path to the original file'
    )
    parser.add_argument(
        'translated',
        help='Path to the translated file'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Verify files exist
    original_path = Path(args.original)
    translated_path = Path(args.translated)
    
    if not original_path.exists():
        print(f"Error: Original file not found: {original_path}", file=sys.stderr)
        sys.exit(2)
    
    if not translated_path.exists():
        print(f"Error: Translated file not found: {translated_path}", file=sys.stderr)
        sys.exit(2)
    
    # Run verification
    verifier = AlignmentVerifier()
    is_aligned = verifier.verify_files(str(original_path), str(translated_path))
    
    # Generate and display report
    report = verifier.generate_report()
    print(report)
    
    if args.verbose and (verifier.errors or verifier.warnings):
        print(f"\nFiles compared:")
        print(f"  Original:   {original_path}")
        print(f"  Translated: {translated_path}")
    
    # Exit with appropriate code
    if not is_aligned:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()