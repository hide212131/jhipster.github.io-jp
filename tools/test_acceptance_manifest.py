#!/usr/bin/env python3
"""Acceptance test for manifest management requirements."""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, os.path.dirname(__file__))

from manifest_manager import ManifestManager
from git_utils import GitUtils
from discover_changes import ChangeDiscoverer
from apply_changes import ChangeApplicator


class AcceptanceTestGitUtils(GitUtils):
    """Git utils for acceptance testing with realistic scenario."""
    
    def __init__(self):
        super().__init__()
        self.files = {}
        self.branches = {"main", "translation-meta"}
        self.current_branch = "main"
        self.commit_count = 0
        
        # Set up realistic scenario
        self._setup_scenario()
    
    def _setup_scenario(self):
        """Set up a realistic testing scenario."""
        # Initial upstream file
        self.files["upstream456:docs/getting-started.md"] = """# Getting Started

Welcome to JHipster! This guide will help you get started.

## Prerequisites

You need Java 11+ and Node.js 16+.

## Installation

```bash
npm install -g generator-jhipster
```

## Create Project

Run the generator:

```bash
jhipster
```
"""
        
        # Updated upstream file (new version)
        self.files["upstream789:docs/getting-started.md"] = """# Getting Started

Welcome to JHipster! This guide will help you get started quickly.

## Prerequisites

You need Java 17+ and Node.js 18+.

## Installation

Install JHipster globally:

```bash
npm install -g generator-jhipster
```

## Create Project

Run the generator:

```bash
jhipster
```

## Next Steps

Continue with the tutorials.
"""
        
        # Existing Japanese translation (based on old upstream)
        self.files["main:docs/getting-started.md"] = """# はじめに

JHipsterへようこそ！このガイドは始め方を説明します。

## 前提条件

Java 11+とNode.js 16+が必要です。

## インストール

```bash
npm install -g generator-jhipster
```

## プロジェクト作成

ジェネレータを実行：

```bash
jhipster
```
"""
        
        # Manifest shows this was translated from upstream456
        self.files["translation-meta:manifest.json"] = json.dumps({
            "version": "1.0",
            "created": "2024-01-01T00:00:00",
            "last_updated": "2024-01-01T00:00:00",
            "upstream_repo": "jhipster/jhipster.github.io",
            "meta_branch": "translation-meta",
            "files": {
                "docs/getting-started.md": {
                    "upstream_sha": "upstream456",
                    "strategy": "translated",
                    "last_translated": "2024-01-01T00:00:00",
                    "lines": 16
                }
            }
        }, indent=2)
    
    def get_file_content(self, file_path: str, ref: str = "HEAD") -> str:
        # Map HEAD to main for testing
        if ref == "HEAD":
            ref = "main"
        # Map upstream/main to the current upstream SHA
        elif ref == "upstream/main":
            ref = "upstream789"
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
        self.commit_count += 1
        return True
    
    def get_current_sha(self, ref: str = "HEAD") -> str:
        if ref == "upstream/main":
            return "upstream789"  # New upstream version
        elif ref == "main":
            return "main123"
        return "default123"
    
    def get_current_branch(self) -> str:
        return self.current_branch
    
    def get_upstream_changes(self, since_sha=None):
        return ["docs/getting-started.md"]


