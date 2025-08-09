#!/usr/bin/env python3
"""
PR本文生成器のテスト
"""

import unittest
import tempfile
import os
import shutil
import subprocess
from pathlib import Path
import sys

# テスト対象をインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pr_body import PRBodyGenerator


class TestPRBodyGenerator(unittest.TestCase):
    
    def setUp(self):
        """テスト用の一時リポジトリを作成"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # package.jsonを作成してプロジェクトルートを明確にする
        Path('package.json').write_text('{"name": "test-repo"}')
        
        # Git リポジトリ初期化
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)
        
        # 初期コミット作成
        Path('README.md').write_text('# Test Repository')
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)
        
        # ベースブランチとして origin/main を設定
        subprocess.run(['git', 'branch', '-M', 'main'], check=True)
        
        self.generator = PRBodyGenerator(base_branch='HEAD~1', project_root=Path.cwd())
    
    def tearDown(self):
        """テスト環境のクリーンアップ"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def test_empty_changes(self):
        """変更がない場合のテスト"""
        analysis = self.generator.analyze_changes()
        self.assertEqual(len(analysis), 0)
        
        pr_body = self.generator.generate_pr_body_markdown(analysis, "abc1234")
        self.assertIn("変更されたファイルはありません", pr_body)
        self.assertIn("abc1234", pr_body)
    
    def test_new_translatable_file(self):
        """新規翻訳対象ファイルのテスト"""
        # 新規マークダウンファイル作成
        docs_dir = Path('docs')
        docs_dir.mkdir()
        (docs_dir / 'new-doc.md').write_text('# New Document\nContent here.')
        
        subprocess.run(['git', 'add', 'docs/new-doc.md'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Add new doc'], check=True)
        
        analysis = self.generator.analyze_changes()
        self.assertEqual(len(analysis), 1)
        
        result = analysis[0]
        self.assertEqual(result['filepath'], 'docs/new-doc.md')
        self.assertEqual(result['change_type'], 'insert')
        self.assertEqual(result['strategy'], 'retranslate')
        self.assertTrue(result['is_translatable'])
        self.assertFalse(result['has_conflict'])
        self.assertEqual(result['current_lines'], 2)
        self.assertEqual(result['base_lines'], 0)
        self.assertEqual(result['line_diff'], 2)
    
    def test_new_non_translatable_file(self):
        """新規非翻訳ファイルのテスト"""
        # 新規JSONファイル作成
        (Path('config.json')).write_text('{"test": true}')
        
        subprocess.run(['git', 'add', 'config.json'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Add config'], check=True)
        
        analysis = self.generator.analyze_changes()
        self.assertEqual(len(analysis), 1)
        
        result = analysis[0]
        self.assertEqual(result['filepath'], 'config.json')
        self.assertEqual(result['change_type'], 'copy_only')
        self.assertEqual(result['strategy'], 'keep')
        self.assertFalse(result['is_translatable'])
    
    def test_modified_file_with_conflict(self):
        """競合ありファイル変更のテスト"""
        # 初期ファイル作成
        docs_dir = Path('docs')
        docs_dir.mkdir()
        doc_file = docs_dir / 'existing.md'
        doc_file.write_text('# Existing\nOriginal content.')
        
        subprocess.run(['git', 'add', 'docs/existing.md'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Add existing doc'], check=True)
        
        # 競合マーカー付きで変更
        doc_file.write_text('''# Existing
<<<<<<< HEAD
Current content
=======
Merged content
>>>>>>> feature
Common content''')
        
        subprocess.run(['git', 'add', 'docs/existing.md'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Add conflict'], check=True)
        
        analysis = self.generator.analyze_changes()
        self.assertEqual(len(analysis), 1)
        
        result = analysis[0]
        self.assertEqual(result['filepath'], 'docs/existing.md')
        self.assertEqual(result['change_type'], 'replace')
        self.assertEqual(result['strategy'], 'retranslate')
        self.assertTrue(result['is_translatable'])
        self.assertTrue(result['has_conflict'])
    
    def test_deleted_file(self):
        """削除ファイルのテスト"""
        # 初期ファイル作成
        docs_dir = Path('docs')
        docs_dir.mkdir()
        doc_file = docs_dir / 'to-delete.md'
        doc_file.write_text('# To Delete\nWill be removed.')
        
        subprocess.run(['git', 'add', 'docs/to-delete.md'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Add file to delete'], check=True)
        
        # ファイル削除
        doc_file.unlink()
        subprocess.run(['git', 'add', 'docs/to-delete.md'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Delete file'], check=True)
        
        analysis = self.generator.analyze_changes()
        self.assertEqual(len(analysis), 1)
        
        result = analysis[0]
        self.assertEqual(result['filepath'], 'docs/to-delete.md')
        self.assertEqual(result['change_type'], 'delete')
        self.assertEqual(result['strategy'], 'delete')
        self.assertTrue(result['is_translatable'])
        self.assertEqual(result['current_lines'], 0)
        self.assertEqual(result['base_lines'], 2)
        self.assertEqual(result['line_diff'], -2)
    
    def test_pr_body_generation(self):
        """PR本文生成のテスト"""
        # 複数ファイルの変更を作成
        docs_dir = Path('docs')
        docs_dir.mkdir()
        
        # 翻訳対象ファイル
        (docs_dir / 'guide.md').write_text('# Guide\nNew guide content.')
        # 非翻訳ファイル
        Path('package.json').write_text('{"name": "test"}')
        
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Add multiple files'], check=True)
        
        analysis = self.generator.analyze_changes()
        pr_body = self.generator.generate_pr_body_markdown(analysis, "def5678")
        
        # 基本構造の確認
        self.assertIn("# 変更ファイル一覧", pr_body)
        self.assertIn("def5678", pr_body)
        self.assertIn("| ファイル | 変更種別 | 戦略", pr_body)
        self.assertIn("docs/guide.md", pr_body)
        self.assertIn("package.json", pr_body)
        self.assertIn("## 統計", pr_body)
        self.assertIn("総ファイル数:** 2", pr_body)
        self.assertIn("翻訳対象ファイル数:** 1", pr_body)
    
    def test_file_output(self):
        """ファイル出力のテスト"""
        output_path = self.generator.generate()
        
        self.assertTrue(Path(output_path).exists())
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("# 変更ファイル一覧", content)


if __name__ == '__main__':
    unittest.main()