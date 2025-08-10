#!/usr/bin/env python3
"""Test segmentation and reflow functionality with sample files."""

import os
import sys
from pathlib import Path
from segmenter import TextSegmenter
from reflow import LineReflow


def load_sample_file(file_path: str) -> str:
    """Load a sample markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def simulate_translation(text: str) -> str:
    """Simulate translation by appending [翻訳] to English text."""
    # Simple simulation: add Japanese markers to show translation
    lines = text.split('\n')
    translated_lines = []
    
    for line in lines:
        if line.strip() and not line.strip().startswith('---') and not line.strip().startswith('```'):
            # Add translation marker to content lines
            translated_lines.append(line + " [翻訳]")
        else:
            # Keep structural lines as-is (frontmatter, code fences, empty lines)
            translated_lines.append(line)
    
    return '\n'.join(translated_lines)


def test_segmentation_and_reflow(file_path: str) -> dict:
    """Test segmentation and reflow on a sample file."""
    print(f"\n=== Testing {os.path.basename(file_path)} ===")
    
    # Load sample
    original_text = load_sample_file(file_path)
    original_lines = original_text.split('\n')
    original_line_count = len(original_lines)
    
    print(f"Original file: {original_line_count} lines")
    
    # Initialize components
    segmenter = TextSegmenter()
    reflow = LineReflow()
    
    # Test segmentation
    blocks = segmenter.segment_into_blocks(original_text)
    print(f"Segmented into {len(blocks)} blocks:")
    
    block_info = []
    for i, block in enumerate(blocks):
        block_type = block['type']
        line_count = block['line_count']
        first_line = block['lines'][0] if block['lines'] else ""
        print(f"  Block {i}: {block_type} ({line_count} lines) - {first_line[:50]}...")
        block_info.append({
            'type': block_type,
            'line_count': line_count,
            'translatable': segmenter.is_translatable_block(block)
        })
    
    # Test translation and reflow for each block
    translated_blocks = []
    total_original_lines = 0
    total_translated_lines = 0
    
    for i, block in enumerate(blocks):
        original_block_lines = block['lines']
        original_count = len(original_block_lines)
        total_original_lines += original_count
        
        if segmenter.is_translatable_block(block):
            # Simulate translation
            block_text = '\n'.join(original_block_lines)
            translated_text = simulate_translation(block_text)
            
            # Reflow to match original line count
            reflowed_lines = reflow.reflow_to_match_lines(original_block_lines, translated_text)
            
            # Preserve structure markers
            reflowed_lines = reflow.maintain_structure_markers(original_block_lines, reflowed_lines)
            
            translated_blocks.extend(reflowed_lines)
            total_translated_lines += len(reflowed_lines)
            
            print(f"  Block {i}: {original_count} -> {len(reflowed_lines)} lines")
        else:
            # Keep non-translatable blocks as-is
            translated_blocks.extend(original_block_lines)
            total_translated_lines += original_count
            print(f"  Block {i}: {original_count} lines (preserved)")
    
    # Check line count alignment
    line_count_match = total_original_lines == total_translated_lines
    print(f"\nLine count check: {total_original_lines} original -> {total_translated_lines} translated")
    print(f"Line count match: {'✓' if line_count_match else '✗'}")
    
    return {
        'file_path': file_path,
        'original_line_count': original_line_count,
        'translated_line_count': total_translated_lines,
        'line_count_match': line_count_match,
        'blocks': block_info,
        'translated_text': '\n'.join(translated_blocks)
    }


def test_context_provision():
    """Test context provision functionality."""
    print("\n=== Testing Context Provision ===")
    
    segmenter = TextSegmenter()
    
    # Create sample blocks
    sample_text = """# Heading 1

This is a paragraph.

## Heading 2

- List item 1
- List item 2

Another paragraph here.

```javascript
const code = "sample";
```

Final paragraph."""
    
    blocks = segmenter.segment_into_blocks(sample_text)
    print(f"Sample has {len(blocks)} blocks")
    
    # Test context for middle block (index 3)
    target_index = 3
    context_blocks = segmenter.get_context_blocks(blocks, target_index, context_size=2)
    print(f"Context for block {target_index} (±2): {len(context_blocks)} blocks")
    
    for i, block in enumerate(context_blocks):
        actual_index = max(0, target_index - 2) + i
        marker = " <- TARGET" if actual_index == target_index else ""
        print(f"  Context block {actual_index}: {block['type']}{marker}")


def main():
    """Run segmentation and reflow tests."""
    print("=== Segmentation and Reflow Tests ===")
    
    # Test with repository sample files
    repo_root = Path(__file__).parent.parent
    sample_files = [
        repo_root / "README.md",
        repo_root / "pages" / "video_tutorial.md"
    ]
    
    results = []
    
    for file_path in sample_files:
        if file_path.exists():
            result = test_segmentation_and_reflow(str(file_path))
            results.append(result)
        else:
            print(f"Sample file not found: {file_path}")
    
    # Test context provision
    test_context_provision()
    
    # Summary
    print(f"\n=== Test Summary ===")
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['line_count_match'])
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    for result in results:
        status = "✓" if result['line_count_match'] else "✗"
        print(f"{status} {os.path.basename(result['file_path'])}: {result['original_line_count']} -> {result['translated_line_count']}")
    
    # Return success if all tests passed
    return 0 if passed_tests == total_tests else 1


if __name__ == '__main__':
    sys.exit(main())