#!/usr/bin/env python3
"""Test CLI integration with manifest management."""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, os.path.dirname(__file__))


def test_discover_changes_cli():
    """Test discover_changes CLI with manifest options."""
    print("=== Testing discover_changes CLI ===")
    
    # Test help output includes manifest options
    print("Testing CLI help...")
    result = subprocess.run(
        [sys.executable, "discover_changes.py", "--help"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__)
    )
    
    assert result.returncode == 0
    assert "--meta-branch" in result.stdout
    print("✓ CLI help shows manifest options")
    
    # Test default execution (will use stub/mock data)
    print("Testing CLI execution...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_file = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, "discover_changes.py", "-o", output_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        assert result.returncode == 0
        
        # Verify output file contains expected structure
        with open(output_file, 'r') as f:
            changes = json.load(f)
        
        assert "meta_branch" in changes
        assert changes["meta_branch"] == "translation-meta"
        assert "files" in changes
        
        print("✓ CLI execution produces correct output with manifest info")
        
    finally:
        os.unlink(output_file)


def test_apply_changes_cli():
    """Test apply_changes CLI functionality."""
    print("\n=== Testing apply_changes CLI ===")
    
    # Test help output
    print("Testing CLI help...")
    result = subprocess.run(
        [sys.executable, "apply_changes.py", "--help"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__)
    )
    
    assert result.returncode == 0
    print("✓ CLI help works")
    
    # Create a simple changes file for testing
    changes_data = {
        "files": {
            "translate": [{
                "path": "docs/test.md",
                "status": "modified",
                "operations": [],
                "current_upstream_sha": "upstream456"
            }],
            "copy_only": []
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(changes_data, f)
        changes_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_file = f.name
    
    try:
        # Test CLI execution
        print("Testing CLI execution...")
        result = subprocess.run(
            [sys.executable, "apply_changes.py", "-c", changes_file, "-o", output_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        assert result.returncode == 0
        print("✓ CLI execution works")
        
    finally:
        os.unlink(changes_file)
        os.unlink(output_file)


def test_end_to_end_workflow():
    """Test end-to-end workflow with manifest management."""
    print("\n=== Testing End-to-End Workflow ===")
    
    # Step 1: Discover changes
    print("Step 1: Discover changes...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        changes_file = f.name
    
    result = subprocess.run(
        [sys.executable, "discover_changes.py", "-o", changes_file],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__)
    )
    
    assert result.returncode == 0
    
    # Verify changes file
    with open(changes_file, 'r') as f:
        changes = json.load(f)
    
    assert "meta_branch" in changes
    print("✓ Changes discovered successfully")
    
    # Step 2: Apply changes
    print("Step 2: Apply changes...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        results_file = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, "apply_changes.py", "-c", changes_file, "-o", results_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        assert result.returncode == 0
        
        # Verify results file
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        assert "processed_files" in results
        assert "statistics" in results
        
        print("✓ Changes applied successfully")
        print("✓ End-to-end workflow completed")
        
    finally:
        os.unlink(changes_file)
        os.unlink(results_file)


def main():
    """Run CLI integration tests."""
    print("Running CLI Integration Tests")
    print("=" * 50)
    
    try:
        test_discover_changes_cli()
        test_apply_changes_cli() 
        test_end_to_end_workflow()
        
        print("\n" + "=" * 50)
        print("🎉 ALL CLI TESTS PASSED!")
        print("CLI integration with manifest management is working correctly.")
        
    except Exception as e:
        print(f"\n❌ CLI TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()