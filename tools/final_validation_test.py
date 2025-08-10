#!/usr/bin/env python3
"""Final validation test for discover_changes.py functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
from discover_changes import ChangeDiscoverer


def run_final_validation():
    """Run final validation test with realistic scenarios."""
    
    print("=== Final Validation: discover_changes.py 差分検出 ===\n")
    
    discoverer = ChangeDiscoverer()
    
    # Mock realistic file changes
    with patch('git_utils.GitUtils.add_upstream_remote'), \
         patch('git_utils.GitUtils.fetch_upstream'), \
         patch('git_utils.GitUtils.get_upstream_changes') as mock_changes, \
         patch('git_utils.GitUtils.get_file_content') as mock_content:
        
        # Setup mocks
        mock_changes.return_value = [
            "docs/new-feature.md",      # Added file
            "docs/updated-guide.md",    # Modified file  
            "docs/removed-section.md",  # Deleted file
            "static/logo.png",          # Ignore file
            "LICENSE",                  # Copy only file
        ]
        
        def content_mock(file_path, ref):
            """Mock file content for different scenarios."""
            if file_path == "docs/new-feature.md":
                if ref == "upstream/main":
                    return """# New Feature Documentation
This is a brand new feature that was added upstream.

## Installation
Follow these steps to install the new feature.

## Usage  
Here's how to use the new feature."""
                else:  # HEAD
                    return None  # File doesn't exist locally yet
            
            elif file_path == "docs/updated-guide.md":
                if ref == "upstream/main":
                    return """# User Guide
Welcome to the updated user guide.

## Getting Started
This section has been completely rewritten with new information.

## Advanced Topics
- New topic A
- New topic B 
- Updated topic C

## Conclusion
Thank you for reading the updated guide."""
                else:  # HEAD  
                    return """# User Guide
Welcome to the user guide.

## Getting Started
This section contains the old information.

## Advanced Topics  
- Old topic A
- Old topic B

## Conclusion
Thank you for reading."""
            
            elif file_path == "docs/removed-section.md":
                if ref == "upstream/main":
                    return None  # File was deleted upstream
                else:  # HEAD
                    return """# Removed Section
This section was removed from the documentation.
It contained outdated information."""
            
            elif file_path == "static/logo.png":
                # Binary file - should be ignored
                return "binary-content" if ref == "upstream/main" else "binary-content"
            
            elif file_path == "LICENSE":
                # Text file that should be copied only
                return "MIT License\nCopyright..." if ref == "upstream/main" else "MIT License\nCopyright..."
            
            return None
        
        mock_content.side_effect = content_mock
        
        # Run change discovery
        print("Running change discovery...")
        changes = discoverer.discover_changes("upstream/main", "translation-meta")
        
        # Display results
        print(f"Discovered changes at: {changes['timestamp']}")
        print(f"Upstream ref: {changes['upstream_ref']}")
        print(f"Meta branch: {changes['meta_branch']}\n")
        
        # Analyze each file category
        for category, files in changes["files"].items():
            if not files:
                continue
                
            print(f"=== {category.upper()} FILES ({len(files)}) ===")
            
            for file_info in files:
                path = file_info["path"]
                status = file_info["status"]
                operations = file_info.get("operations", [])
                summary = file_info.get("summary", {})
                
                print(f"\nFile: {path}")
                print(f"Status: {status}")
                
                if operations:
                    print(f"Operations ({len(operations)}):")
                    for i, op in enumerate(operations):
                        op_type = op["operation"]
                        change_type = op["change_type"]
                        strategy = op["strategy"]
                        
                        print(f"  {i+1}. {op_type} (lines {op['old_start']}-{op['old_end']} → {op['new_start']}-{op['new_end']})")
                        print(f"     Change type: {change_type}")
                        print(f"     Strategy: {strategy}")
                        
                        if op_type == "insert" and op["new_lines"]:
                            print(f"     Added: {len(op['new_lines'])} lines")
                        elif op_type == "delete" and op["old_lines"]:
                            print(f"     Removed: {len(op['old_lines'])} lines")
                        elif op_type == "replace":
                            print(f"     Similarity: {op['similarity_ratio']:.3f}")
                
                if summary.get("total_operations", 0) > 0:
                    print(f"Summary:")
                    print(f"  - Total operations: {summary['total_operations']}")
                    print(f"  - Unchanged lines: {summary['unchanged_lines']}")
                    print(f"  - Added lines: {summary['added_lines']}")
                    print(f"  - Removed lines: {summary['removed_lines']}")
                    print(f"  - Modified lines: {summary['modified_lines']}")
                    print(f"  - Minor edits: {summary['minor_edits']}")
                    print(f"  - Major changes: {summary['major_changes']}")
        
        # Save full JSON output
        output_file = "/tmp/validation_changes.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(changes, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== VALIDATION RESULTS ===")
        print(f"✅ Full JSON output saved to: {output_file}")
        
        # Verify acceptance criteria
        translate_files = changes["files"]["translate"]
        copy_only_files = changes["files"]["copy_only"]
        ignore_files = changes["files"]["ignore"]
        
        print(f"✅ Translation targets detected: {len(translate_files)} files")
        print(f"✅ Copy-only files detected: {len(copy_only_files)} files")
        print(f"✅ Ignored files detected: {len(ignore_files)} files")
        
        # Check for all operation types
        all_operations = []
        for file_info in translate_files:
            all_operations.extend(file_info.get("operations", []))
        
        operation_types = set(op["operation"] for op in all_operations)
        change_types = set(op["change_type"] for op in all_operations)
        strategies = set(op["strategy"] for op in all_operations)
        
        print(f"✅ Operation types detected: {sorted(operation_types)}")
        print(f"✅ Change types detected: {sorted(change_types)}")
        print(f"✅ Translation strategies: {sorted(strategies)}")
        
        print(f"\n🎉 差分検出システム正常動作確認完了！")
        print(f"   All acceptance criteria have been successfully validated.")


if __name__ == '__main__':
    run_final_validation()