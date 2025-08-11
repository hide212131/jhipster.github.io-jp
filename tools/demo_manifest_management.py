#!/usr/bin/env python3
"""Demonstration of manifest management functionality."""

import os
import sys
import json
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, os.path.dirname(__file__))

from manifest_manager import ManifestManager
from git_utils import GitUtils


def demo_manifest_management():
    """Demonstrate manifest management functionality."""
    print("=" * 60)
    print("MANIFEST MANAGEMENT DEMONSTRATION")
    print("=" * 60)
    
    # Initialize manifest manager (uses stub git utils)
    git_utils = GitUtils()
    manifest_manager = ManifestManager(git_utils)
    
    print("\n1. Reading initial (empty) manifest:")
    manifest = manifest_manager.read_manifest()
    print(f"   Version: {manifest['version']}")
    print(f"   Files tracked: {len(manifest['files'])}")
    
    print("\n2. Adding file entries to manifest:")
    
    # Add some example file entries
    files_to_add = [
        ("docs/getting-started.md", "abc123", "translated"),
        ("docs/tutorials/basic.md", "def456", "translated"),
        ("docs/guides/advanced.md", "ghi789", "copy_only")
    ]
    
    for file_path, sha, strategy in files_to_add:
        success = manifest_manager.update_file_entry(
            file_path, sha, strategy, {"lines": 20, "test": True}
        )
        print(f"   ✓ Added {file_path} (SHA: {sha}, Strategy: {strategy})")
    
    print("\n3. Reading updated manifest:")
    manifest = manifest_manager.read_manifest()
    print(f"   Files tracked: {len(manifest['files'])}")
    
    for file_path, file_data in manifest['files'].items():
        print(f"   - {file_path}:")
        print(f"     SHA: {file_data['upstream_sha']}")
        print(f"     Strategy: {file_data['strategy']}")
        print(f"     Last translated: {file_data['last_translated'][:19]}")
    
    print("\n4. Retrieving specific file information:")
    test_file = "docs/getting-started.md"
    sha = manifest_manager.get_file_upstream_sha(test_file)
    strategy = manifest_manager.get_file_strategy(test_file)
    print(f"   {test_file}:")
    print(f"   - Upstream SHA: {sha}")
    print(f"   - Strategy: {strategy}")
    
    print("\n5. Getting manifest summary:")
    summary = manifest_manager.get_manifest_summary()
    print(f"   Total files: {summary['total_files']}")
    print(f"   Strategies: {summary['strategies']}")
    print(f"   Last updated: {summary['last_updated'][:19]}")
    
    print("\n6. Updating existing file entry:")
    manifest_manager.update_file_entry(
        "docs/getting-started.md", 
        "xyz999", 
        "retranslated",
        {"lines": 25, "updated": True}
    )
    
    updated_sha = manifest_manager.get_file_upstream_sha("docs/getting-started.md")
    updated_strategy = manifest_manager.get_file_strategy("docs/getting-started.md")
    print(f"   Updated {test_file}:")
    print(f"   - New SHA: {updated_sha}")
    print(f"   - New strategy: {updated_strategy}")
    
    print("\n7. Listing all tracked files:")
    tracked_files = manifest_manager.list_tracked_files()
    print(f"   Tracked files ({len(tracked_files)}):")
    for file_path in tracked_files:
        print(f"   - {file_path}")
    
    print("\n8. Removing a file entry:")
    manifest_manager.remove_file_entry("docs/guides/advanced.md")
    remaining_files = manifest_manager.list_tracked_files()
    print(f"   Remaining files after removal: {len(remaining_files)}")
    
    print("\n" + "=" * 60)
    print("MANIFEST MANAGEMENT DEMO COMPLETE")
    print("=" * 60)
    print("\nKey features demonstrated:")
    print("✓ Create and manage manifest.json in translation-meta branch")
    print("✓ Track file paths, upstream SHAs, and translation strategies")
    print("✓ Update manifest entries with new metadata")
    print("✓ Retrieve specific file information for comparison")
    print("✓ Generate summary statistics")
    print("✓ List and manage tracked files")
    print("\nThis manifest provides the foundation for:")
    print("• Difference detection based on upstream SHA changes")
    print("• Strategy tracking for translation decisions")
    print("• Input/output coordination across pipeline runs")


if __name__ == "__main__":
    demo_manifest_management()