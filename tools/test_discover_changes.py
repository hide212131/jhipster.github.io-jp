#!/usr/bin/env python3
"""Tests for discover_changes.py functionality."""

import json
import tempfile
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

from discover_changes import ChangeDiscoverer
from line_diff import LineDiff, DiffOperation
from git_utils import GitUtils
from file_filters import FileFilter


class TestLineDiff(unittest.TestCase):
    """Test LineDiff functionality."""
    
    def setUp(self):
        self.line_diff = LineDiff()
    
    def test_equal_operation(self):
        """Test detection of equal (unchanged) content."""
        old_lines = ["line1", "line2", "line3"]
        new_lines = ["line1", "line2", "line3"]
        
        operations = self.line_diff.get_diff_operations(old_lines, new_lines)
        
        self.assertEqual(len(operations), 1)
        self.assertEqual(operations[0].operation, "equal")
        self.assertEqual(operations[0].old_lines, old_lines)
        self.assertEqual(operations[0].new_lines, new_lines)
        
        # Test change type classification
        change_type = self.line_diff.classify_change_type(operations[0])
        self.assertEqual(change_type, "unchanged")
        
        # Test translation strategy
        strategy = self.line_diff.get_translation_strategy(operations[0])
        self.assertEqual(strategy, "keep_existing")
    
    def test_insert_operation(self):
        """Test detection of insert (added) content."""
        old_lines = ["line1", "line3"]
        new_lines = ["line1", "line2", "line3"]
        
        operations = self.line_diff.get_diff_operations(old_lines, new_lines)
        
        # Should have equal, insert, equal operations
        insert_ops = [op for op in operations if op.operation == "insert"]
        self.assertEqual(len(insert_ops), 1)
        self.assertEqual(insert_ops[0].new_lines, ["line2"])
        
        # Test change type classification
        change_type = self.line_diff.classify_change_type(insert_ops[0])
        self.assertEqual(change_type, "added")
        
        # Test translation strategy
        strategy = self.line_diff.get_translation_strategy(insert_ops[0])
        self.assertEqual(strategy, "translate_new")
    
    def test_delete_operation(self):
        """Test detection of delete (removed) content."""
        old_lines = ["line1", "line2", "line3"]
        new_lines = ["line1", "line3"]
        
        operations = self.line_diff.get_diff_operations(old_lines, new_lines)
        
        # Should have equal, delete, equal operations
        delete_ops = [op for op in operations if op.operation == "delete"]
        self.assertEqual(len(delete_ops), 1)
        self.assertEqual(delete_ops[0].old_lines, ["line2"])
        
        # Test change type classification
        change_type = self.line_diff.classify_change_type(delete_ops[0])
        self.assertEqual(change_type, "removed")
        
        # Test translation strategy
        strategy = self.line_diff.get_translation_strategy(delete_ops[0])
        self.assertEqual(strategy, "delete_existing")
    
    def test_replace_operation_major_change(self):
        """Test detection of replace (modified) content - major change."""
        old_lines = ["old content line"]
        new_lines = ["completely different content"]
        
        operations = self.line_diff.get_diff_operations(old_lines, new_lines)
        
        replace_ops = [op for op in operations if op.operation == "replace"]
        self.assertEqual(len(replace_ops), 1)
        self.assertEqual(replace_ops[0].old_lines, old_lines)
        self.assertEqual(replace_ops[0].new_lines, new_lines)
        
        # Test change type classification - should be major change
        change_type = self.line_diff.classify_change_type(replace_ops[0])
        self.assertEqual(change_type, "modified")
        
        # Test translation strategy
        strategy = self.line_diff.get_translation_strategy(replace_ops[0])
        self.assertEqual(strategy, "retranslate")
    
    def test_replace_operation_minor_change(self):
        """Test detection of replace (modified) content - minor change."""
        old_lines = ["Hello world"]
        new_lines = ["Hello world!"]  # Minor punctuation change
        
        operations = self.line_diff.get_diff_operations(old_lines, new_lines)
        
        replace_ops = [op for op in operations if op.operation == "replace"]
        self.assertEqual(len(replace_ops), 1)
        
        # Test change type classification - should be minor edit
        change_type = self.line_diff.classify_change_type(replace_ops[0])
        self.assertEqual(change_type, "minor_edit")
        
        # Test translation strategy
        strategy = self.line_diff.get_translation_strategy(replace_ops[0])
        self.assertEqual(strategy, "keep_existing")
    
    def test_diff_summary(self):
        """Test diff summary generation."""
        # Create a complex diff with multiple operation types
        operations = [
            DiffOperation("equal", 0, 2, 0, 2, ["line1", "line2"], ["line1", "line2"]),
            DiffOperation("insert", 2, 2, 2, 3, [], ["new line"]),
            DiffOperation("delete", 2, 3, 3, 3, ["old line"], []),
            DiffOperation("replace", 3, 4, 3, 4, ["old content"], ["new content"])
        ]
        
        summary = self.line_diff.get_diff_summary(operations)
        
        self.assertEqual(summary["total_operations"], 4)
        self.assertEqual(summary["unchanged_lines"], 2)
        self.assertEqual(summary["added_lines"], 1)
        self.assertEqual(summary["removed_lines"], 1)
        self.assertEqual(summary["major_changes"], 1)


