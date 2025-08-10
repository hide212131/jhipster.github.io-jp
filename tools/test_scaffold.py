#!/usr/bin/env python3
"""Simple test runner for tools scaffold."""

import sys
from pathlib import Path

def test_imports():
    """Test that all modules can be imported."""
    modules = [
        'config',
        'git_utils', 
        'file_filters',
        'placeholder',
        'segmenter',
        'reflow',
        'line_diff',
        'llm',
        'translate_blockwise',
        'discover_changes',
        'apply_changes',
        'pr_body',
        'verify_alignment',
        'run_sync'
    ]
    
    print("Testing module imports...")
    failed = []
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"✗ {module}: {e}")
            failed.append(module)
    
    return len(failed) == 0

def test_cli_help():
    """Test CLI help commands work."""
    import subprocess
    
    cli_scripts = [
        'run_sync.py',
        'discover_changes.py', 
        'apply_changes.py',
        'pr_body.py',
        'verify_alignment.py',
        'translate_blockwise.py'
    ]
    
    print("\nTesting CLI help commands...")
    failed = []
    
    for script in cli_scripts:
        try:
            result = subprocess.run([sys.executable, script, '--help'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'Usage:' in result.stdout:
                print(f"✓ {script} --help")
            else:
                print(f"✗ {script} --help: bad return code or output")
                failed.append(script)
        except Exception as e:
            print(f"✗ {script} --help: {e}")
            failed.append(script)
    
    return len(failed) == 0

def main():
    """Run all tests."""
    print("=== Tools Scaffold Tests ===\n")
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test CLI help
    if not test_cli_help():
        all_passed = False
    
    print(f"\n=== Test Results ===")
    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())