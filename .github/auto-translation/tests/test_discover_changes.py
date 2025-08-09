#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム
変更検出テスト
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

from discover_changes import (
    TranslationMetaManager, UpstreamChangeDiscoverer
)


class TestTranslationMetaManager(unittest.TestCase):
    """TranslationMetaManager クラスのテスト"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.meta_manager = TranslationMetaManager(self.temp_dir)
    
    def tearDown(self):
        # テンポラリディレクトリのクリーンアップ
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_upstream_sha_no_file(self):
        """メタファイルが存在しない場合のテスト"""
        sha = self.meta_manager.get_upstream_sha()
        self.assertIsNone(sha)
    
    def test_set_and_get_upstream_sha(self):
        """upstream SHA の保存と取得のテスト"""
        test_sha = "abc1234567890"
        
        # SHA を保存
        self.meta_manager.set_upstream_sha(test_sha)
        
        # SHA を取得
        retrieved_sha = self.meta_manager.get_upstream_sha()
        self.assertEqual(retrieved_sha, test_sha)
    
    def test_set_upstream_sha_multiple_times(self):
        """複数回 SHA を更新するテスト"""
        first_sha = "abc1234567890"
        second_sha = "def0987654321"
        
        # 最初の SHA を保存
        self.meta_manager.set_upstream_sha(first_sha)
        self.assertEqual(self.meta_manager.get_upstream_sha(), first_sha)
        
        # SHA を更新
        self.meta_manager.set_upstream_sha(second_sha)
        self.assertEqual(self.meta_manager.get_upstream_sha(), second_sha)
    
    def test_invalid_json_handling(self):
        """不正な JSON ファイルの処理テスト"""
        # 不正な JSON ファイルを作成
        with open(self.meta_manager.meta_file, 'w') as f:
            f.write("invalid json content")
        
        # SHA 取得（エラーハンドリング）
        sha = self.meta_manager.get_upstream_sha()
        self.assertIsNone(sha)
        
        # 新しい SHA を設定（ファイル上書き）
        test_sha = "new123456"
        self.meta_manager.set_upstream_sha(test_sha)
        
        # 正常に取得できることを確認
        retrieved_sha = self.meta_manager.get_upstream_sha()
        self.assertEqual(retrieved_sha, test_sha)


class TestUpstreamChangeDiscoverer(unittest.TestCase):
    """UpstreamChangeDiscoverer クラスのテスト"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.discoverer = UpstreamChangeDiscoverer(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_is_translatable_file(self):
        """翻訳対象ファイル判定のテスト"""
        # 翻訳対象ファイル
        self.assertTrue(self.discoverer.is_translatable_file("docs/guide.md"))
        self.assertTrue(self.discoverer.is_translatable_file("pages/tutorial.mdx"))
        self.assertTrue(self.discoverer.is_translatable_file("help/manual.adoc"))
        self.assertTrue(self.discoverer.is_translatable_file("content/page.html"))
        
        # 翻訳対象外ファイル
        self.assertFalse(self.discoverer.is_translatable_file("package.json"))
        self.assertFalse(self.discoverer.is_translatable_file("image.png"))
        self.assertFalse(self.discoverer.is_translatable_file("style.css"))
        self.assertFalse(self.discoverer.is_translatable_file("script.js"))
        
        # ルート直下のファイル（翻訳対象外）
        self.assertFalse(self.discoverer.is_translatable_file("README.md"))
        self.assertFalse(self.discoverer.is_translatable_file("CHANGELOG.md"))
        
        # ドットで始まるファイル（翻訳対象外）
        self.assertFalse(self.discoverer.is_translatable_file(".gitignore"))
        self.assertFalse(self.discoverer.is_translatable_file(".github/workflows/test.yml"))
    
    @patch('subprocess.run')
    def test_setup_upstream_remote_new(self, mock_run):
        """新規 upstream リモート設定のテスト"""
        # get-url が失敗（リモートが存在しない）
        mock_run.side_effect = [
            MagicMock(returncode=1),  # git remote get-url upstream (失敗)
            MagicMock(returncode=0)   # git remote add upstream (成功)
        ]
        
        result = self.discoverer.setup_upstream_remote()
        
        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 2)
    
    @patch('subprocess.run')
    def test_setup_upstream_remote_existing(self, mock_run):
        """既存 upstream リモートの確認テスト"""
        # get-url が成功（リモートが既に存在）
        mock_run.return_value = MagicMock(returncode=0)
        
        result = self.discoverer.setup_upstream_remote()
        
        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 1)
    
    @patch('subprocess.run')
    def test_get_changed_files_between_shas(self, mock_run):
        """SHA間での変更ファイル取得のテスト"""
        mock_run.return_value = MagicMock(
            stdout="A\tdocs/new-file.md\nM\tdocs/existing-file.md\nD\tdocs/old-file.md\n",
            returncode=0
        )
        
        files = self.discoverer.get_changed_files_between_shas("abc123", "def456")
        
        expected = [
            ("A", "docs/new-file.md"),
            ("M", "docs/existing-file.md"),
            ("D", "docs/old-file.md")
        ]
        
        self.assertEqual(files, expected)
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_get_file_content_at_sha_exists(self, mock_run):
        """指定 SHA でのファイル内容取得テスト（ファイル存在）"""
        test_content = "# Test File\n\nThis is test content."
        mock_run.return_value = MagicMock(
            stdout=test_content,
            returncode=0
        )
        
        content = self.discoverer.get_file_content_at_sha("docs/test.md", "abc123")
        
        self.assertEqual(content, test_content)
    
    @patch('subprocess.run')
    def test_get_file_content_at_sha_not_exists(self, mock_run):
        """指定 SHA でのファイル内容取得テスト（ファイル不存在）"""
        mock_run.return_value = MagicMock(returncode=1)
        
        content = self.discoverer.get_file_content_at_sha("docs/nonexistent.md", "abc123")
        
        self.assertIsNone(content)
    
    @patch.object(UpstreamChangeDiscoverer, 'fetch_upstream')
    @patch.object(UpstreamChangeDiscoverer, 'get_current_upstream_sha')
    def test_discover_changes_initial(self, mock_get_sha, mock_fetch):
        """初回実行時の変更検出テスト"""
        mock_fetch.return_value = True
        mock_get_sha.return_value = "abc123456"
        
        # 初回実行（メタファイルなし）
        changes = self.discoverer.discover_changes()
        
        self.assertTrue(changes["is_initial"])
        self.assertEqual(changes["new_sha"], "abc123456")
        self.assertIsNone(changes["old_sha"])
        self.assertEqual(changes["changed_files"], [])
    
    @patch.object(UpstreamChangeDiscoverer, 'fetch_upstream')
    @patch.object(UpstreamChangeDiscoverer, 'get_current_upstream_sha')
    def test_discover_changes_no_change(self, mock_get_sha, mock_fetch):
        """変更なしの場合のテスト"""
        mock_fetch.return_value = True
        mock_get_sha.return_value = "same123456"
        
        # 前回と同じ SHA を設定
        self.discoverer.meta_manager.set_upstream_sha("same123456")
        
        changes = self.discoverer.discover_changes()
        
        self.assertFalse(changes["is_initial"])
        self.assertTrue(changes.get("no_changes", False))
        self.assertEqual(changes["old_sha"], "same123456")
        self.assertEqual(changes["new_sha"], "same123456")
    
    @patch.object(UpstreamChangeDiscoverer, 'fetch_upstream')
    @patch.object(UpstreamChangeDiscoverer, 'get_current_upstream_sha')
    @patch.object(UpstreamChangeDiscoverer, 'get_changed_files_between_shas')
    @patch.object(UpstreamChangeDiscoverer, '_analyze_file_diff')
    def test_discover_changes_with_files(self, mock_analyze, mock_get_files, mock_get_sha, mock_fetch):
        """ファイル変更ありの場合のテスト"""
        mock_fetch.return_value = True
        mock_get_sha.return_value = "new123456"
        mock_get_files.return_value = [
            ("A", "docs/new-guide.md"),
            ("M", "docs/existing.md"),
            ("M", "package.json")  # 翻訳対象外
        ]
        mock_analyze.return_value = {
            "status": "M",
            "operations": [],
            "summary": {"total_operations": 1},
            "has_significant_changes": False
        }
        
        # 前回の SHA を設定
        self.discoverer.meta_manager.set_upstream_sha("old123456")
        
        changes = self.discoverer.discover_changes()
        
        self.assertFalse(changes["is_initial"])
        self.assertEqual(changes["old_sha"], "old123456")
        self.assertEqual(changes["new_sha"], "new123456")
        
        # 翻訳対象ファイルのみが含まれることを確認
        changed_files = changes["changed_files"]
        self.assertEqual(len(changed_files), 2)  # package.json は除外
        self.assertIn(("A", "docs/new-guide.md"), changed_files)
        self.assertIn(("M", "docs/existing.md"), changed_files)
    
    def test_serialize_operation(self):
        """LineOperation シリアライズのテスト"""
        from line_diff import LineOperation, OperationType
        
        operation = LineOperation(
            operation=OperationType.REPLACE,
            old_start=1, old_end=2,
            new_start=1, new_end=2,
            old_lines=["old content"],
            new_lines=["new content"]
        )
        
        serialized = self.discoverer._serialize_operation(operation)
        
        expected_keys = [
            "operation", "old_start", "old_end", "new_start", "new_end",
            "old_lines", "new_lines", "similarity_ratio", "is_minor_change"
        ]
        
        for key in expected_keys:
            self.assertIn(key, serialized)
        
        self.assertEqual(serialized["operation"], "replace")
        self.assertEqual(serialized["old_lines"], ["old content"])
        self.assertEqual(serialized["new_lines"], ["new content"])
    
    def test_generate_summary(self):
        """要約生成のテスト"""
        file_diffs = {
            "docs/file1.md": {
                "has_significant_changes": True,
                "operations": [
                    {"operation": "equal"},
                    {"operation": "replace", "is_minor_change": False}
                ]
            },
            "docs/file2.md": {
                "has_significant_changes": False,
                "operations": [
                    {"operation": "replace", "is_minor_change": True}
                ]
            }
        }
        
        summary = self.discoverer._generate_summary(file_diffs)
        
        self.assertEqual(summary["total_files"], 2)
        self.assertEqual(summary["significant_changes"], 1)
        self.assertEqual(summary["minor_changes"], 1)
        
        op_counts = summary["operation_counts"]
        self.assertEqual(op_counts["equal"], 1)
        self.assertEqual(op_counts["replace"], 2)
        self.assertEqual(op_counts["minor_replace"], 1)


