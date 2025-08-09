#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム
変更適用テスト
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# プロジェクトルートにモジュールを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from apply_changes import (
    ChangePolicy, ApplicationResult, SemanticChangeDetector, ChangeApplicator
)


class TestSemanticChangeDetector(unittest.TestCase):
    """SemanticChangeDetector クラスのテスト"""
    
    def setUp(self):
        # LLM API を使用しないモックベースのテスト
        self.detector = SemanticChangeDetector(api_key=None)
    
    def test_fallback_semantic_detection_no_change(self):
        """フォールバック意味検出：変更なしのテスト"""
        old_text = "Hello, world!"
        new_text = "Hello,  world!"  # 空白が1つ追加されただけ
        
        result = self.detector._fallback_semantic_detection(old_text, new_text)
        
        # 軽微な変更のため False を期待
        self.assertFalse(result)
    
    def test_fallback_semantic_detection_significant_change(self):
        """フォールバック意味検出：重要な変更のテスト"""
        old_text = "Hello, world!"
        new_text = "Goodbye, world! This is a completely different message."
        
        result = self.detector._fallback_semantic_detection(old_text, new_text)
        
        # 大きな変更のため True を期待
        self.assertTrue(result)
    
    def test_fallback_semantic_detection_punctuation_only(self):
        """フォールバック意味検出：句読点のみの変更テスト"""
        old_text = "これはテストです。"
        new_text = "これはテストです！"  # 句読点のみ変更
        
        result = self.detector._fallback_semantic_detection(old_text, new_text)
        
        # 句読点のみの変更のため False を期待
        self.assertFalse(result)
    
    @patch('google.generativeai.GenerativeModel')
    def test_has_semantic_change_with_llm_yes(self, mock_model_class):
        """LLM による意味変更検出：YES 回答のテスト"""
        # LLM レスポンスをモック
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "YES"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        detector = SemanticChangeDetector(api_key="fake_key")
        detector.model = mock_model
        
        result = detector.has_semantic_change("old text", "new text")
        
        self.assertTrue(result)
        mock_model.generate_content.assert_called_once()
    
    @patch('google.generativeai.GenerativeModel')
    def test_has_semantic_change_with_llm_no(self, mock_model_class):
        """LLM による意味変更検出：NO 回答のテスト"""
        # LLM レスポンスをモック
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "NO"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        detector = SemanticChangeDetector(api_key="fake_key")
        detector.model = mock_model
        
        result = detector.has_semantic_change("old text", "new text")
        
        self.assertFalse(result)
    
    @patch('google.generativeai.GenerativeModel')
    def test_has_semantic_change_llm_error_fallback(self, mock_model_class):
        """LLM エラー時のフォールバック処理テスト"""
        # LLM でエラーが発生
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_model_class.return_value = mock_model
        
        detector = SemanticChangeDetector(api_key="fake_key")
        detector.model = mock_model
        
        # エラー時はフォールバック処理が実行される
        result = detector.has_semantic_change("short", "much longer text with significant changes")
        
        # フォールバック判定が実行されることを確認
        self.assertTrue(result)  # 大きな変更なので True
    
    def test_create_semantic_change_prompt(self):
        """意味変更判定プロンプト作成のテスト"""
        detector = SemanticChangeDetector()
        
        old_text = "古いテキスト"
        new_text = "新しいテキスト"
        
        prompt = detector._create_semantic_change_prompt(old_text, new_text)
        
        self.assertIn("YES", prompt)
        self.assertIn("NO", prompt)
        self.assertIn(old_text, prompt)
        self.assertIn(new_text, prompt)
        self.assertIn("意味的な変更", prompt)


