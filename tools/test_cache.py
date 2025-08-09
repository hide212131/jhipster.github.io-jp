"""
Basic tests for translation cache and reporting functionality.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
import sys

# Add tools to path for testing
sys.path.insert(0, str(Path(__file__).parent))

from cache import TranslationCache, CacheSession
from report import TranslationReporter


class TestTranslationCache(unittest.TestCase):
    """Test TranslationCache functionality."""
    
    def setUp(self):
        """Set up test with temporary cache directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = TranslationCache(self.temp_dir)
        
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_cache_set_get(self):
        """Test basic cache set and get operations."""
        path = "test.md"
        upstream_sha = "abc123"
        line_no = 1
        src_content = "Hello World"
        translation = "こんにちは世界"
        
        # Initially should not exist
        self.assertIsNone(self.cache.get(path, upstream_sha, line_no, src_content))
        self.assertFalse(self.cache.exists(path, upstream_sha, line_no, src_content))
        
        # Store translation
        self.cache.set(path, upstream_sha, line_no, src_content, translation)
        
        # Should now exist and return correct translation
        self.assertEqual(self.cache.get(path, upstream_sha, line_no, src_content), translation)
        self.assertTrue(self.cache.exists(path, upstream_sha, line_no, src_content))
        
    def test_cache_hash_sensitivity(self):
        """Test that cache is sensitive to content changes."""
        path = "test.md"
        upstream_sha = "abc123"
        line_no = 1
        
        # Store translation for original content
        self.cache.set(path, upstream_sha, line_no, "Hello", "こんにちは")
        
        # Different content should not hit cache
        self.assertIsNone(self.cache.get(path, upstream_sha, line_no, "Hello!"))
        
        # Original content should still hit cache
        self.assertEqual(self.cache.get(path, upstream_sha, line_no, "Hello"), "こんにちは")
        
    def test_cache_stats(self):
        """Test cache statistics."""
        initial_stats = self.cache.get_stats()
        self.assertEqual(initial_stats["total_entries"], 0)
        
        # Add some entries
        self.cache.set("file1.md", "sha1", 1, "content1", "translation1")
        self.cache.set("file1.md", "sha1", 2, "content2", "translation2")
        self.cache.set("file2.md", "sha2", 1, "content3", "translation3")
        
        stats = self.cache.get_stats()
        self.assertEqual(stats["total_entries"], 3)
        self.assertEqual(stats["unique_files"], 2)
        self.assertIsNotNone(stats["last_entry"])
        
    def test_cache_clear(self):
        """Test cache clearing functionality."""
        # Add entries
        self.cache.set("file1.md", "sha1", 1, "content1", "translation1")
        self.cache.set("file2.md", "sha2", 1, "content2", "translation2")
        
        # Clear specific file
        deleted = self.cache.clear_cache("file1.md")
        self.assertEqual(deleted, 1)
        
        # Verify file1 entries are gone but file2 remains
        self.assertIsNone(self.cache.get("file1.md", "sha1", 1, "content1"))
        self.assertEqual(self.cache.get("file2.md", "sha2", 1, "content2"), "translation2")
        
        # Clear all
        deleted = self.cache.clear_cache()
        self.assertEqual(deleted, 1)
        self.assertEqual(self.cache.get_stats()["total_entries"], 0)


class TestCacheSession(unittest.TestCase):
    """Test CacheSession functionality."""
    
    def setUp(self):
        """Set up test with temporary cache."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = TranslationCache(self.temp_dir)
        self.session = CacheSession(self.cache)
        
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_session_hit_miss_tracking(self):
        """Test hit/miss tracking in session."""
        path = "test.md"
        upstream_sha = "abc123"
        
        # First lookup should be a miss
        result = self.session.lookup(path, upstream_sha, 1, "Hello")
        self.assertIsNone(result)
        self.assertEqual(self.session.misses, 1)
        self.assertEqual(self.session.hits, 0)
        
        # Store translation
        self.session.store(path, upstream_sha, 1, "Hello", "こんにちは")
        
        # Second lookup should be a hit
        result = self.session.lookup(path, upstream_sha, 1, "Hello")
        self.assertEqual(result, "こんにちは")
        self.assertEqual(self.session.hits, 1)
        self.assertEqual(self.session.misses, 1)
        
        # Check hit rate
        self.assertEqual(self.session.get_hit_rate(), 50.0)
        
    def test_session_stats(self):
        """Test session statistics."""
        stats = self.session.get_session_stats()
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["hit_rate"], 0.0)
        self.assertEqual(len(stats["operations"]), 0)


class TestTranslationReporter(unittest.TestCase):
    """Test TranslationReporter functionality."""
    
    def setUp(self):
        """Set up test with temporary output directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.reporter = TranslationReporter(self.temp_dir)
        
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_report_generation(self):
        """Test basic report generation."""
        # Add some test data
        self.reporter.add_file_processing("test.md", "abc123", 10, 8, 5)
        self.reporter.add_line_decision(
            "test.md", 1, "Hello", "こんにちは", "Standard greeting", False, 120.5
        )
        self.reporter.add_summary_stats(1, 10, 8, 5, 500.0)
        
        # Generate report
        report_path = self.reporter.generate_report()
        
        # Verify file exists
        self.assertTrue(os.path.exists(report_path))
        
        # Verify content
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.assertIn("metadata", data)
        self.assertIn("files", data)
        self.assertIn("line_decisions", data)
        self.assertIn("summary", data)
        
        # Check specific values
        self.assertEqual(data["files"]["test.md"]["total_lines"], 10)
        self.assertEqual(data["summary"]["total_files"], 1)
        self.assertEqual(len(data["line_decisions"]), 1)
        
    def test_report_data_structure(self):
        """Test report data structure."""
        data = self.reporter.get_report_data()
        
        # Check required fields
        required_fields = ["metadata", "cache_stats", "files", "session_stats", "line_decisions"]
        for field in required_fields:
            self.assertIn(field, data)
            
        # Check metadata
        self.assertIn("generated_at", data["metadata"])
        self.assertIn("version", data["metadata"])


if __name__ == "__main__":
    unittest.main()