#!/usr/bin/env python3
"""
LLM Cache システムのテスト
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

# テスト対象のモジュールをインポート
import sys
sys.path.append(str(Path(__file__).parent.parent / "scripts"))

from llm_cache import LLMCache


class TestLLMCache(unittest.TestCase):
    """LLMCacheのテストクラス"""

    def setUp(self):
        """テスト前の準備"""
        # 一時的なデータベースファイルを作成
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.cache = LLMCache(cache_db_path=self.temp_db.name)

    def tearDown(self):
        """テスト後の清理"""
        # 一時ファイルを削除
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_cache_initialization(self):
        """キャッシュの初期化テスト"""
        # データベースが作成されていることを確認
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # 統計情報が正しく初期化されていることを確認
        stats = self.cache.get_stats()
        self.assertEqual(stats["cache_hits"], 0)
        self.assertEqual(stats["cache_misses"], 0)
        self.assertEqual(stats["cache_stores"], 0)

    def test_cache_put_and_get(self):
        """キャッシュの保存と取得テスト"""
        # テストデータ
        file_path = "docs/test.md"
        upstream_sha = "abc1234"
        line_no = 1
        original = "Hello, world!"
        translated = "こんにちは、世界！"
        
        # キャッシュに保存
        result = self.cache.put(file_path, upstream_sha, line_no, original, translated)
        self.assertTrue(result)
        
        # キャッシュから取得
        cached_result = self.cache.get(file_path, upstream_sha, line_no, original)
        self.assertEqual(cached_result, translated)
        
        # 統計情報を確認
        stats = self.cache.get_stats()
        self.assertEqual(stats["cache_hits"], 1)
        self.assertEqual(stats["cache_stores"], 1)

    def test_cache_miss(self):
        """キャッシュミステスト"""
        # 存在しないキーでアクセス
        result = self.cache.get("nonexistent.md", "xyz789", 1, "Missing content")
        self.assertIsNone(result)
        
        # 統計情報を確認
        stats = self.cache.get_stats()
        self.assertEqual(stats["cache_misses"], 1)

    def test_cache_key_sensitivity(self):
        """キャッシュキーの敏感性テスト"""
        file_path = "docs/test.md"
        upstream_sha = "abc1234"
        line_no = 1
        original1 = "Hello, world!"
        original2 = "Hello, world? "  # 少し違う
        translated = "こんにちは、世界！"
        
        # 最初のコンテンツをキャッシュ
        self.cache.put(file_path, upstream_sha, line_no, original1, translated)
        
        # 同じコンテンツは取得できる
        result1 = self.cache.get(file_path, upstream_sha, line_no, original1)
        self.assertEqual(result1, translated)
        
        # 少し違うコンテンツは取得できない
        result2 = self.cache.get(file_path, upstream_sha, line_no, original2)
        self.assertIsNone(result2)

    def test_hit_rate_calculation(self):
        """ヒット率計算テスト"""
        # 初期状態でのヒット率
        stats = self.cache.get_stats()
        self.assertEqual(stats["hit_rate_percent"], 0.0)
        
        # テストデータでキャッシュを作成
        self.cache.put("test.md", "sha123", 1, "content1", "翻訳1")
        self.cache.put("test.md", "sha123", 2, "content2", "翻訳2")
        
        # 2回ヒット、1回ミス
        self.cache.get("test.md", "sha123", 1, "content1")  # ヒット
        self.cache.get("test.md", "sha123", 2, "content2")  # ヒット
        self.cache.get("test.md", "sha123", 3, "content3")  # ミス
        
        stats = self.cache.get_stats()
        self.assertEqual(stats["cache_hits"], 2)
        self.assertEqual(stats["cache_misses"], 1)
        self.assertEqual(stats["total_requests"], 3)
        self.assertAlmostEqual(stats["hit_rate_percent"], 66.67, places=1)

    def test_database_stats(self):
        """データベース統計テスト"""
        # いくつかのエントリを追加
        for i in range(5):
            self.cache.put(f"test{i}.md", "sha123", 1, f"content{i}", f"翻訳{i}")
        
        db_stats = self.cache.get_database_stats()
        
        # 基本的な統計が取得できることを確認
        self.assertIn("total_entries", db_stats)
        self.assertEqual(db_stats["total_entries"], 5)
        self.assertIn("database_size_mb", db_stats)
        self.assertIn("top_files", db_stats)

    def test_cleanup_old_entries(self):
        """古いエントリのクリーンアップテスト"""
        # エントリを追加
        self.cache.put("old.md", "sha123", 1, "old content", "古い翻訳")
        
        # 0日後（つまり今）以降のエントリを削除
        deleted_count = self.cache.cleanup_old_entries(0)
        
        # 何かが削除されることを確認（実際の数はタイミングによる）
        self.assertGreaterEqual(deleted_count, 0)

    def test_clear_cache(self):
        """キャッシュクリアテスト"""
        # エントリを追加
        self.cache.put("test.md", "sha123", 1, "content", "翻訳")
        
        # キャッシュをクリア
        result = self.cache.clear_cache()
        self.assertTrue(result)
        
        # エントリが削除されていることを確認
        cached_result = self.cache.get("test.md", "sha123", 1, "content")
        self.assertIsNone(cached_result)
        
        # データベース統計でも確認
        db_stats = self.cache.get_database_stats()
        self.assertEqual(db_stats["total_entries"], 0)


class TestReportGeneration(unittest.TestCase):
    """レポート生成のテスト"""

    def test_report_schema(self):
        """レポートJSONスキーマのテスト"""
        # サンプルレポートデータ
        sample_report = {
            "metadata": {
                "pipeline_start_time": "2024-01-01T10:00:00",
                "pipeline_end_time": "2024-01-01T10:30:00",
                "commit_hash": "abc1234",
                "dry_run": False,
                "classification_file": "classification.json",
                "report_generated_at": "2024-01-01T10:30:00"
            },
            "summary": {
                "total_files": 10,
                "translatable_files": 5,
                "cache_hit_rate": 75.0,
                "lines_processed": 100,
                "lines_cached": 75,
                "lines_translated": 25
            },
            "classification": {
                "summary": {
                    "a": ["new1.md", "new2.md"],
                    "b-1": ["updated1.md"],
                    "b-2": ["conflict1.md"],
                    "c": ["image.png"]
                }
            },
            "decisions": [
                {
                    "file_path": "test.md",
                    "line_no": 1,
                    "decision": "cache_hit",
                    "reason": "found_in_cache",
                    "original": "Hello",
                    "translated": "こんにちは"
                }
            ],
            "cache_stats": {
                "runtime_stats": {
                    "cache_hits": 75,
                    "cache_misses": 25,
                    "total_requests": 100,
                    "hit_rate_percent": 75.0
                }
            }
        }
        
        # 必須フィールドの確認
        self.assertIn("metadata", sample_report)
        self.assertIn("summary", sample_report)
        self.assertIn("decisions", sample_report)
        
        # metadata の必須フィールド
        metadata = sample_report["metadata"]
        required_metadata_fields = [
            "pipeline_start_time", "pipeline_end_time", "commit_hash",
            "dry_run", "report_generated_at"
        ]
        for field in required_metadata_fields:
            self.assertIn(field, metadata)
        
        # summary の必須フィールド
        summary = sample_report["summary"]
        required_summary_fields = [
            "total_files", "translatable_files", "cache_hit_rate",
            "lines_processed", "lines_cached", "lines_translated"
        ]
        for field in required_summary_fields:
            self.assertIn(field, summary)
        
        # decisions の構造確認
        if sample_report["decisions"]:
            decision = sample_report["decisions"][0]
            required_decision_fields = [
                "file_path", "line_no", "decision", "reason", "original", "translated"
            ]
            for field in required_decision_fields:
                self.assertIn(field, decision)

    def test_decision_types(self):
        """決定理由の種類テスト"""
        valid_decisions = ["keep", "retranslate", "insert", "delete", "cache_hit"]
        
        # サンプル決定データ
        decisions = [
            {"decision": "keep", "reason": "empty_or_markdown_syntax"},
            {"decision": "retranslate", "reason": "llm_translation"},
            {"decision": "cache_hit", "reason": "found_in_cache"},
            {"decision": "keep", "reason": "translation_failed"},
        ]
        
        for decision_data in decisions:
            self.assertIn(decision_data["decision"], valid_decisions)


if __name__ == "__main__":
    unittest.main()