class TestChangeApplicator(unittest.TestCase):
    """ChangeApplicator クラスのテスト"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.applicator = ChangeApplicator(self.temp_dir)
        
        # SemanticChangeDetector をモック
        self.applicator.semantic_detector = MagicMock()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_determine_policy_equal(self):
        """equal 操作のポリシー決定テスト"""
        operation = {"operation": "equal"}
        
        policy = self.applicator.determine_policy(operation)
        
        self.assertEqual(policy, ChangePolicy.KEEP_EXISTING)
    
    def test_determine_policy_insert(self):
        """insert 操作のポリシー決定テスト"""
        operation = {"operation": "insert"}
        
        policy = self.applicator.determine_policy(operation)
        
        self.assertEqual(policy, ChangePolicy.NEW_TRANSLATION)
    
    def test_determine_policy_delete(self):
        """delete 操作のポリシー決定テスト"""
        operation = {"operation": "delete"}
        
        policy = self.applicator.determine_policy(operation)
        
        self.assertEqual(policy, ChangePolicy.DELETE)
    
    def test_determine_policy_replace_minor(self):
        """replace 操作（軽微変更）のポリシー決定テスト"""
        operation = {
            "operation": "replace",
            "is_minor_change": True,
            "old_lines": ["old text"],
            "new_lines": ["new text"]
        }
        
        policy = self.applicator.determine_policy(operation)
        
        self.assertEqual(policy, ChangePolicy.KEEP_EXISTING)
    
    def test_determine_policy_replace_semantic_change(self):
        """replace 操作（意味変更あり）のポリシー決定テスト"""
        operation = {
            "operation": "replace",
            "is_minor_change": False,
            "old_lines": ["old text"],
            "new_lines": ["completely different text"]
        }
        
        # LLM が意味変更ありと判定
        self.applicator.semantic_detector.has_semantic_change.return_value = True
        
        policy = self.applicator.determine_policy(operation)
        
        self.assertEqual(policy, ChangePolicy.RETRANSLATE)
    
    def test_determine_policy_replace_no_semantic_change(self):
        """replace 操作（意味変更なし）のポリシー決定テスト"""
        operation = {
            "operation": "replace",
            "is_minor_change": False,
            "old_lines": ["old text"],
            "new_lines": ["old text with minor formatting"]
        }
        
        # LLM が意味変更なしと判定
        self.applicator.semantic_detector.has_semantic_change.return_value = False
        
        policy = self.applicator.determine_policy(operation)
        
        self.assertEqual(policy, ChangePolicy.KEEP_EXISTING)
    
    def test_apply_operation_keep_existing(self):
        """keep_existing ポリシーの適用テスト"""
        operation = {
            "operation": "equal",
            "old_start": 0,
            "old_end": 2,
            "new_lines": ["line1", "line2"]
        }
        
        existing_translation = ["translated line1", "translated line2", "translated line3"]
        
        result_lines, reason = self.applicator.apply_operation(
            operation, existing_translation, ChangePolicy.KEEP_EXISTING
        )
        
        # 変更されないことを確認
        self.assertEqual(result_lines, existing_translation)
        self.assertIn("既訳を維持", reason)
    
    def test_apply_operation_new_translation(self):
        """new_translation ポリシーの適用テスト"""
        operation = {
            "operation": "insert",
            "old_start": 1,
            "old_end": 1,
            "new_lines": ["New line to translate"]
        }
        
        existing_translation = ["line1", "line2"]
        
        result_lines, reason = self.applicator.apply_operation(
            operation, existing_translation, ChangePolicy.NEW_TRANSLATION
        )
        
        # 新しい行が挿入されることを確認
        self.assertGreater(len(result_lines), len(existing_translation))
        self.assertIn("新規翻訳", reason)
    
    def test_apply_operation_delete(self):
        """delete ポリシーの適用テスト"""
        operation = {
            "operation": "delete",
            "old_start": 1,
            "old_end": 2,
            "new_lines": []
        }
        
        existing_translation = ["line1", "line to delete", "line3"]
        
        result_lines, reason = self.applicator.apply_operation(
            operation, existing_translation, ChangePolicy.DELETE
        )
        
        # 行が削除されることを確認
        self.assertLess(len(result_lines), len(existing_translation))
        self.assertIn("削除", reason)
    
    def test_apply_operation_retranslate(self):
        """retranslate ポリシーの適用テスト"""
        operation = {
            "operation": "replace",
            "old_start": 1,
            "old_end": 2,
            "new_lines": ["Updated content to retranslate"]
        }
        
        existing_translation = ["line1", "old translation", "line3"]
        
        result_lines, reason = self.applicator.apply_operation(
            operation, existing_translation, ChangePolicy.RETRANSLATE
        )
        
        # 翻訳が置換されることを確認
        self.assertEqual(len(result_lines), len(existing_translation))
        self.assertIn("[要翻訳]", result_lines[1])  # 翻訳マーカーが追加される
        self.assertIn("再翻訳", reason)
    
    def test_translate_lines(self):
        """行翻訳処理のテスト"""
        lines = ["Line to translate", "", "Another line"]
        
        translated = self.applicator._translate_lines(lines)
        
        # 翻訳マーカーが追加されることを確認
        self.assertEqual(len(translated), len(lines))
        self.assertIn("[要翻訳]", translated[0])
        self.assertEqual(translated[1], "")  # 空行はそのまま
        self.assertIn("[要翻訳]", translated[2])
    
    def test_apply_file_changes_success(self):
        """ファイル変更適用の成功テスト"""
        operations = [
            {
                "operation": "equal",
                "old_start": 0,
                "old_end": 1,
                "new_lines": ["unchanged line"]
            },
            {
                "operation": "insert",
                "old_start": 1,
                "old_end": 1,
                "new_lines": ["new line"]
            }
        ]
        
        existing_translation = "unchanged line\nexisting line"
        
        result = self.applicator.apply_file_changes("test.md", operations, existing_translation)
        
        self.assertIsInstance(result, ApplicationResult)
        self.assertTrue(result.applied)
        self.assertEqual(result.file_path, "test.md")
        self.assertIsNone(result.error)
    
    def test_apply_file_changes_error_handling(self):
        """ファイル変更適用のエラーハンドリングテスト"""
        # 不正な操作を渡してエラーを発生させる
        operations = [
            {
                "operation": "invalid_operation",  # 不正な操作
                "old_start": 0,
                "old_end": 1
            }
        ]
        
        # determine_policy でエラーが発生するようにモック
        self.applicator.determine_policy = MagicMock(side_effect=Exception("Test error"))
        
        result = self.applicator.apply_file_changes("test.md", operations)
        
        self.assertFalse(result.applied)
        self.assertIsNotNone(result.error)
        self.assertIn("Test error", result.error)
    
    def test_determine_overall_policy(self):
        """全体ポリシー決定のテスト"""
        # 優先度のテスト: RETRANSLATE > NEW_TRANSLATION > DELETE > KEEP_EXISTING
        
        # RETRANSLATE が含まれる場合
        policies = [ChangePolicy.KEEP_EXISTING, ChangePolicy.RETRANSLATE, ChangePolicy.DELETE]
        overall = self.applicator._determine_overall_policy(policies)
        self.assertEqual(overall, ChangePolicy.RETRANSLATE)
        
        # NEW_TRANSLATION が含まれる場合（RETRANSLATE なし）
        policies = [ChangePolicy.KEEP_EXISTING, ChangePolicy.NEW_TRANSLATION, ChangePolicy.DELETE]
        overall = self.applicator._determine_overall_policy(policies)
        self.assertEqual(overall, ChangePolicy.NEW_TRANSLATION)
        
        # DELETE のみの場合
        policies = [ChangePolicy.KEEP_EXISTING, ChangePolicy.DELETE]
        overall = self.applicator._determine_overall_policy(policies)
        self.assertEqual(overall, ChangePolicy.DELETE)
        
        # KEEP_EXISTING のみの場合
        policies = [ChangePolicy.KEEP_EXISTING]
        overall = self.applicator._determine_overall_policy(policies)
        self.assertEqual(overall, ChangePolicy.KEEP_EXISTING)
    
    def test_apply_changes_batch(self):
        """一括変更適用のテスト"""
        change_analysis = {
            "file_diffs": {
                "docs/file1.md": {
                    "operations": [
                        {
                            "operation": "equal",
                            "old_start": 0,
                            "old_end": 1,
                            "new_lines": ["line1"]
                        }
                    ]
                },
                "docs/file2.md": {
                    "operations": [
                        {
                            "operation": "insert",
                            "old_start": 0,
                            "old_end": 0,
                            "new_lines": ["new line"]
                        }
                    ]
                }
            }
        }
        
        results = self.applicator.apply_changes_batch(change_analysis)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(isinstance(r, ApplicationResult) for r in results))
    
    def test_generate_application_report(self):
        """適用レポート生成のテスト"""
        results = [
            ApplicationResult(
                file_path="file1.md",
                policy=ChangePolicy.KEEP_EXISTING,
                applied=True,
                reason="No changes needed",
                original_lines=[],
                translated_lines=[]
            ),
            ApplicationResult(
                file_path="file2.md",
                policy=ChangePolicy.NEW_TRANSLATION,
                applied=True,
                reason="New content added",
                original_lines=[],
                translated_lines=[]
            ),
            ApplicationResult(
                file_path="file3.md",
                policy=ChangePolicy.RETRANSLATE,
                applied=False,
                reason="Error occurred",
                original_lines=[],
                translated_lines=[],
                error="Mock error"
            )
        ]
        
        report = self.applicator.generate_application_report(results)
        
        self.assertIn("変更適用レポート", report)
        self.assertIn("処理ファイル数: 3", report)
        self.assertIn("成功: 2", report)
        self.assertIn("エラー: 1", report)
        self.assertIn("既訳維持: 1", report)
        self.assertIn("新規翻訳: 1", report)
        self.assertIn("再翻訳: 1", report)
        self.assertIn("file1.md", report)
        self.assertIn("file2.md", report)
        self.assertIn("file3.md", report)
        self.assertIn("Mock error", report)


class TestApplicationResult(unittest.TestCase):
    """ApplicationResult データクラスのテスト"""
    
    def test_application_result_creation(self):
        """ApplicationResult の作成テスト"""
        result = ApplicationResult(
            file_path="test.md",
            policy=ChangePolicy.NEW_TRANSLATION,
            applied=True,
            reason="Test reason",
            original_lines=["line1"],
            translated_lines=["translated line1"]
        )
        
        self.assertEqual(result.file_path, "test.md")
        self.assertEqual(result.policy, ChangePolicy.NEW_TRANSLATION)
        self.assertTrue(result.applied)
        self.assertEqual(result.reason, "Test reason")
        self.assertEqual(result.original_lines, ["line1"])
        self.assertEqual(result.translated_lines, ["translated line1"])
        self.assertIsNone(result.error)
    
    def test_application_result_with_error(self):
        """エラー付き ApplicationResult のテスト"""
        result = ApplicationResult(
            file_path="test.md",
            policy=ChangePolicy.KEEP_EXISTING,
            applied=False,
            reason="Error occurred",
            original_lines=[],
            translated_lines=[],
            error="Mock error message"
        )
        
        self.assertFalse(result.applied)
        self.assertEqual(result.error, "Mock error message")


class TestIntegrationScenarios(unittest.TestCase):
    """統合シナリオテスト"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.applicator = ChangeApplicator(self.temp_dir)
        
        # モックセットアップ
        self.applicator.semantic_detector = MagicMock()
        self.applicator.semantic_detector.has_semantic_change.return_value = False  # デフォルトは意味変更なし
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_comprehensive_change_application(self):
        """包括的な変更適用テスト（全パターン）"""
        # equal, insert, delete, replace のすべてを含む操作セット
        operations = [
            {
                "operation": "equal",
                "old_start": 0, "old_end": 1,
                "new_lines": ["# Title"],
                "is_minor_change": False
            },
            {
                "operation": "insert",
                "old_start": 1, "old_end": 1,
                "new_lines": ["New paragraph"],
                "is_minor_change": False
            },
            {
                "operation": "replace",
                "old_start": 1, "old_end": 2,
                "old_lines": ["Old content"],
                "new_lines": ["Updated content"],
                "is_minor_change": False  # 重要な変更
            },
            {
                "operation": "delete",
                "old_start": 2, "old_end": 3,
                "old_lines": ["Content to delete"],
                "new_lines": [],
                "is_minor_change": False
            },
            {
                "operation": "replace",
                "old_start": 3, "old_end": 4,
                "old_lines": ["Minor change content"],
                "new_lines": ["Minor change content!"],  # 軽微変更
                "is_minor_change": True
            }
        ]
        
        existing_translation = [
            "# タイトル",
            "古い内容",
            "削除される内容",
            "軽微変更内容"
        ]
        
        # 意味変更判定をセットアップ
        def mock_semantic_change(old_text, new_text):
            # "Updated content" への変更は意味変更あり
            return "Updated content" in new_text
        
        self.applicator.semantic_detector.has_semantic_change.side_effect = mock_semantic_change
        
        result = self.applicator.apply_file_changes("comprehensive_test.md", operations, "\n".join(existing_translation))
        
        # 結果検証
        self.assertTrue(result.applied)
        self.assertIsNone(result.error)
        
        # 適用されたポリシーの確認
        # 重要な変更（replace with semantic change）があるため、RETRANSLATE が全体ポリシーになるはず
        self.assertEqual(result.policy, ChangePolicy.RETRANSLATE)
    
    def test_minor_changes_only_scenario(self):
        """軽微変更のみのシナリオテスト"""
        operations = [
            {
                "operation": "replace",
                "old_start": 0, "old_end": 1,
                "old_lines": ["Hello, world."],
                "new_lines": ["Hello, world!"],  # 句読点のみ変更
                "is_minor_change": True
            },
            {
                "operation": "replace",
                "old_start": 1, "old_end": 2,
                "old_lines": ["Another sentence."],
                "new_lines": ["Another sentence"],  # 句読点削除
                "is_minor_change": True
            }
        ]
        
        existing_translation = ["こんにちは、世界。", "別の文。"]
        
        result = self.applicator.apply_file_changes("minor_changes.md", operations, "\n".join(existing_translation))
        
        # 軽微変更のみなので既訳維持
        self.assertEqual(result.policy, ChangePolicy.KEEP_EXISTING)
        self.assertTrue(result.applied)
    
    def test_line_correspondence_maintenance(self):
        """置換レンジ内での 1:1 行対応の維持テスト"""
        operations = [
            {
                "operation": "replace",
                "old_start": 1, "old_end": 3,  # 2行の置換
                "old_lines": ["Old line 1", "Old line 2"],
                "new_lines": ["New line 1", "New line 2"],  # 同じく2行
                "is_minor_change": False
            }
        ]
        
        existing_translation = ["Title", "古い行1", "古い行2", "Footer"]
        
        # 意味変更ありと判定
        self.applicator.semantic_detector.has_semantic_change.return_value = True
        
        result = self.applicator.apply_file_changes("line_correspondence.md", operations, "\n".join(existing_translation))
        
        # 行数が維持されることを確認
        original_line_count = len(existing_translation)
        final_line_count = len(result.translated_lines)
        
        self.assertEqual(original_line_count, final_line_count)
        self.assertEqual(result.policy, ChangePolicy.RETRANSLATE)


if __name__ == '__main__':
    unittest.main()