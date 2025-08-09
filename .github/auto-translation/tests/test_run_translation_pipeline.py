#!/usr/bin/env python3
"""
run_translation_pipeline.py のテスト
開発モード機能のテストを含む
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from run_translation_pipeline import TranslationPipeline


class TestTranslationPipelineDev(unittest.TestCase):
    """開発モード機能のテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.test_classification = {
            "summary": {
                "a": ["docs/new-guide.md", "docs/another-new.md"],
                "b-1": ["docs/updated.md", "README.md"],
                "b-2": ["docs/conflict.md"],
                "c": ["package.json", "image.png"]
            },
            "total_files": 6,
            "translatable_files": 5
        }
        
    def test_apply_dev_mode_filters_normal_mode(self):
        """通常モードではフィルタが適用されないことをテスト"""
        pipeline = TranslationPipeline("abc1234", mode="normal")
        result = pipeline.apply_dev_mode_filters(self.test_classification.copy())
        
        # 変更されないことを確認
        self.assertEqual(result, self.test_classification)
        
    def test_filter_by_paths(self):
        """パスフィルタのテスト"""
        pipeline = TranslationPipeline("abc1234", mode="dev", paths=["docs/"])
        
        filtered = pipeline._filter_by_paths(self.test_classification.copy())
        
        # docs/ 以下のファイルのみ残ることを確認
        expected_a = ["docs/new-guide.md", "docs/another-new.md"]
        expected_b1 = ["docs/updated.md"]
        expected_b2 = ["docs/conflict.md"]
        expected_c = []  # package.json, image.png は除外
        
        self.assertEqual(filtered["summary"]["a"], expected_a)
        self.assertEqual(filtered["summary"]["b-1"], expected_b1)
        self.assertEqual(filtered["summary"]["b-2"], expected_b2)
        self.assertEqual(filtered["summary"]["c"], expected_c)
        
    def test_filter_by_multiple_paths(self):
        """複数パスフィルタのテスト"""
        pipeline = TranslationPipeline("abc1234", mode="dev", paths=["docs/", "README"])
        
        filtered = pipeline._filter_by_paths(self.test_classification.copy())
        
        # docs/ 以下のファイルとREADMEで始まるファイルが残ることを確認
        expected_b1 = ["docs/updated.md", "README.md"]
        self.assertEqual(filtered["summary"]["b-1"], expected_b1)
        
    def test_filter_by_limit(self):
        """ファイル数制限のテスト"""
        pipeline = TranslationPipeline("abc1234", mode="dev", limit=3)
        
        filtered = pipeline._filter_by_limit(self.test_classification.copy())
        
        # 翻訳対象ファイル数をカウント
        translatable_count = (
            len(filtered["summary"]["a"]) + 
            len(filtered["summary"]["b-1"]) + 
            len(filtered["summary"]["b-2"])
        )
        
        # 制限数以下になることを確認
        self.assertLessEqual(translatable_count, 3)
        
        # 優先順位（a > b-1 > b-2）が保たれることを確認
        # a カテゴリが優先されるので、2ファイルとも残るはず
        self.assertEqual(len(filtered["summary"]["a"]), 2)
        
        # c カテゴリ（非翻訳対象）は影響されない
        self.assertEqual(filtered["summary"]["c"], self.test_classification["summary"]["c"])
        
    @patch('subprocess.run')
    def test_filter_by_before_commit(self, mock_run):
        """コミット日時フィルタのテスト"""
        # git diffの結果をモック
        mock_result = Mock()
        mock_result.stdout = "docs/new-guide.md\nREADME.md"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        pipeline = TranslationPipeline("abc1234", mode="dev", before_commit="def5678")
        
        filtered = pipeline._filter_by_before_commit(self.test_classification.copy())
        
        # git diffで返されたファイルが除外されることを確認
        self.assertNotIn("docs/new-guide.md", filtered["summary"]["a"])
        self.assertNotIn("README.md", filtered["summary"]["b-1"])
        
        # その他のファイルは残ることを確認
        self.assertIn("docs/another-new.md", filtered["summary"]["a"])
        self.assertIn("docs/updated.md", filtered["summary"]["b-1"])
        
    @patch('subprocess.run')
    def test_filter_by_before_commit_error(self, mock_run):
        """コミット日時フィルタでエラーが発生した場合のテスト"""
        # git diffがエラーを返す場合
        mock_run.side_effect = subprocess.CalledProcessError(1, "git diff")
        
        pipeline = TranslationPipeline("abc1234", mode="dev", before_commit="invalid")
        
        # エラーが発生しても元の分類結果が返されることを確認
        filtered = pipeline._filter_by_before_commit(self.test_classification.copy())
        self.assertEqual(filtered, self.test_classification)
        
    def test_combined_filters(self):
        """複数フィルタの組み合わせテスト"""
        pipeline = TranslationPipeline(
            "abc1234", 
            mode="dev", 
            paths=["docs/"], 
            limit=2
        )
        
        # パスフィルタを適用
        filtered = pipeline._filter_by_paths(self.test_classification.copy())
        
        # 制限フィルタを適用
        filtered = pipeline._filter_by_limit(filtered)
        
        # 翻訳対象ファイル数をカウント
        translatable_count = (
            len(filtered["summary"]["a"]) + 
            len(filtered["summary"]["b-1"]) + 
            len(filtered["summary"]["b-2"])
        )
        
        # docs/ 以下かつ制限数以下になることを確認
        self.assertLessEqual(translatable_count, 2)
        
        # すべてのファイルがdocs/以下であることを確認
        all_files = (
            filtered["summary"]["a"] + 
            filtered["summary"]["b-1"] + 
            filtered["summary"]["b-2"]
        )
        for file_path in all_files:
            self.assertTrue(file_path.startswith("docs/"))
            
    def test_apply_dev_mode_filters_updates_translatable_count(self):
        """開発モードでtranslatable_filesが再計算されることをテスト"""
        pipeline = TranslationPipeline("abc1234", mode="dev", limit=1)
        
        result = pipeline.apply_dev_mode_filters(self.test_classification.copy())
        
        # translatable_filesが再計算されることを確認
        self.assertIn("translatable_files", result)
        
        # 制限後の翻訳対象ファイル数を計算
        actual_translatable = (
            len(result["summary"]["a"]) + 
            len(result["summary"]["b-1"]) + 
            len(result["summary"]["b-2"])
        )
        
        # 再計算された値が正しいことを確認
        self.assertEqual(result["translatable_files"], actual_translatable)
        self.assertLessEqual(actual_translatable, 1)


class TestTranslationPipelineInit(unittest.TestCase):
    """TranslationPipeline初期化のテスト"""
    
    def test_init_normal_mode(self):
        """通常モードの初期化"""
        pipeline = TranslationPipeline("abc1234")
        
        self.assertEqual(pipeline.commit_hash, "abc1234")
        self.assertEqual(pipeline.mode, "normal")
        self.assertFalse(pipeline.dry_run)
        self.assertIsNone(pipeline.before_commit)
        self.assertIsNone(pipeline.limit)
        self.assertEqual(pipeline.paths, [])
        
    def test_init_dev_mode_with_filters(self):
        """開発モードとフィルタオプションの初期化"""
        pipeline = TranslationPipeline(
            "abc1234",
            dry_run=True,
            mode="dev",
            before_commit="def5678",
            limit=5,
            paths=["docs/", "src/"]
        )
        
        self.assertEqual(pipeline.commit_hash, "abc1234")
        self.assertEqual(pipeline.mode, "dev")
        self.assertTrue(pipeline.dry_run)
        self.assertEqual(pipeline.before_commit, "def5678")
        self.assertEqual(pipeline.limit, 5)
        self.assertEqual(pipeline.paths, ["docs/", "src/"])


if __name__ == "__main__":
    unittest.main()