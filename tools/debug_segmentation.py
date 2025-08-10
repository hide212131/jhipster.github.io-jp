#!/usr/bin/env python3
"""Debug script to examine code fence segmentation."""

from segmenter import TextSegmenter

def debug_code_fence():
    """Debug code fence segmentation."""
    sample_text = """---
layout: default
title: チーム
---

# チーム

JHipsterは世界中の人々のチームによって開発されています。

## インストール

```bash
npm install
```

このコマンドでインストールできます。"""
    
    segmenter = TextSegmenter()
    blocks = segmenter.segment_into_blocks(sample_text)
    
    print("=== Code Fence Debug ===")
    print("Original text:")
    print(repr(sample_text))
    print("\nSegmented blocks:")
    
    for i, block in enumerate(blocks):
        translatable = segmenter.is_translatable_block(block)
        print(f"Block {i}: {block['type']} ({block['line_count']} lines) - Translatable: {translatable}")
        for j, line in enumerate(block['lines']):
            print(f"  {j}: {repr(line)}")
        print()

if __name__ == '__main__':
    debug_code_fence()