class TestFileFilter(unittest.TestCase):
    """Test FileFilter functionality."""
    
    def setUp(self):
        self.file_filter = FileFilter()
    
    def test_translation_target_detection(self):
        """Test detection of files that should be translated."""
        # Markdown files should be translation targets
        self.assertTrue(self.file_filter.is_translation_target("docs/guide.md"))
        self.assertTrue(self.file_filter.is_translation_target("pages/index.mdx"))
        
        # Non-markdown files should not be translation targets
        self.assertFalse(self.file_filter.is_translation_target("package.json"))
        self.assertFalse(self.file_filter.is_translation_target("image.png"))
        
        # Excluded paths should not be translation targets
        self.assertFalse(self.file_filter.is_translation_target("node_modules/some-file.md"))
        self.assertFalse(self.file_filter.is_translation_target(".git/config"))
    
    def test_copy_only_detection(self):
        """Test detection of files that should be copied only."""
        # Non-markdown, non-excluded files should be copy-only
        self.assertTrue(self.file_filter.is_copy_only("README.txt"))
        self.assertTrue(self.file_filter.is_copy_only("config.js"))
        
        # Markdown files should not be copy-only
        self.assertFalse(self.file_filter.is_copy_only("docs/guide.md"))
        
        # Excluded files should not be copy-only
        self.assertFalse(self.file_filter.is_copy_only("image.png"))  # excluded extension
        self.assertFalse(self.file_filter.is_copy_only("node_modules/file.js"))  # excluded path
    
    def test_ignore_detection(self):
        """Test detection of files that should be ignored."""
        # Excluded paths should be ignored
        self.assertTrue(self.file_filter.should_ignore("node_modules/package.json"))
        self.assertTrue(self.file_filter.should_ignore(".git/config"))
        self.assertTrue(self.file_filter.should_ignore("build/output.js"))
        
        # Excluded extensions should be ignored
        self.assertTrue(self.file_filter.should_ignore("image.png"))
        self.assertTrue(self.file_filter.should_ignore("style.css"))
        
        # Regular files should not be ignored
        self.assertFalse(self.file_filter.should_ignore("docs/guide.md"))
        self.assertFalse(self.file_filter.should_ignore("README.md"))
    
    def test_filter_files_categorization(self):
        """Test file categorization into translate/copy_only/ignore."""
        files = [
            "docs/guide.md",           # translate
            "pages/index.mdx",         # translate
            "README.txt",              # copy_only
            "config.js",               # copy_only
            "image.png",               # ignore (excluded extension)
            "node_modules/dep.js",     # ignore (excluded path)
            ".git/config"              # ignore (excluded path)
        ]
        
        result = self.file_filter.filter_files(files)
        
        self.assertIn("docs/guide.md", result["translate"])
        self.assertIn("pages/index.mdx", result["translate"])
        self.assertIn("README.txt", result["copy_only"])
        self.assertIn("config.js", result["copy_only"])
        self.assertIn("image.png", result["ignore"])
        self.assertIn("node_modules/dep.js", result["ignore"])
        self.assertIn(".git/config", result["ignore"])


