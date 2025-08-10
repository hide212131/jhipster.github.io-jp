#!/usr/bin/env python3
"""Test full segmentation, context provision, and reflow pipeline."""

import os
import sys
from pathlib import Path
from segmenter import TextSegmenter
from reflow import LineReflow


def simulate_translation_with_context(context_text: str) -> str:
    """Simulate translation of context-enriched text."""
    # In a real implementation, this would send to LLM
    # For now, just add [翻訳] to the target content
    lines = context_text.split('\n')
    translated_lines = []
    
    for line in lines:
        if line.strip() and not line.startswith('__'):
            translated_lines.append(line + " [翻訳]")
        else:
            translated_lines.append(line)
    
    return '\n'.join(translated_lines)


def test_full_pipeline(file_path: str) -> dict:
    """Test complete segmentation -> context -> translation -> reflow pipeline."""
    print(f"\n=== Full Pipeline Test: {os.path.basename(file_path)} ===")
    
    # Load sample
    with open(file_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    
    original_lines = original_text.split('\n')
    original_line_count = len(original_lines)
    
    print(f"Original file: {original_line_count} lines")
    
    # Initialize components
    segmenter = TextSegmenter()
    reflow = LineReflow()
    
    # Step 1: Segment into blocks
    blocks = segmenter.segment_into_blocks(original_text)
    print(f"Segmented into {len(blocks)} blocks")
    
    # Step 2: Process each translatable block with context
    translated_blocks = []
    total_original_lines = 0
    total_translated_lines = 0
    context_demonstrations = 0
    
    for i, block in enumerate(blocks):
        original_block_lines = block['lines']
        original_count = len(original_block_lines)
        total_original_lines += original_count
        
        if segmenter.is_translatable_block(block) and context_demonstrations < 3:
            # Demonstrate context provision for first few translatable blocks
            print(f"\n--- Block {i} with Context ---")
            
            # Build context text
            context_text = segmenter.build_context_text(blocks, i, context_size=1)
            print("Context text:")
            print(context_text[:200] + "..." if len(context_text) > 200 else context_text)
            
            # Simulate translation with context
            translated_context = simulate_translation_with_context(context_text)
            
            # Extract target translation
            translated_text = segmenter.extract_target_from_context(translated_context)
            print(f"Extracted translation: {translated_text[:100]}...")
            
            # Reflow to match original line count
            reflowed_lines = reflow.reflow_to_match_lines(original_block_lines, translated_text)
            reflowed_lines = reflow.maintain_structure_markers(original_block_lines, reflowed_lines)
            
            translated_blocks.extend(reflowed_lines)
            total_translated_lines += len(reflowed_lines)
            
            print(f"Reflow: {original_count} -> {len(reflowed_lines)} lines")
            context_demonstrations += 1
            
        elif segmenter.is_translatable_block(block):
            # Regular translation without context demonstration
            block_text = '\n'.join(original_block_lines)
            translated_text = simulate_translation_with_context(block_text)
            
            reflowed_lines = reflow.reflow_to_match_lines(original_block_lines, translated_text)
            reflowed_lines = reflow.maintain_structure_markers(original_block_lines, reflowed_lines)
            
            translated_blocks.extend(reflowed_lines)
            total_translated_lines += len(reflowed_lines)
            
        else:
            # Keep non-translatable blocks as-is
            translated_blocks.extend(original_block_lines)
            total_translated_lines += original_count
    
    # Step 3: Verify line count alignment
    line_count_match = total_original_lines == total_translated_lines
    print(f"\nFinal check: {total_original_lines} original -> {total_translated_lines} translated")
    print(f"Line count match: {'✓' if line_count_match else '✗'}")
    
    return {
        'file_path': file_path,
        'original_line_count': original_line_count,
        'translated_line_count': total_translated_lines,
        'line_count_match': line_count_match,
        'blocks_count': len(blocks),
        'translated_text': '\n'.join(translated_blocks)
    }


def test_code_fence_preservation():
    """Test that code fences are properly preserved."""
    print("\n=== Code Fence Preservation Test ===")
    
    sample_text = """# Installation Guide

Here's how to install:

```bash
npm install -g @jhipster/generator-jhipster
jhipster --version
```

That's it! You can now use JHipster.

```javascript
const generator = require('generator-jhipster');
console.log('JHipster rocks!');
```

Happy coding!"""
    
    segmenter = TextSegmenter()
    blocks = segmenter.segment_into_blocks(sample_text)
    
    code_blocks = [b for b in blocks if b['type'] == 'code_fence']
    print(f"Found {len(code_blocks)} code blocks:")
    
    for i, block in enumerate(code_blocks):
        lang = block.get('language', 'none')
        print(f"  Code block {i}: {lang} ({block['line_count']} lines)")
        print(f"    Content: {' | '.join(block['lines'])}")
        print(f"    Translatable: {segmenter.is_translatable_block(block)}")


def main():
    """Run full pipeline tests."""
    print("=== Full Segmentation, Context, and Reflow Pipeline Tests ===")
    
    # Test with repository sample files
    repo_root = Path(__file__).parent.parent
    sample_files = [
        repo_root / "README.md",
        repo_root / "pages" / "video_tutorial.md"
    ]
    
    results = []
    
    for file_path in sample_files:
        if file_path.exists():
            result = test_full_pipeline(str(file_path))
            results.append(result)
        else:
            print(f"Sample file not found: {file_path}")
    
    # Test code fence preservation
    test_code_fence_preservation()
    
    # Summary
    print(f"\n=== Test Summary ===")
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['line_count_match'])
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    for result in results:
        status = "✓" if result['line_count_match'] else "✗"
        print(f"{status} {os.path.basename(result['file_path'])}: {result['original_line_count']} -> {result['translated_line_count']} lines, {result['blocks_count']} blocks")
    
    # Check acceptance criteria: 2 samples with original line count = translated line count
    acceptance_met = passed_tests >= 2
    print(f"\nAcceptance Criteria: {'✅ MET' if acceptance_met else '❌ NOT MET'}")
    print("- Requirement: 2 samples with original line count = translated line count")
    print(f"- Result: {passed_tests} samples passed line count matching")
    
    return 0 if acceptance_met else 1


if __name__ == '__main__':
    sys.exit(main())