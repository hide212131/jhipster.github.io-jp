#!/usr/bin/env python3
"""Test metrics collection integration."""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metrics_collector import MetricsCollector, get_metrics_collector, reset_metrics_collector


def test_metrics_collector_basic():
    """Test basic metrics collector functionality."""
    print("Testing basic metrics collector...")
    
    collector = MetricsCollector()
    collector.start_pipeline()
    
    # Simulate file operations
    file1 = collector.record_file_operation("docs/test1.md", "replaced", 10, 12, "abc123", "retranslate")
    collector.record_llm_call("docs/test1.md", 0, 2.5)
    
    file2 = collector.record_file_operation("docs/test2.md", "inserted", 0, 5, "def456", "new")
    collector.record_llm_call("docs/test2.md", 1, 1.2)  # 1 retry
    
    collector.record_file_operation("static/image.png", "nondoc_copied", 0, 0, "ghi789", "copy")
    
    collector.end_pipeline()
    
    # Get aggregated stats
    stats = collector.get_aggregated_statistics()
    
    # Verify expected values
    assert stats["summary"]["files"]["replaced"] == 1
    assert stats["summary"]["files"]["inserted"] == 1
    assert stats["summary"]["files"]["nondoc_copied"] == 1
    assert stats["summary"]["operations"]["llm_calls"] == 2
    assert stats["summary"]["operations"]["retries"] == 1
    
    print("✓ Basic metrics collector test passed")


def test_metrics_report_generation():
    """Test report generation and file saving."""
    print("Testing report generation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        collector = MetricsCollector()
        collector.start_pipeline()
        
        # Add some test data
        collector.record_file_operation("test.md", "replaced", 5, 7, "test123", "retranslate")
        collector.record_llm_call("test.md", 0, 1.0)
        
        collector.end_pipeline()
        
        # Save report
        report_path = os.path.join(temp_dir, "test_report.json")
        success = collector.save_report(report_path)
        
        assert success, "Report saving should succeed"
        assert os.path.exists(report_path), "Report file should exist"
        
        # Load and verify report
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        assert "metadata" in report
        assert "summary" in report
        assert "files" in report
        assert len(report["files"]) == 1
        assert report["files"][0]["path"] == "test.md"
        
        print("✓ Report generation test passed")


def test_global_collector():
    """Test global collector singleton."""
    print("Testing global collector...")
    
    # Reset to ensure clean state
    reset_metrics_collector()
    
    # Get collector instances
    collector1 = get_metrics_collector()
    collector2 = get_metrics_collector()
    
    # Should be the same instance
    assert collector1 is collector2, "Should return same instance"
    
    # Add data through one instance
    collector1.record_file_operation("test.md", "kept", 5, 5, "test", "keep")
    
    # Should be accessible through other instance
    stats = collector2.get_aggregated_statistics()
    assert stats["summary"]["files"]["kept"] == 1
    
    print("✓ Global collector test passed")


def main():
    """Run all tests."""
    print("Running metrics collector tests...\n")
    
    try:
        test_metrics_collector_basic()
        test_metrics_report_generation()
        test_global_collector()
        
        print("\n✅ All metrics collector tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())