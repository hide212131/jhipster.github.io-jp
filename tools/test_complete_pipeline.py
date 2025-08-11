#!/usr/bin/env python3
"""Test complete metrics pipeline with simulated file processing."""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metrics_collector import MetricsCollector, reset_metrics_collector
from pr_body import PRBodyGenerator


def test_complete_pipeline():
    """Test complete pipeline with simulated metrics."""
    print("Testing complete metrics pipeline...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Reset collector
        reset_metrics_collector()
        
        # Simulate a complete sync run
        collector = MetricsCollector()
        collector.start_pipeline()
        
        # Simulate various file operations
        # 1. New file translation
        collector.record_file_operation("docs/new-feature.md", "inserted", 0, 15, "abc123", "translate_new")
        collector.record_llm_call("docs/new-feature.md", 0, 2.3, False)
        
        # 2. Updated file retranslation 
        collector.record_file_operation("docs/existing-guide.md", "replaced", 20, 22, "def456", "retranslate")
        collector.record_llm_call("docs/existing-guide.md", 1, 3.7, False)  # 1 retry
        
        # 3. Kept existing translation
        collector.record_file_operation("docs/unchanged.md", "kept", 10, 10, "ghi789", "keep_existing")
        # No LLM call for kept files
        
        # 4. Deleted file
        collector.record_file_operation("docs/obsolete.md", "deleted", 8, 0, "jkl012", "delete_existing")
        
        # 5. Non-doc copied files
        collector.record_file_operation("static/logo.png", "nondoc_copied", 0, 0, "mno345", "copy_only")
        collector.record_file_operation("config.yml", "nondoc_copied", 0, 0, "pqr678", "copy_only")
        
        # 6. Error case
        collector.record_file_operation("docs/broken.md", "error", 5, 0, "stu901", "error", error="Translation failed")
        
        collector.end_pipeline()
        
        # Generate report
        report_path = os.path.join(temp_dir, "test_report.json")
        success = collector.save_report(report_path)
        assert success, "Report generation should succeed"
        
        # Load and verify report structure
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        # Verify metadata
        assert "metadata" in report
        assert report["metadata"]["total_files"] == 7
        
        # Verify summary statistics
        summary = report["summary"]
        assert summary["files"]["inserted"] == 1
        assert summary["files"]["replaced"] == 1  
        assert summary["files"]["kept"] == 1
        assert summary["files"]["deleted"] == 1
        assert summary["files"]["nondoc_copied"] == 2
        
        assert summary["operations"]["llm_calls"] == 2
        assert summary["operations"]["retries"] == 1
        assert summary["operations"]["error_count"] == 1
        
        assert summary["lines"]["added"] == 17  # 15 + 2
        assert summary["lines"]["removed"] == 13  # 8 from deleted + 5 from error file
        
        # Verify individual file records
        files = report["files"]
        assert len(files) == 7
        
        # Find specific files and verify their data
        new_file = next(f for f in files if f["path"] == "docs/new-feature.md")
        assert new_file["operation"] == "inserted"
        assert new_file["lines_after"] == 15
        assert new_file["llm_calls"] == 1
        assert new_file["retries"] == 0
        
        replaced_file = next(f for f in files if f["path"] == "docs/existing-guide.md")
        assert replaced_file["operation"] == "replaced"
        assert replaced_file["lines_before"] == 20
        assert replaced_file["lines_after"] == 22
        assert replaced_file["llm_calls"] == 1
        assert replaced_file["retries"] == 1
        
        error_file = next(f for f in files if f["path"] == "docs/broken.md")
        assert error_file["operation"] == "error"
        assert error_file["error"] == "Translation failed"
        
        print("✓ Complete pipeline test passed")
        
        # Test PR body generation with this report
        test_pr_body_with_metrics(temp_dir, report_path)


def test_pr_body_with_metrics(temp_dir, report_path):
    """Test PR body generation with realistic metrics."""
    print("Testing PR body generation with metrics...")
    
    # Create a mock changes file
    changes_data = {
        "files": {
            "translate": [
                {
                    "path": "docs/new-feature.md",
                    "status": "added",
                    "strategy": "translate_new",
                    "upstream_sha": "abc123",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/abc123"
                },
                {
                    "path": "docs/existing-guide.md", 
                    "status": "modified",
                    "strategy": "retranslate",
                    "upstream_sha": "def456",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/def456"
                }
            ],
            "copy_only": [
                {
                    "path": "static/logo.png",
                    "status": "added",
                    "upstream_sha": "mno345",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/mno345"
                }
            ],
            "ignore": []
        },
        "upstream_ref": "upstream/main"
    }
    
    changes_path = os.path.join(temp_dir, "changes.json")
    with open(changes_path, 'w', encoding='utf-8') as f:
        json.dump(changes_data, f, indent=2)
    
    # Generate PR body
    generator = PRBodyGenerator()
    pr_body = generator.generate_pr_body(changes_path, None, report_path)
    
    # Save PR body for inspection
    pr_body_path = os.path.join(temp_dir, "test_pr_body.md")
    with open(pr_body_path, 'w', encoding='utf-8') as f:
        f.write(pr_body)
    
    # Verify PR body contains metrics
    assert "📈 Aggregated Statistics (from report.json)" in pr_body
    assert "**Inserted**: 1 files" in pr_body
    assert "**Replaced**: 1 files" in pr_body
    assert "**LLM calls**: 2" in pr_body
    assert "**Retries**: 1" in pr_body
    
    print("✓ PR body generation with metrics test passed")
    
    # Print preview
    print("\n=== PR Body Preview ===")
    lines = pr_body.split('\n')
    for i, line in enumerate(lines[:30]):
        print(f"{i+1:2}: {line}")
    if len(lines) > 30:
        print(f"... ({len(lines) - 30} more lines)")


def main():
    """Run all tests."""
    print("Running complete metrics pipeline tests...\n")
    
    try:
        test_complete_pipeline()
        
        print("\n✅ All complete pipeline tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())