def test_acceptance_criteria():
    """Test that acceptance criteria are met."""
    print("=" * 60)
    print("ACCEPTANCE TEST: Translation Meta Management")
    print("=" * 60)
    
    # Set up test environment
    git_utils = AcceptanceTestGitUtils()
    manifest_manager = ManifestManager(git_utils)
    discoverer = ChangeDiscoverer()
    applicator = ChangeApplicator()
    
    # Wire up components
    discoverer.git_utils = git_utils
    discoverer.manifest_manager = manifest_manager
    applicator.git_utils = git_utils
    applicator.manifest_manager = manifest_manager
    
    print("\nScenario: File has been translated from upstream456, upstream is now at upstream789")
    print("Expected: System should detect difference and know what to retranslate")
    
    # ACCEPTANCE CRITERION 1: Difference detection correctly references manifest
    print("\n1. Testing difference detection references manifest...")
    
    changes = discoverer.discover_changes(upstream_ref="upstream/main")
    
    # Verify manifest information is correctly referenced
    translate_files = changes["files"].get("translate", [])
    assert len(translate_files) > 0, "Should detect files needing translation"
    
    getting_started_file = None
    for file_info in translate_files:
        if file_info["path"] == "docs/getting-started.md":
            getting_started_file = file_info
            break
    
    assert getting_started_file is not None, "getting-started.md should be found"
    
    # Verify manifest data is present and correct
    assert getting_started_file["manifest_sha"] == "upstream456", \
        f"Manifest SHA should be upstream456, got {getting_started_file['manifest_sha']}"
    
    assert getting_started_file["current_upstream_sha"] == "upstream789", \
        f"Current upstream SHA should be upstream789, got {getting_started_file['current_upstream_sha']}"
    
    assert getting_started_file["needs_update"] is True, \
        "File should need update since upstream SHA changed"
    
    assert getting_started_file["previous_strategy"] == "translated", \
        "Previous strategy should be loaded from manifest"
    
    # Check that differences are calculated against the manifest baseline
    assert len(getting_started_file["operations"]) > 0, \
        "Should detect operations between upstream456 and upstream789"
    
    print("✓ Difference detection correctly references manifest")
    print("  - Loaded baseline SHA from manifest: upstream456")
    print("  - Detected current upstream SHA: upstream789")
    print("  - Correctly identified file needs update")
    print("  - Found operations between baseline and current upstream")
    
    # ACCEPTANCE CRITERION 2: Application correctly updates manifest
    print("\n2. Testing application updates manifest...")
    
    # Mock translator to avoid actual LLM calls
    def mock_translate_file_content(content, context=None):
        # Simulate updated translation
        return """# はじめに

JHipsterへようこそ！このガイドは素早く始める方法を説明します。

## 前提条件

Java 17+とNode.js 18+が必要です。

## インストール

JHipsterをグローバルにインストール：

```bash
npm install -g generator-jhipster
```

## プロジェクト作成

ジェネレータを実行：

```bash
jhipster
```

## 次のステップ

チュートリアルを続けてください。
"""
    
    applicator.translator.translate_file_content = mock_translate_file_content
    
    # Create changes file for application
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(changes, f)
        changes_file = f.name
    
    try:
        # Apply changes
        results = applicator.apply_changes(changes_file)
        
        # Verify application succeeded
        assert len(results["errors"]) == 0, f"Application should succeed, got errors: {results['errors']}"
        processed_count = results["statistics"]["translated"] + results["statistics"]["kept_existing"]
        assert processed_count > 0, "Should have processed at least one file"
        
        print("✓ Changes applied successfully (translated or kept with LLM check)")
        
        # Verify manifest was updated
        updated_manifest = manifest_manager.read_manifest()
        
        file_entry = updated_manifest["files"]["docs/getting-started.md"]
        assert file_entry["upstream_sha"] == "upstream789", \
            f"Manifest should be updated to upstream789, got {file_entry['upstream_sha']}"
        
        assert file_entry["strategy"] in ["translated", "retranslated", "kept_existing_llm"], \
            f"Strategy should indicate processing, got {file_entry['strategy']}"
        
        print("✓ Manifest correctly updated after application")
        print(f"  - Updated upstream SHA to: {file_entry['upstream_sha']}")
        print(f"  - Updated strategy to: {file_entry['strategy']}")
        print(f"  - Updated timestamp: {file_entry['last_translated']}")
        
    finally:
        os.unlink(changes_file)
    
    # ACCEPTANCE CRITERION 3: Input/output coordination works correctly
    print("\n3. Testing input/output coordination...")
    
    # Run discovery again - should now show no changes needed
    changes_after = discoverer.discover_changes(upstream_ref="upstream/main")
    
    translate_files_after = changes_after["files"].get("translate", [])
    getting_started_after = None
    for file_info in translate_files_after:
        if file_info["path"] == "docs/getting-started.md":
            getting_started_after = file_info
            break
    
    if getting_started_after:
        assert getting_started_after["needs_update"] is False, \
            "File should not need update after manifest was updated"
        assert getting_started_after["manifest_sha"] == "upstream789", \
            "Manifest should now show current upstream SHA"
    
    print("✓ Input/output coordination works correctly")
    print("  - Second discovery shows file is up to date")
    print("  - Manifest properly reflects current state")
    
    # ACCEPTANCE CRITERION 4: Translation-meta branch management
    print("\n4. Testing translation-meta branch management...")
    
    # Verify meta branch exists and contains manifest
    assert git_utils.branch_exists("translation-meta"), "translation-meta branch should exist"
    
    manifest_content = git_utils.get_file_content("manifest.json", "translation-meta")
    assert manifest_content is not None, "manifest.json should exist in translation-meta branch"
    
    manifest_data = json.loads(manifest_content)
    assert manifest_data["version"] == "1.0", "Manifest should have correct version"
    assert "docs/getting-started.md" in manifest_data["files"], "Manifest should track the test file"
    
    print("✓ Translation-meta branch properly managed")
    print("  - Branch exists and is accessible")
    print("  - Contains valid manifest.json")
    print("  - Manifest tracks file states correctly")
    
    print("\n" + "=" * 60)
    print("🎉 ALL ACCEPTANCE CRITERIA PASSED!")
    print("=" * 60)
    print("\nSummary of verified functionality:")
    print("✓ Difference detection correctly references manifest for baseline comparison")
    print("✓ Application process correctly updates manifest with new upstream SHAs")  
    print("✓ Input/output coordination ensures manifest state reflects processing results")
    print("✓ Translation-meta branch properly manages manifest.json")
    print("\nThe implementation meets all specified requirements.")


def main():
    """Run acceptance test."""
    try:
        test_acceptance_criteria()
    except Exception as e:
        print(f"\n❌ ACCEPTANCE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()