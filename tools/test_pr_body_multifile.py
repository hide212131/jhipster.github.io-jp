#!/usr/bin/env python3
"""Test pr_body.py for multi-file update scenarios.

Tests the acceptance criteria: マルチファイル更新時に表が正しく埋まる
(table filled correctly for multi-file updates)
"""

import json
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from pr_body import PRBodyGenerator


def create_multi_file_test_data():
    """Create comprehensive test data for multi-file scenario."""
    
    # Changes data with all required fields for comprehensive testing
    changes_data = {
        "upstream_ref": "upstream/main",
        "upstream_sha": "abc123def456789",
        "timestamp": "2025-01-23T10:30:00Z",
        "base_commit": "def456ghi789abc", 
        "files": {
            "translate": [
                {
                    "path": "docs/getting-started/installation.md",
                    "status": "modified",
                    "change_type": "replace",
                    "strategy": "retranslate",
                    "upstream_sha": "abc123def456789",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/abc123def456789",
                    "lines_added": 5,
                    "lines_removed": 3,
                    "lines_modified": 10,
                    "total_lines_before": 45,
                    "total_lines_after": 47,
                    "summary": {
                        "total_operations": 3,
                        "added_lines": 5,
                        "removed_lines": 3,
                        "modified_lines": 10
                    }
                },
                {
                    "path": "docs/creating-an-app/creating-an-entity.md",
                    "status": "added",
                    "change_type": "insert",
                    "strategy": "translate_new",
                    "upstream_sha": "def456ghi789abc",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/def456ghi789abc",
                    "lines_added": 50,
                    "lines_removed": 0,
                    "lines_modified": 0,
                    "total_lines_before": 0,
                    "total_lines_after": 50,
                    "summary": {
                        "total_operations": 1,
                        "added_lines": 50,
                        "removed_lines": 0,
                        "modified_lines": 0
                    }
                },
                {
                    "path": "docs/deprecated/old-guide.md",
                    "status": "deleted",
                    "change_type": "delete",
                    "strategy": "delete",
                    "upstream_sha": "ghi789abc123def",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/ghi789abc123def",
                    "lines_added": 0,
                    "lines_removed": 25,
                    "lines_modified": 0,
                    "total_lines_before": 25,
                    "total_lines_after": 0,
                    "summary": {
                        "total_operations": 1,
                        "added_lines": 0,
                        "removed_lines": 25,
                        "modified_lines": 0
                    }
                },
                {
                    "path": "docs/tutorials/microservices.md",
                    "status": "modified",
                    "change_type": "equal",
                    "strategy": "keep_existing",
                    "upstream_sha": "jkl012mno345pqr",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/jkl012mno345pqr",
                    "lines_added": 0,
                    "lines_removed": 0,
                    "lines_modified": 0,
                    "total_lines_before": 30,
                    "total_lines_after": 30,
                    "summary": {
                        "total_operations": 0,
                        "added_lines": 0,
                        "removed_lines": 0,
                        "modified_lines": 0
                    }
                },
                {
                    "path": "docs/advanced/security.md",
                    "status": "modified",
                    "change_type": "replace",
                    "strategy": "retranslate",
                    "upstream_sha": "pqr678stu901vwx",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/pqr678stu901vwx",
                    "lines_added": 15,
                    "lines_removed": 8,
                    "lines_modified": 20,
                    "total_lines_before": 80,
                    "total_lines_after": 87,
                    "summary": {
                        "total_operations": 3,
                        "added_lines": 15,
                        "removed_lines": 8,
                        "modified_lines": 20
                    }
                }
            ],
            "copy_only": [
                {
                    "path": "static/images/logo.png",
                    "status": "added",
                    "change_type": "copy",
                    "strategy": "copy_only",
                    "upstream_sha": "ghi789jkl012mno",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/ghi789jkl012mno"
                },
                {
                    "path": "package.json",
                    "status": "modified",
                    "change_type": "copy",
                    "strategy": "copy_only",
                    "upstream_sha": "jkl012mno345pqr",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/jkl012mno345pqr"
                },
                {
                    "path": "static/css/main.scss",
                    "status": "deleted",
                    "change_type": "copy",
                    "strategy": "copy_only",
                    "upstream_sha": "mno345pqr678stu",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/mno345pqr678stu"
                },
                {
                    "path": "assets/js/application.js",
                    "status": "modified",
                    "change_type": "copy",
                    "strategy": "copy_only",
                    "upstream_sha": "stu901vwx234yz",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/stu901vwx234yz"
                }
            ],
            "ignore": [
                {
                    "path": "node_modules/some-package/index.js",
                    "status": "modified",
                    "reason": "excluded_path"
                },
                {
                    "path": ".git/config",
                    "status": "modified",
                    "reason": "excluded_path"
                }
            ]
        },
        "statistics": {
            "total_files": 11,
            "translate_files": 5,
            "copy_only_files": 4,
            "ignored_files": 2
        }
    }
    
    # Apply results data
    apply_results_data = {
        "timestamp": "2025-01-23T10:35:00Z",
        "processing_time": 180.7,
        "pipeline_version": "1.0.0",
        "upstream_ref": "upstream/main",
        "translation_branch": "translate/sync-20250123-1030",
        "statistics": {
            "files": {
                "total_processed": 9,
                "translated": 3,
                "copied": 4,
                "kept_existing": 1,
                "deleted": 1,
                "errors": 0
            }
        },
        "files_processed": [
            {
                "path": "docs/getting-started/installation.md",
                "status": "translated",
                "strategy": "retranslate",
                "change_type": "replace",
                "line_count_before": 45,
                "line_count_after": 47,
                "llm_calls": 8,
                "retries": 1,
                "processing_time": 38.2
            }
        ],
        "errors": [],
        "verification": {
            "line_count_matches": True,
            "structure_preserved": True,
            "code_blocks_intact": True,
            "placeholders_restored": True,
            "all_files_valid": True
        }
    }
    
    # Report.json data  
    report_data = {
        "report_version": "1.0.0",
        "generation_time": "2025-01-23T10:40:00Z",
        "pipeline_run_id": "sync-20250123-1030",
        "summary": {
            "files": {
                "inserted": 1,
                "replaced": 2,
                "kept": 1,
                "deleted": 1,
                "nondoc_copied": 4
            },
            "operations": {
                "llm_calls": 45,
                "retries": 5,
                "cache_hits": 12,
                "total_processing_time": 180.7
            },
            "lines": {
                "total_original": 180,
                "total_final": 214,
                "net_change": 34
            }
        }
    }
    
    return changes_data, apply_results_data, report_data


