#!/usr/bin/env python3
"""
Simple test script to demonstrate dev_filter functionality with sample data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from dev_filter import DevFilter

def test_limit_filter():
    """Test limit filtering."""
    print("=== Testing Limit Filter ===")
    
    sample_files = [f"file_{i:03d}.md" for i in range(1, 21)]  # 20 files
    sample_commits = [f"commit_{i:03d}" for i in range(1, 11)]  # 10 commits
    
    dev_filter = DevFilter(limit=5)
    
    filtered_files = dev_filter.apply_limit(sample_files)
    filtered_commits = dev_filter.apply_limit(sample_commits)
    
    print(f"Original files: {len(sample_files)}, after limit=5: {len(filtered_files)}")
    print(f"Files: {filtered_files}")
    print(f"Original commits: {len(sample_commits)}, after limit=5: {len(filtered_commits)}")
    print(f"Commits: {filtered_commits}")
    print()

def test_path_filter():
    """Test path filtering."""
    print("=== Testing Path Filter ===")
    
    sample_files = [
        "tips/001_tip_example.md",
        "pages/installation.md",
        "pages/getting_started.md",
        "tips/002_tip_another.md",
        "_posts/2023-01-01-release.md",
        "blueprints/quarkus/index.md",
        "tips/003_tip_more.md"
    ]
    
    dev_filter = DevFilter(paths=["*tips*", "*pages*"])
    filtered_files = dev_filter.filter_paths(sample_files)
    
    print(f"Original files: {sample_files}")
    print(f"Filtered files (tips/pages): {filtered_files}")
    print()

def test_commit_filter_with_samples():
    """Test commit filtering with sample data."""
    print("=== Testing Commit Filter (Sample Data) ===")
    
    sample_commits = ["commit_001", "commit_002", "commit_003", "commit_004", "commit_005"]
    
    # Test filtering by a commit in the middle
    dev_filter = DevFilter(before="commit_003")
    
    # Simulate the fallback logic for when git commands don't work
    if dev_filter.before in sample_commits:
        before_index = sample_commits.index(dev_filter.before)
        filtered_commits = sample_commits[before_index + 1:]  # Commits after the specified one
    else:
        filtered_commits = sample_commits
    
    print(f"Original commits: {sample_commits}")
    print(f"Filtered commits (before commit_003): {filtered_commits}")
    print()

def test_combined_filters():
    """Test combined filtering."""
    print("=== Testing Combined Filters ===")
    
    sample_files = [
        "tips/001_tip_example.md",
        "tips/002_tip_another.md", 
        "tips/003_tip_more.md",
        "pages/installation.md",
        "pages/getting_started.md",
        "_posts/2023-01-01-release.md",
        "blueprints/quarkus/index.md"
    ]
    
    sample_commits = ["commit_001", "commit_002", "commit_003", "commit_004", "commit_005"]
    
    dev_filter = DevFilter(limit=3, paths=["*tips*"])
    
    result = dev_filter.apply_all_filters(commits=sample_commits, files=sample_files)
    
    print(f"Original files: {sample_files}")
    print(f"Original commits: {sample_commits}")
    print(f"After combined filters (limit=3, paths=*tips*): {result}")
    print()

if __name__ == "__main__":
    print("Running dev_filter tests with sample data...")
    print()
    
    test_limit_filter()
    test_path_filter()
    test_commit_filter_with_samples()
    test_combined_filters()
    
    print("All tests completed!")