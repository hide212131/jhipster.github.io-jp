#!/usr/bin/env python3
"""Test run_sync.py filtering functionality."""

import json
import subprocess
import os
from pathlib import Path

def run_sync_command(args):
    """Run run_sync.py with given arguments and return results."""
    cmd = ["python", "run_sync.py"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
    return result

def test_dev_mode_basic():
    """Test basic dev mode functionality."""
    print("Testing basic dev mode...")
    result = run_sync_command(["--mode", "dev"])
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    print("✓ Basic dev mode works")

def test_dev_mode_with_limit():
    """Test dev mode with --limit parameter."""
    print("Testing dev mode with --limit...")
    result = run_sync_command(["--mode", "dev", "--limit", "1"])
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    # Check if results file was created
    results_file = Path("tools/.out/sync_results.json")
    assert results_file.exists(), "Results file not created"
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    assert results["mode"] == "dev", "Wrong mode in results"
    assert results["limit"] == 1, "Limit not recorded in results"
    print("✓ Dev mode with --limit works")

def test_dev_mode_with_before():
    """Test dev mode with --before parameter."""
    print("Testing dev mode with --before...")
    test_sha = "abc123"
    result = run_sync_command(["--mode", "dev", "--before", test_sha])
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    # Check if results file was created
    results_file = Path("tools/.out/sync_results.json")
    assert results_file.exists(), "Results file not created"
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    assert results["mode"] == "dev", "Wrong mode in results"
    assert results["before_sha"] == test_sha, "Before SHA not recorded in results"
    print("✓ Dev mode with --before works")

def test_dev_mode_with_paths():
    """Test dev mode with --paths parameter."""
    print("Testing dev mode with --paths...")
    result = run_sync_command(["--mode", "dev", "--paths", "docs/guide"])
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    results_file = Path("tools/.out/sync_results.json")
    assert results_file.exists(), "Results file not created"
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    assert results["mode"] == "dev", "Wrong mode in results"
    assert results["paths"] == "docs/guide", "Paths not recorded in results"
    print("✓ Dev mode with --paths works")

def test_dev_mode_combined_filters():
    """Test dev mode with combined filters."""
    print("Testing dev mode with combined filters...")
    result = run_sync_command([
        "--mode", "dev", 
        "--limit", "2", 
        "--before", "def456",
        "--paths", "docs/example"
    ])
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    results_file = Path("tools/.out/sync_results.json")
    assert results_file.exists(), "Results file not created"
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    assert results["mode"] == "dev", "Wrong mode in results"
    assert results["limit"] == 2, "Limit not recorded"
    assert results["before_sha"] == "def456", "Before SHA not recorded"
    assert results["paths"] == "docs/example", "Paths not recorded"
    print("✓ Dev mode with combined filters works")

def test_ci_mode_basic():
    """Test basic CI mode functionality."""
    print("Testing basic CI mode...")
    result = run_sync_command(["--mode", "ci"])
    # In CI mode without proper config, it should fail but still create results file
    assert result.returncode == 1, f"Expected exit code 1 for missing config, got {result.returncode}"
    
    results_file = Path("tools/.out/sync_results.json")
    assert results_file.exists(), "Results file not created"
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    assert results["mode"] == "ci", "Wrong mode in results"
    assert "error" in results, "Error not recorded in results"
    print("✓ Basic CI mode works (correctly fails with missing config)")

def main():
    """Run all tests."""
    print("=== Run Sync Filtering Tests ===\n")
    
    # Ensure we're in the tools directory
    os.chdir(Path(__file__).parent)
    
    # Create output directory if it doesn't exist
    Path("tools/.out").mkdir(parents=True, exist_ok=True)
    
    tests = [
        test_dev_mode_basic,
        test_dev_mode_with_limit,
        test_dev_mode_with_before,
        test_dev_mode_with_paths,
        test_dev_mode_combined_filters,
        test_ci_mode_basic,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        print()
    
    print("=== Test Results ===")
    print(f"✅ Passed: {passed}")
    if failed > 0:
        print(f"❌ Failed: {failed}")
        return 1
    else:
        print("🎉 All tests passed!")
        return 0

if __name__ == "__main__":
    exit(main())