class TestChangeDiscoverer(unittest.TestCase):
    """Test ChangeDiscoverer functionality."""
    
    def setUp(self):
        self.discoverer = ChangeDiscoverer()
    
    @patch('git_utils.GitUtils.get_upstream_changes')
    @patch('git_utils.GitUtils.get_file_content')
    @patch('git_utils.GitUtils.add_upstream_remote')
    @patch('git_utils.GitUtils.fetch_upstream')
    def test_discover_changes_with_various_patterns(self, mock_fetch, mock_add_remote, mock_get_content, mock_get_changes):
        """Test discovery of changes with various change patterns."""
        # Mock git operations
        mock_add_remote.return_value = True
        mock_fetch.return_value = True
        mock_get_changes.return_value = ["test.md", "other.md"]
        
        # Mock file content to create different change patterns
        def mock_content_side_effect(file_path, ref):
            if file_path == "test.md":
                if ref == "upstream/main":
                    return "# Title\nOriginal content\nMore content"
                else:  # HEAD
                    return "# Title\nModified content\nMore content"
            elif file_path == "other.md":
                if ref == "upstream/main":
                    return "# Header\nLine 1\nLine 2"
                else:  # HEAD
                    return "# Header\nLine 1\nLine 2"  # No changes
            return None
        
        mock_get_content.side_effect = mock_content_side_effect
        
        # Discover changes
        changes = self.discoverer.discover_changes()
        
        # Verify structure
        self.assertIn("upstream_ref", changes)
        self.assertIn("meta_branch", changes)
        self.assertIn("files", changes)
        self.assertIn("translate", changes["files"])
        
        # Verify files are processed
        translate_files = changes["files"]["translate"]
        self.assertEqual(len(translate_files), 2)
        
        # Find the modified file
        modified_file = next(f for f in translate_files if f["path"] == "test.md")
        self.assertEqual(modified_file["status"], "modified")
        self.assertGreater(len(modified_file["operations"]), 0)
        
        # Verify operations contain all required fields
        for operation in modified_file["operations"]:
            required_fields = ["operation", "old_start", "old_end", "new_start", "new_end", 
                              "old_lines", "new_lines", "similarity_ratio", "change_type", "strategy"]
            for field in required_fields:
                self.assertIn(field, operation)
    
    @patch('git_utils.GitUtils.get_upstream_changes')
    @patch('git_utils.GitUtils.get_file_content')
    @patch('git_utils.GitUtils.add_upstream_remote')
    @patch('git_utils.GitUtils.fetch_upstream')
    def test_discover_changes_with_added_file(self, mock_fetch, mock_add_remote, mock_get_content, mock_get_changes):
        """Test discovery of added files."""
        mock_add_remote.return_value = True
        mock_fetch.return_value = True
        mock_get_changes.return_value = ["new_file.md"]
        
        def mock_content_side_effect(file_path, ref):
            if ref == "upstream/main":
                return "# New File\nThis is new content"
            else:  # HEAD - file doesn't exist locally
                return None
        
        mock_get_content.side_effect = mock_content_side_effect
        
        changes = self.discoverer.discover_changes()
        
        translate_files = changes["files"]["translate"]
        self.assertEqual(len(translate_files), 1)
        self.assertEqual(translate_files[0]["status"], "added")
    
    @patch('git_utils.GitUtils.get_upstream_changes')
    @patch('git_utils.GitUtils.get_file_content')
    @patch('git_utils.GitUtils.add_upstream_remote')
    @patch('git_utils.GitUtils.fetch_upstream')
    def test_discover_changes_with_deleted_file(self, mock_fetch, mock_add_remote, mock_get_content, mock_get_changes):
        """Test discovery of deleted files."""
        mock_add_remote.return_value = True
        mock_fetch.return_value = True
        mock_get_changes.return_value = ["deleted_file.md"]
        
        def mock_content_side_effect(file_path, ref):
            if ref == "upstream/main":
                return None  # File doesn't exist upstream
            else:  # HEAD
                return "# Deleted File\nThis file was deleted"
        
        mock_get_content.side_effect = mock_content_side_effect
        
        changes = self.discoverer.discover_changes()
        
        translate_files = changes["files"]["translate"]
        self.assertEqual(len(translate_files), 1)
        self.assertEqual(translate_files[0]["status"], "deleted")


