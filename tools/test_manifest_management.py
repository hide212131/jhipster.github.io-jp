#!/usr/bin/env python3
"""Test manifest management functionality."""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, os.path.dirname(__file__))

from manifest_manager import ManifestManager
from git_utils import GitUtils
from discover_changes import ChangeDiscoverer
from apply_changes import ChangeApplicator


class MockGitUtils(GitUtils):
    """Mock GitUtils for testing."""
    
    def __init__(self):
        super().__init__()
        self.files = {}
        self.branches = set()
        self.current_branch = "main"
        self.shas = {
            "main": "main123",
            "upstream/main": "upstream456", 
            "translation-meta": "meta789"
        }
    
    def get_file_content(self, file_path: str, ref: str = "HEAD") -> str:
        # Map refs to actual content keys
        if ref == "HEAD":
            ref = "main"
        elif ref == "upstream/main":
            ref = "upstream456"
        key = f"{ref}:{file_path}"
        return self.files.get(key)
    
    def branch_exists(self, branch_name: str) -> bool:
        return branch_name in self.branches
    
    def create_orphan_branch(self, branch_name: str) -> bool:
        self.branches.add(branch_name)
        return True
    
    def write_file_to_branch(self, file_path: str, content: str, branch_name: str, commit_message: str) -> bool:
        key = f"{branch_name}:{file_path}"
        self.files[key] = content
        return True
    
    def get_current_sha(self, ref: str = "HEAD") -> str:
        if ref == "upstream/main":
            return "upstream456"
        return self.shas.get(ref, "default123")
    
    def get_current_branch(self) -> str:
        return self.current_branch


def test_manifest_manager():
    """Test manifest manager basic functionality."""
    print("=== Testing Manifest Manager ===")
    
    # Setup mock git utils
    mock_git = MockGitUtils()
    manifest_manager = ManifestManager(mock_git)
    
    # Test reading empty manifest
    print("Testing empty manifest read...")
    manifest = manifest_manager.read_manifest()
    assert "version" in manifest
    assert "files" in manifest
    print("✓ Empty manifest read successfully")
    
    # Test updating file entry
    print("Testing file entry update...")
    success = manifest_manager.update_file_entry(
        "docs/test.md",
        "upstream456",
        "translated",
        {"lines": 10}
    )
    assert success
    print("✓ File entry updated successfully")
    
    # Test reading updated manifest
    print("Testing manifest with file entry...")
    manifest = manifest_manager.read_manifest()
    assert "docs/test.md" in manifest["files"]
    file_entry = manifest["files"]["docs/test.md"]
    assert file_entry["upstream_sha"] == "upstream456"
    assert file_entry["strategy"] == "translated"
    assert file_entry["lines"] == 10
    print("✓ File entry read successfully")
    
    # Test getting file upstream SHA
    print("Testing file upstream SHA retrieval...")
    sha = manifest_manager.get_file_upstream_sha("docs/test.md")
    assert sha == "upstream456"
    print("✓ File upstream SHA retrieved successfully")
    
    # Test getting file strategy
    print("Testing file strategy retrieval...")
    strategy = manifest_manager.get_file_strategy("docs/test.md")
    assert strategy == "translated"
    print("✓ File strategy retrieved successfully")
    
    # Test getting manifest summary
    print("Testing manifest summary...")
    summary = manifest_manager.get_manifest_summary()
    assert summary["total_files"] == 1
    assert summary["strategies"]["translated"] == 1
    print("✓ Manifest summary generated successfully")
    
    print("✅ All manifest manager tests passed!")


def test_discover_changes_with_manifest():
    """Test discover changes using manifest for comparison."""
    print("\n=== Testing Discover Changes with Manifest ===")
    
    # Setup mock git utils with some content
    mock_git = MockGitUtils()
    
    # Add some upstream content
    mock_git.files["upstream/main:docs/test.md"] = "# Test\nNew content\nMore lines"
    
    # Add some manifest content for comparison
    mock_git.files["translation-meta:manifest.json"] = json.dumps({
        "version": "1.0",
        "files": {
            "docs/test.md": {
                "upstream_sha": "old456",
                "strategy": "translated",
                "last_translated": "2024-01-01T00:00:00"
            }
        }
    })
    
    # Add old upstream content at the manifest SHA
    mock_git.files["old456:docs/test.md"] = "# Test\nOld content"
    
    # Setup discoverer
    discoverer = ChangeDiscoverer()
    discoverer.git_utils = mock_git
    discoverer.manifest_manager = ManifestManager(mock_git)
    
    # Mock the file discovery (normally done by git utils)
    def mock_get_upstream_changes(since_sha=None):
        return ["docs/test.md"]
    
    mock_git.get_upstream_changes = mock_get_upstream_changes
    
    # Discover changes
    print("Testing change discovery with manifest...")
    changes = discoverer.discover_changes()
    
    # Verify results contain manifest information
    translate_files = changes["files"].get("translate", [])
    assert len(translate_files) > 0
    
    test_file = None
    for file_info in translate_files:
        if file_info["path"] == "docs/test.md":
            test_file = file_info
            break
    
    assert test_file is not None
    assert "manifest_sha" in test_file
    assert "current_upstream_sha" in test_file
    assert "needs_update" in test_file
    assert test_file["manifest_sha"] == "old456"
    assert test_file["needs_update"] is True
    
    print("✓ Change discovery with manifest working correctly")
    print("✅ All discover changes tests passed!")