def test_multi_file_table_generation():
    """Test that the table is correctly populated for multi-file updates."""
    print("=== Testing Multi-File Table Generation ===")
    
    # Create test data
    changes_data, apply_results_data, report_data = create_multi_file_test_data()
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as changes_file:
        json.dump(changes_data, changes_file, indent=2)
        changes_file_path = changes_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as apply_file:
        json.dump(apply_results_data, apply_file, indent=2)
        apply_file_path = apply_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as report_file:
        json.dump(report_data, report_file, indent=2)
        report_file_path = report_file.name
    
    try:
        # Generate PR body
        generator = PRBodyGenerator()
        pr_body = generator.generate_pr_body(changes_file_path, apply_file_path, report_file_path)
        
        # Validate table content
        lines = pr_body.split('\n')
        
        # Find translation files table
        table_started = False
        table_header_found = False
        translation_rows = []
        
        for line in lines:
            if "Translation Files" in line:
                table_started = True
                continue
            
            if table_started and line.startswith("| File | Status | Strategy"):
                table_header_found = True
                continue
                
            if table_started and line.startswith("|") and not line.startswith("|---"):
                if "File" not in line:  # Skip header row
                    translation_rows.append(line)
            
            if table_started and line.startswith("### ") and "Translation Files" not in line:
                break
        
        print(f"✅ Table header found: {table_header_found}")
        print(f"✅ Translation rows found: {len(translation_rows)}")
        
        # Validate each row has required information
        required_columns = 6  # File, Status, Strategy, Lines Diff, SHA, Commit
        valid_rows = 0
        
        for row in translation_rows:
            columns = [col.strip() for col in row.split('|') if col.strip()]
            if len(columns) >= required_columns:
                valid_rows += 1
                # Check if row contains expected data
                if any("docs/" in col for col in columns):
                    print(f"  ✅ Valid row: {columns[0]}")
        
        print(f"✅ Valid rows with all columns: {valid_rows}")
        
        # Verify copy-only files table
        copy_table_found = False
        copy_rows = []
        
        for i, line in enumerate(lines):
            if "Copy-Only Files" in line:
                copy_table_found = True
                # Look for table rows in the next few lines
                for j in range(i+1, min(i+20, len(lines))):
                    if lines[j].startswith("| ") and "File" not in lines[j] and not lines[j].startswith("|---"):
                        copy_rows.append(lines[j])
                    elif lines[j].startswith("### ") and j > i+5:
                        break
        
        print(f"✅ Copy-only table found: {copy_table_found}")
        print(f"✅ Copy-only rows found: {len(copy_rows)}")
        
        # Verify report.json aggregation
        report_aggregation_found = "Aggregated Statistics (from report.json)" in pr_body
        llm_calls_found = "LLM calls**: 45" in pr_body
        
        print(f"✅ Report.json aggregation found: {report_aggregation_found}")
        print(f"✅ LLM calls aggregated correctly: {llm_calls_found}")
        
        # Check for SHA and commit links
        sha_links_found = len([line for line in lines if "github.com/jhipster/jhipster.github.io/commit/" in line])
        print(f"✅ Commit links found: {sha_links_found}")
        
        # Overall validation
        success = (
            table_header_found and
            len(translation_rows) >= 4 and  # We have 5 translation files
            valid_rows >= 4 and
            copy_table_found and
            len(copy_rows) >= 3 and  # We have 4 copy-only files  
            report_aggregation_found and
            llm_calls_found and
            sha_links_found >= 8  # Should have many commit links
        )
        
        print(f"\n{'✅ PASS' if success else '❌ FAIL'}: Multi-file table generation test")
        
        if not success:
            print("\n=== Generated PR Body for Debug ===")
            print(pr_body[:1000] + "..." if len(pr_body) > 1000 else pr_body)
        
        return success
        
    finally:
        # Clean up
        os.unlink(changes_file_path)
        os.unlink(apply_file_path)
        os.unlink(report_file_path)