class TestJSONOutput(unittest.TestCase):
    """Test JSON output format compliance."""
    
    @patch('git_utils.GitUtils.get_upstream_changes')
    @patch('git_utils.GitUtils.get_file_content')
    @patch('git_utils.GitUtils.add_upstream_remote')
    @patch('git_utils.GitUtils.fetch_upstream')
    def test_json_output_structure(self, mock_fetch, mock_add_remote, mock_get_content, mock_get_changes):
        """Test that JSON output has correct structure for all change patterns."""
        mock_add_remote.return_value = True
        mock_fetch.return_value = True
        mock_get_changes.return_value = ["complex_file.md"]
        
        # Create complex content with all types of changes
        upstream_content = """# Title
Original line 1
Line to be deleted
Original line 3
Line to be modified
Final line"""
        
        current_content = """# Title
Original line 1
Original line 3
New modified line
Added new line
Final line"""
        
        def mock_content_side_effect(file_path, ref):
            if ref == "upstream/main":
                return upstream_content
            else:  # HEAD
                return current_content
        
        mock_get_content.side_effect = mock_content_side_effect
        
        discoverer = ChangeDiscoverer()
        changes = discoverer.discover_changes()
        
        # Test that output is JSON serializable
        json_str = json.dumps(changes, ensure_ascii=False, indent=2)
        parsed = json.loads(json_str)
        
        # Test required top-level fields
        required_fields = ["upstream_ref", "meta_branch", "timestamp", "files"]
        for field in required_fields:
            self.assertIn(field, parsed)
        
        # Test file categories
        self.assertIn("translate", parsed["files"])
        self.assertIn("copy_only", parsed["files"])
        self.assertIn("ignore", parsed["files"])
        
        # Test file structure
        translate_files = parsed["files"]["translate"]
        self.assertEqual(len(translate_files), 1)
        
        file_info = translate_files[0]
        required_file_fields = ["path", "status", "operations", "summary"]
        for field in required_file_fields:
            self.assertIn(field, file_info)
        
        # Test operations structure
        operations = file_info["operations"]
        self.assertGreater(len(operations), 0)
        
        operation_types = set(op["operation"] for op in operations)
        # Should have multiple operation types for complex changes
        self.assertGreater(len(operation_types), 1)
        
        # Test that operations include all required fields
        for operation in operations:
            required_op_fields = ["operation", "old_start", "old_end", "new_start", "new_end",
                                 "old_lines", "new_lines", "similarity_ratio", "change_type", "strategy"]
            for field in required_op_fields:
                self.assertIn(field, operation)
        
        # Test summary structure
        summary = file_info["summary"]
        required_summary_fields = ["total_operations", "unchanged_lines", "added_lines",
                                  "removed_lines", "modified_lines", "minor_edits", "major_changes"]
        for field in required_summary_fields:
            self.assertIn(field, summary)


def main():
    """Run all tests."""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()