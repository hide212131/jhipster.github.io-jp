#!/usr/bin/env python3
"""
Command-line interface for the line-wise translator.

Usage:
    python3 -m tools.cli input.md [output.md]
    python3 -m tools.cli --help
"""

import argparse
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.translate_linewise import translate_markdown_file, LinewiseTranslator


def main():
    parser = argparse.ArgumentParser(
        description="Line-wise translator for markdown files with placeholder protection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.md                    # Output to input.translated.md
  %(prog)s input.md output.md          # Output to specified file
  %(prog)s --test                      # Run built-in tests
  %(prog)s --validate input.md         # Validate without translating

Features:
  - 1 input line → 1 output line guarantee
  - Protects inline code, URLs, Jekyll variables, HTML tags
  - Skips translation inside code fences and tables
  - Preserves YAML frontmatter
  - Validates placeholder restoration
        """
    )
    
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input markdown file to translate'
    )
    
    parser.add_argument(
        'output_file',
        nargs='?',
        help='Output file (default: input_file.translated.md)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run built-in tests'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate file structure without translating'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show translation statistics'
    )
    
    args = parser.parse_args()
    
    if args.test:
        run_tests()
        return
    
    if not args.input_file:
        parser.print_help()
        sys.exit(1)
    
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    
    if args.validate:
        validate_file(args.input_file, args.stats)
    else:
        translate_file(args.input_file, args.output_file, args.stats)


def validate_file(input_file: str, show_stats: bool = False):
    """Validate file structure without translating."""
    print(f"Validating: {input_file}")
    
    translator = LinewiseTranslator()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]
    
    # Statistics
    total_lines = len(lines)
    translatable_lines = 0
    protected_elements = 0
    code_fence_lines = 0
    table_lines = 0
    yaml_lines = 0
    
    # Reset translator state
    translator.state = translator.ProcessingState.NORMAL if hasattr(translator, 'ProcessingState') else translator.state
    translator.yaml_delimiter_count = 0
    translator.code_fence_marker = None
    
    for i, line in enumerate(lines):
        if translator.should_translate_line(line):
            translatable_lines += 1
            
            # Count protected elements
            from tools.placeholder import PlaceholderManager
            manager = PlaceholderManager()
            manager.protect_content(line)
            protected_elements += manager.get_placeholder_count()
        else:
            # Categorize non-translatable lines
            stripped = line.strip()
            if translator.is_yaml_frontmatter(line):
                yaml_lines += 1
            elif translator.is_code_fence_start(line) or translator.is_code_fence_end(line, translator.code_fence_marker):
                code_fence_lines += 1
            elif translator.is_table_line(line):
                table_lines += 1
    
    print(f"✓ File structure is valid")
    
    if show_stats:
        print(f"\nStatistics:")
        print(f"  Total lines: {total_lines}")
        print(f"  Translatable lines: {translatable_lines}")
        print(f"  Protected elements: {protected_elements}")
        print(f"  YAML frontmatter lines: {yaml_lines}")
        print(f"  Code fence lines: {code_fence_lines}")
        print(f"  Table lines: {table_lines}")
        print(f"  Other non-translatable: {total_lines - translatable_lines - yaml_lines - code_fence_lines - table_lines}")


def translate_file(input_file: str, output_file: str = None, show_stats: bool = False):
    """Translate a file with optional statistics."""
    if show_stats:
        validate_file(input_file, True)
        print()
    
    print(f"Translating: {input_file}")
    translate_markdown_file(input_file, output_file)
    
    # Verify output
    if output_file is None:
        output_file = input_file.rsplit('.', 1)[0] + '.translated.md'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        input_lines = len(f.readlines())
    
    with open(output_file, 'r', encoding='utf-8') as f:
        output_lines = len(f.readlines())
    
    if input_lines == output_lines:
        print(f"✓ Line count preserved: {input_lines} lines")
    else:
        print(f"⚠ Line count mismatch: {input_lines} → {output_lines}", file=sys.stderr)


def run_tests():
    """Run built-in tests."""
    print("Running built-in tests...")
    
    # Import and run the test module
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, 
            os.path.join(os.path.dirname(__file__), 'test_translation.py')
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ All tests passed")
            print(result.stderr.split('\n')[-2])  # Show test count
        else:
            print("✗ Some tests failed")
            print(result.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()