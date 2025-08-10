#!/usr/bin/env python3
"""Test apply_changes.py functionality with fixtures for 4 change types."""

import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from apply_changes import ChangeApplicator
from line_diff import LineDiff, DiffOperation


class TestApplyChangesFourTypes(unittest.TestCase):
    """Test apply_changes with 4 types of changes: equal/insert/delete/replace."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.applicator = ChangeApplicator()
        self.line_diff = LineDiff()
        
        # Mock git_utils to return test content
        self.applicator.git_utils.get_file_content = Mock()
        self.applicator.translator.translate_file_content = Mock()
        
        # Create temp directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = Path(self.temp_dir) / "test_file.md"
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_apply_changes_equal_operation(self):
        """Test applying changes with EQUAL operation (既訳温存)."""
        # Setup: unchanged content should preserve existing translation
        upstream_content = "# Title\nUnchanged content\nAnother line"
        existing_japanese = "# タイトル\n変更されていないコンテンツ\n別の行"
        
        changes_data = {
            "files": {
                "translate": [{
                    "path": "test_file.md",
                    "status": "unchanged",
                    "operations": [{
                        "operation": "equal",
                        "old_start": 0, "old_end": 3,
                        "new_start": 0, "new_end": 3,
                        "old_lines": upstream_content.split('\n'),
                        "new_lines": upstream_content.split('\n'),
                        "similarity_ratio": 1.0,
                        "change_type": "unchanged",
                        "strategy": "keep_existing"
                    }]
                }]
            }
        }
        
        # Mock existing Japanese content
        with patch.object(self.applicator, '_get_existing_translation') as mock_get_existing:
            mock_get_existing.return_value = existing_japanese
            
            # Create changes file
            changes_file = Path(self.temp_dir) / "changes.json"
            with open(changes_file, 'w', encoding='utf-8') as f:
                json.dump(changes_data, f)
            
            # Apply changes
            results = self.applicator.apply_changes(str(changes_file))
            
            # Verify existing translation was preserved
            self.assertEqual(len(results["processed_files"]), 1)
            result = results["processed_files"][0]["result"]
            self.assertEqual(result["action"], "kept_existing")
            self.assertEqual(results["statistics"]["kept_existing"], 1)
    
    def test_apply_changes_insert_operation(self):
        """Test applying changes with INSERT operation (新規挿入)."""
        # Setup: new content added should be translated
        changes_data = {
            "files": {
                "translate": [{
                    "path": "test_file.md",
                    "status": "modified", 
                    "operations": [{
                        "operation": "insert",
                        "old_start": 1, "old_end": 1,
                        "new_start": 1, "new_end": 2,
                        "old_lines": [],
                        "new_lines": ["New content to be translated"],
                        "similarity_ratio": 0.0,
                        "change_type": "added",
                        "strategy": "translate_new"
                    }]
                }]
            }
        }
        
        # Mock translation
        self.applicator.translator.translate_file_content.return_value = "翻訳された新しいコンテンツ"
        
        # Create changes file
        changes_file = Path(self.temp_dir) / "changes.json"
        with open(changes_file, 'w', encoding='utf-8') as f:
            json.dump(changes_data, f)
        
        # Apply changes
        results = self.applicator.apply_changes(str(changes_file))
        
        # Verify new content was translated
        self.assertEqual(len(results["processed_files"]), 1)
        result = results["processed_files"][0]["result"]
        self.assertEqual(result["action"], "translated")
        self.assertEqual(results["statistics"]["translated"], 1)
    
    def test_apply_changes_delete_operation(self):
        """Test applying changes with DELETE operation (削除)."""
        # Setup: deleted content should be removed from translation
        changes_data = {
            "files": {
                "translate": [{
                    "path": "test_file.md",
                    "status": "modified",
                    "operations": [{
                        "operation": "delete", 
                        "old_start": 1, "old_end": 2,
                        "new_start": 1, "new_end": 1,
                        "old_lines": ["Content to be deleted"],
                        "new_lines": [],
                        "similarity_ratio": 0.0,
                        "change_type": "removed",
                        "strategy": "delete_existing"
                    }]
                }]
            }
        }
        
        # Create changes file
        changes_file = Path(self.temp_dir) / "changes.json"
        with open(changes_file, 'w', encoding='utf-8') as f:
            json.dump(changes_data, f)
        
        # Apply changes
        results = self.applicator.apply_changes(str(changes_file))
        
        # Verify deletion was handled
        self.assertEqual(len(results["processed_files"]), 1)
        result = results["processed_files"][0]["result"]
        # Delete operations typically result in file-level handling
        self.assertIn(result["action"], ["kept_existing", "translated"])
    
    def test_apply_changes_replace_minor_edit(self):
        """Test applying changes with REPLACE operation - minor edit (既訳温存)."""
        # Setup: minor change (similarity ≥ 0.98) should preserve existing translation
        changes_data = {
            "files": {
                "translate": [{
                    "path": "test_file.md", 
                    "status": "modified",
                    "operations": [{
                        "operation": "replace",
                        "old_start": 0, "old_end": 1,
                        "new_start": 0, "new_end": 1,
                        "old_lines": ["Hello world"],
                        "new_lines": ["Hello world!"],
                        "similarity_ratio": 0.987,  # ≥ 0.98 threshold
                        "change_type": "minor_edit",
                        "strategy": "keep_existing"
                    }]
                }]
            }
        }
        
        existing_japanese = "こんにちは世界"
        
        with patch.object(self.applicator, '_get_existing_translation') as mock_get_existing:
            mock_get_existing.return_value = existing_japanese
            
            # Create changes file
            changes_file = Path(self.temp_dir) / "changes.json"
            with open(changes_file, 'w', encoding='utf-8') as f:
                json.dump(changes_data, f)
            
            # Apply changes
            results = self.applicator.apply_changes(str(changes_file))
            
            # Verify existing translation was preserved for minor edit
            self.assertEqual(len(results["processed_files"]), 1)
            result = results["processed_files"][0]["result"]
            self.assertEqual(result["action"], "kept_existing")
            self.assertEqual(results["statistics"]["kept_existing"], 1)
    
    def test_apply_changes_replace_major_change_with_llm(self):
        """Test applying changes with REPLACE operation - major change with LLM判定 (再翻訳)."""
        # Setup: borderline change that needs LLM to determine semantic change
        changes_data = {
            "files": {
                "translate": [{
                    "path": "test_file.md",
                    "status": "modified", 
                    "operations": [{
                        "operation": "replace",
                        "old_start": 0, "old_end": 1,
                        "new_start": 0, "new_end": 1,
                        "old_lines": ["Content about cats"],
                        "new_lines": ["Content about dogs"],
                        "similarity_ratio": 0.85,  # Between 0.8-0.98, borderline case
                        "change_type": "modified",
                        "strategy": "retranslate"
                    }]
                }]
            }
        }
        
        existing_japanese = "猫についてのコンテンツ"
        
        # Mock LLM semantic change detection and existing translation
        with patch.object(self.applicator.translator, 'check_semantic_change') as mock_llm:
            with patch.object(self.applicator, '_get_existing_translation') as mock_get_existing:
                mock_llm.return_value = True  # LLM says it's a semantic change
                mock_get_existing.return_value = existing_japanese
                self.applicator.translator.translate_file_content.return_value = "犬についてのコンテンツ"
                
                # Create changes file
                changes_file = Path(self.temp_dir) / "changes.json"
                with open(changes_file, 'w', encoding='utf-8') as f:
                    json.dump(changes_data, f)
                
                # Apply changes
                results = self.applicator.apply_changes(str(changes_file))
                
                # Verify content was retranslated due to semantic change
                self.assertEqual(len(results["processed_files"]), 1)
                result = results["processed_files"][0]["result"]
                self.assertEqual(result["action"], "translated")
                self.assertEqual(results["statistics"]["translated"], 1)
                
                # Verify LLM was consulted
                mock_llm.assert_called_once_with("Content about cats", "Content about dogs")
    
    def test_apply_changes_replace_llm_no_semantic_change(self):
        """Test LLM determines no semantic change (既訳温存)."""
        # Setup: borderline change where LLM determines no semantic change
        changes_data = {
            "files": {
                "translate": [{
                    "path": "test_file.md",
                    "status": "modified", 
                    "operations": [{
                        "operation": "replace",
                        "old_start": 0, "old_end": 1,
                        "new_start": 0, "new_end": 1,
                        "old_lines": ["Hello world"],
                        "new_lines": ["Hello world."],
                        "similarity_ratio": 0.85,  # Between 0.8-0.98, borderline case
                        "change_type": "modified",
                        "strategy": "retranslate"
                    }]
                }]
            }
        }
        
        existing_japanese = "こんにちは世界"
        
        # Mock LLM semantic change detection - no semantic change
        with patch.object(self.applicator.translator, 'check_semantic_change') as mock_llm:
            with patch.object(self.applicator, '_get_existing_translation') as mock_get_existing:
                mock_llm.return_value = False  # LLM says no semantic change
                mock_get_existing.return_value = existing_japanese
                
                # Create changes file
                changes_file = Path(self.temp_dir) / "changes.json"
                with open(changes_file, 'w', encoding='utf-8') as f:
                    json.dump(changes_data, f)
                
                # Apply changes
                results = self.applicator.apply_changes(str(changes_file))
                
                # Verify existing translation was preserved
                self.assertEqual(len(results["processed_files"]), 1)
                result = results["processed_files"][0]["result"]
                self.assertEqual(result["action"], "kept_existing_llm")
                self.assertEqual(results["statistics"]["kept_existing"], 1)
                
                # Verify LLM was consulted
                mock_llm.assert_called_once_with("Hello world", "Hello world.")


class TestApplyChangesIntegration(unittest.TestCase):
    """Integration tests for apply_changes with mixed operations."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.applicator = ChangeApplicator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_mixed_operations_file(self):
        """Test file with mixed operations (all 4 types)."""
        # Setup: file with equal, insert, delete, and replace operations
        changes_data = {
            "files": {
                "translate": [{
                    "path": "mixed_operations.md",
                    "status": "modified",
                    "operations": [
                        # EQUAL - keep existing
                        {
                            "operation": "equal",
                            "old_start": 0, "old_end": 1,
                            "new_start": 0, "new_end": 1,
                            "old_lines": ["# Title"],
                            "new_lines": ["# Title"],
                            "similarity_ratio": 1.0,
                            "change_type": "unchanged",
                            "strategy": "keep_existing"
                        },
                        # INSERT - translate new
                        {
                            "operation": "insert",
                            "old_start": 1, "old_end": 1,
                            "new_start": 1, "new_end": 2,
                            "old_lines": [],
                            "new_lines": ["New paragraph"],
                            "similarity_ratio": 0.0,
                            "change_type": "added",
                            "strategy": "translate_new"
                        },
                        # REPLACE minor - keep existing
                        {
                            "operation": "replace",
                            "old_start": 1, "old_end": 2,
                            "new_start": 2, "new_end": 3,
                            "old_lines": ["Some content"],
                            "new_lines": ["Some content."],
                            "similarity_ratio": 0.985,
                            "change_type": "minor_edit", 
                            "strategy": "keep_existing"
                        },
                        # DELETE - remove
                        {
                            "operation": "delete",
                            "old_start": 2, "old_end": 3,
                            "new_start": 3, "new_end": 3,
                            "old_lines": ["Old paragraph"],
                            "new_lines": [],
                            "similarity_ratio": 0.0,
                            "change_type": "removed",
                            "strategy": "delete_existing"
                        }
                    ]
                }]
            }
        }
        
        # Create changes file
        changes_file = Path(self.temp_dir) / "changes.json"
        with open(changes_file, 'w', encoding='utf-8') as f:
            json.dump(changes_data, f)
        
        # Mock dependencies
        with patch.object(self.applicator, '_apply_file_changes') as mock_apply:
            mock_apply.return_value = {
                "action": "mixed_operations",
                "details": "Applied 4 different operation types",
                "operations_count": 4
            }
            
            # Apply changes
            results = self.applicator.apply_changes(str(changes_file))
            
            # Verify mixed operations were processed
            self.assertEqual(len(results["processed_files"]), 1)
            mock_apply.assert_called_once()


if __name__ == '__main__':
    unittest.main()