def test_edge_cases():
    """Test edge cases like empty files, missing data, etc."""
    print("\n=== Testing Edge Cases ===")
    
    # Test with minimal data
    minimal_changes = {
        "upstream_ref": "upstream/main",
        "files": {
            "translate": [],
            "copy_only": [],
            "ignore": []
        },
        "statistics": {
            "total_files": 0,
            "translate_files": 0,
            "copy_only_files": 0,
            "ignored_files": 0
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(minimal_changes, f, indent=2)
        minimal_file = f.name
    
    try:
        generator = PRBodyGenerator()
        pr_body = generator.generate_pr_body(minimal_file)
        
        # Should not crash and should contain basic structure
        basic_structure = (
            "LLM Translation Sync" in pr_body and
            "Summary" in pr_body and
            "File Changes" in pr_body
        )
        
        print(f"✅ Minimal data handling: {'PASS' if basic_structure else 'FAIL'}")
        return basic_structure
        
    finally:
        os.unlink(minimal_file)


if __name__ == '__main__':
    print("Testing PR Body Generator - Multi-file Update Scenarios")
    print("=" * 60)
    
    test1_result = test_multi_file_table_generation()
    test2_result = test_edge_cases()
    
    overall_result = test1_result and test2_result
    
    print("\n" + "=" * 60)
    print(f"Overall Test Result: {'✅ ALL TESTS PASSED' if overall_result else '❌ SOME TESTS FAILED'}")
    
    exit(0 if overall_result else 1)