def test_apply_changes_updates_manifest():
    """Test that apply changes updates the manifest."""
    print("\n=== Testing Apply Changes Updates Manifest ===")
    
    # Setup mock git utils
    mock_git = MockGitUtils()
    
    # Add upstream content
    mock_git.files["upstream/main:docs/test.md"] = "# Test\nUpstream content"
    
    # Create a changes file structure
    changes_data = {
        "files": {
            "translate": [{
                "path": "docs/test.md",
                "status": "modified",
                "operations": [{
                    "operation": "replace",
                    "strategy": "retranslate"
                }],
                "current_upstream_sha": "upstream456",
                "manifest_sha": "old123"
            }]
        }
    }
    
    # Create temporary changes file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(changes_data, f)
        changes_file = f.name
    
    try:
        # Setup applicator with mock
        applicator = ChangeApplicator()
        applicator.git_utils = mock_git
        
        # Use a shared manifest manager that has some initial data
        shared_manifest_manager = ManifestManager(mock_git)
        applicator.manifest_manager = shared_manifest_manager
        
        # Pre-populate manifest with initial data for testing
        shared_manifest_manager.update_file_entry(
            "docs/test.md", 
            "old123", 
            "translated"
        )
        
        # Mock the translation to avoid actual LLM calls
        def mock_translate_file_content(content, context=None):
            return "# テスト\n翻訳されたコンテンツ"
        
        applicator.translator.translate_file_content = mock_translate_file_content
        
        # Apply changes
        print("Testing apply changes with manifest update...")
        results = applicator.apply_changes(changes_file)
        
        # Verify manifest was updated
        manifest = applicator.manifest_manager.read_manifest()
        print(f"DEBUG: manifest files: {list(manifest['files'].keys())}")
        assert "docs/test.md" in manifest["files"]
        
        file_entry = manifest["files"]["docs/test.md"]
        print(f"DEBUG: file_entry upstream_sha: {file_entry['upstream_sha']}")
        assert file_entry["upstream_sha"] == "upstream456"
        
        print("✓ Manifest updated after applying changes")
        print("✅ All apply changes tests passed!")
        
    finally:
        # Cleanup
        os.unlink(changes_file)


def test_integration():
    """Test integration of manifest management across components."""
    print("\n=== Testing Integration ===")
    
    # Setup mock git utils
    mock_git = MockGitUtils()
    
    # Add initial upstream content
    mock_git.files["upstream/main:docs/integration.md"] = "# Integration\nOriginal content"
    
    # Setup components
    manifest_manager = ManifestManager(mock_git)
    
    # Step 1: Initialize manifest with file
    print("Step 1: Initialize manifest...")
    success = manifest_manager.update_file_entry(
        "docs/integration.md",
        "upstream123",
        "translated"
    )
    assert success
    print("✓ Manifest initialized")
    
    # Step 2: Update upstream content
    mock_git.files["upstream/main:docs/integration.md"] = "# Integration\nUpdated content\nNew line"
    mock_git.files["upstream123:docs/integration.md"] = "# Integration\nOriginal content"
    
    # Step 3: Discover changes using manifest
    print("Step 2: Discover changes...")
    discoverer = ChangeDiscoverer()
    discoverer.git_utils = mock_git
    discoverer.manifest_manager = manifest_manager
    
    def mock_get_upstream_changes(since_sha=None):
        return ["docs/integration.md"]
    
    mock_git.get_upstream_changes = mock_get_upstream_changes
    mock_git.shas["upstream/main"] = "upstream456"
    
    changes = discoverer.discover_changes()
    
    # Verify changes detected
    translate_files = changes["files"].get("translate", [])
    integration_file = next((f for f in translate_files if f["path"] == "docs/integration.md"), None)
    assert integration_file is not None
    assert integration_file["needs_update"] is True
    assert integration_file["manifest_sha"] == "upstream123"
    assert integration_file["current_upstream_sha"] == "upstream456"
    
    print("✓ Changes discovered using manifest")
    
    # Step 4: Verify manifest tracks the update state correctly
    print("Step 3: Verify manifest state...")
    
    # Get current manifest state
    current_sha = manifest_manager.get_file_upstream_sha("docs/integration.md")
    assert current_sha == "upstream123"  # Should still be old SHA until update
    
    # Update manifest with new SHA
    manifest_manager.update_file_entry(
        "docs/integration.md",
        "upstream456",
        "retranslated"
    )
    
    # Verify update
    updated_sha = manifest_manager.get_file_upstream_sha("docs/integration.md")
    assert updated_sha == "upstream456"
    
    updated_strategy = manifest_manager.get_file_strategy("docs/integration.md")
    assert updated_strategy == "retranslated"
    
    print("✓ Manifest state updated correctly")
    print("✅ All integration tests passed!")


def main():
    """Run all tests."""
    print("Running Manifest Management Tests")
    print("=" * 50)
    
    try:
        test_manifest_manager()
        test_discover_changes_with_manifest()
        test_apply_changes_updates_manifest()
        test_integration()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("Manifest management functionality is working correctly.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()