class TestDiscoverChangesIntegration(unittest.TestCase):
    """discover_changes.py の統合テスト"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        # Git リポジトリのセットアップ（モック用）
        self.addCleanup(self._cleanup)
    
    def _cleanup(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_full_workflow_with_mocks(self, mock_run):
        """モックを使用した完全ワークフローテスト"""
        # Git コマンドの応答をセットアップ
        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', [])
            
            if cmd[:3] == ["git", "remote", "get-url"]:
                return MagicMock(returncode=1)  # リモートが存在しない
            elif cmd[:3] == ["git", "remote", "add"]:
                return MagicMock(returncode=0)  # リモート追加成功
            elif cmd[:2] == ["git", "fetch"]:
                return MagicMock(returncode=0)  # fetch成功
            elif cmd[:2] == ["git", "rev-parse"]:
                return MagicMock(returncode=0, stdout="new123456789\n")
            elif cmd[:3] == ["git", "diff", "--name-status"]:
                return MagicMock(returncode=0, stdout="M\tdocs/changed.md\nA\tdocs/new.md\n")
            elif cmd[:2] == ["git", "show"]:
                show_arg = cmd[2]
                if "old123456789:docs/changed.md" in show_arg:
                    return MagicMock(returncode=0, stdout="Old content\nSecond line")
                elif "new123456789:docs/changed.md" in show_arg:
                    return MagicMock(returncode=0, stdout="New content\nSecond line")
                elif "new123456789:docs/new.md" in show_arg:
                    return MagicMock(returncode=0, stdout="Completely new file content")
                else:
                    return MagicMock(returncode=1)  # ファイル不存在
            
            return MagicMock(returncode=0)
        
        mock_run.side_effect = mock_run_side_effect
        
        # テスト実行
        discoverer = UpstreamChangeDiscoverer(self.temp_dir)
        
        # 前回の SHA を設定
        discoverer.meta_manager.set_upstream_sha("old123456789")
        
        changes = discoverer.discover_changes()
        
        # 結果検証
        self.assertFalse(changes["is_initial"])
        self.assertEqual(changes["old_sha"], "old123456789")
        self.assertEqual(changes["new_sha"], "new123456789")
        self.assertEqual(len(changes["changed_files"]), 2)
        
        # ファイル差分の検証
        file_diffs = changes["file_diffs"]
        self.assertIn("docs/changed.md", file_diffs)
        self.assertIn("docs/new.md", file_diffs)
        
        # 変更ファイルの操作確認
        changed_diff = file_diffs["docs/changed.md"]
        self.assertEqual(changed_diff["status"], "M")
        self.assertIn("operations", changed_diff)


if __name__ == '__main__':
    unittest.main()