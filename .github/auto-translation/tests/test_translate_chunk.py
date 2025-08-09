#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム
翻訳機能テスト
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from translate_chunk import GeminiTranslator


class TestGeminiTranslator(unittest.TestCase):
    def setUp(self):
        # テスト用のダミーAPIキー
        self.api_key = "test_api_key"
        
        # Gemini APIの初期化をモック
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model:
            self.translator = GeminiTranslator(self.api_key)
            self.mock_model = mock_model.return_value
    
    def test_count_tokens_estimate(self):
        """トークン数概算のテスト"""
        # 英語テキスト
        english_text = "Hello world this is a test"
        tokens = self.translator.count_tokens_estimate(english_text)
        self.assertGreater(tokens, 0)
        
        # 日本語テキスト
        japanese_text = "これはテストです"
        tokens = self.translator.count_tokens_estimate(japanese_text)
        self.assertGreater(tokens, 0)
        
        # 混在テキスト
        mixed_text = "これはJHipsterのtest文書です"
        tokens = self.translator.count_tokens_estimate(mixed_text)
        self.assertGreater(tokens, 0)
    
    def test_split_content_by_paragraphs(self):
        """段落分割のテスト"""
        content = """# Title

This is the first paragraph.

This is the second paragraph.
It has multiple lines.

## Subtitle

Another paragraph here.

```code
// Code block should not be split
function test() {
    return true;
}
```

Final paragraph."""
        
        chunks = self.translator.split_content_by_paragraphs(content)
        
        # 少なくとも複数のチャンクに分割されることを確認
        self.assertGreater(len(chunks), 1)
        
        # 各チャンクが文字列であることを確認
        for chunk in chunks:
            self.assertIsInstance(chunk, str)
            self.assertGreater(len(chunk.strip()), 0)
    
    def test_create_translation_prompt(self):
        """翻訳プロンプト作成のテスト"""
        content = "This is a test document for JHipster."
        prompt = self.translator.create_translation_prompt(content)
        
        # プロンプトに必要な要素が含まれていることを確認
        self.assertIn("日本語に翻訳", prompt)
        self.assertIn("マークダウン形式", prompt)
        self.assertIn("常体", prompt)
        self.assertIn(content, prompt)
    
    def test_get_custom_style_guide_for_path(self):
        """カスタムスタイルガイド取得のテスト"""
        # docs/releases/ パスのテスト
        custom_guide = self.translator.get_custom_style_guide_for_path("docs/releases/2024-01-01-release.md")
        
        # カスタムスタイルガイドファイルが存在しない場合は空文字列
        # 実際の環境では異なる場合があるため、文字列であることのみ確認
        self.assertIsInstance(custom_guide, str)
        
        # 通常のdocsパスのテスト
        normal_guide = self.translator.get_custom_style_guide_for_path("docs/getting-started.md")
        self.assertEqual(normal_guide, "")  # カスタムスタイルガイドは適用されない
        
        # 非docsパスのテスト
        other_guide = self.translator.get_custom_style_guide_for_path("src/components/test.tsx")
        self.assertEqual(other_guide, "")  # カスタムスタイルガイドは適用されない
    
    def test_create_translation_prompt_with_custom_style_guide(self):
        """カスタムスタイルガイドを含む翻訳プロンプト作成のテスト"""
        content = "This is a release document for JHipster v8.7.0."
        file_path = "docs/releases/2024-01-01-release.md"
        
        # カスタムスタイルガイドのモック
        with patch.object(self.translator, 'get_custom_style_guide_for_path') as mock_custom_guide:
            mock_custom_guide.return_value = "## リリースノート専用スタイル\n- です・ます調を使用\n- 冒頭で「これはJHipster vXのリリースです」と明記"
            
            prompt = self.translator.create_translation_prompt(content, file_path)
            
            # カスタムスタイルガイドが含まれていることを確認
            self.assertIn("カスタムスタイルガイド", prompt)
            self.assertIn("リリースノート専用スタイル", prompt)
            self.assertIn("カスタムスタイルガイドを優先", prompt)
            self.assertIn(content, prompt)
            
            # get_custom_style_guide_for_pathが正しいパスで呼ばれたことを確認
            mock_custom_guide.assert_called_once_with(file_path)
    
    def test_create_conflict_translation_prompt_with_custom_style_guide(self):
        """カスタムスタイルガイドを含むコンフリクト翻訳プロンプト作成のテスト"""
        content = """<<<<<<< HEAD
これはJHipster v8.6.0のリリースノートです。
=======
This is JHipster v8.7.0 release notes.
>>>>>>> upstream/main"""
        file_path = "docs/releases/2024-01-01-release.md"
        
        # カスタムスタイルガイドのモック
        with patch.object(self.translator, 'get_custom_style_guide_for_path') as mock_custom_guide:
            mock_custom_guide.return_value = "## リリースノート専用スタイル\n- です・ます調を使用\n- 冒頭で「これはJHipster vXのリリースです」と明記"
            
            # 第1段階（翻訳）のテスト
            prompt_stage1 = self.translator.create_conflict_translation_prompt(content, "translate", file_path)
            
            # カスタムスタイルガイドが含まれていることを確認
            self.assertIn("カスタムスタイルガイド", prompt_stage1)
            self.assertIn("リリースノート専用スタイル", prompt_stage1)
            self.assertIn("第1段階", prompt_stage1)
            self.assertIn("新規英語内容を既存日本語のスタイル", prompt_stage1)
            
            # 第2段階（マージ）のテスト
            prompt_stage2 = self.translator.create_conflict_translation_prompt(content, "merge", file_path)
            
            # カスタムスタイルガイドが含まれていることを確認
            self.assertIn("カスタムスタイルガイド", prompt_stage2)
            self.assertIn("第2段階", prompt_stage2)
            self.assertIn("HEAD側を完全に削除", prompt_stage2)
            
            # get_custom_style_guide_for_pathが2回呼ばれたことを確認
            self.assertEqual(mock_custom_guide.call_count, 2)
    
    @patch.object(GeminiTranslator, 'translate_chunk')
    def test_translate_file(self, mock_translate_chunk):
        """ファイル翻訳のテスト"""
        # モックの設定 - 各チャンクで異なる翻訳を返す
        mock_translate_chunk.side_effect = ["# テスト文書", "これはテスト文書です。"]
        
        # テスト用の一時ファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Document\n\nThis is a test document.")
            test_file = f.name
        
        try:
            # 翻訳実行
            result = self.translator.translate_file(test_file)
            
            # 成功したことを確認
            self.assertTrue(result)
            
            # translate_chunkが呼ばれたことを確認
            mock_translate_chunk.assert_called()
            
            # ファイルが更新されたことを確認
            with open(test_file, 'r', encoding='utf-8') as f:
                translated_content = f.read()
            
            # 複数チャンクの翻訳結果が結合されていることを確認
            self.assertEqual(translated_content, "# テスト文書\n\nこれはテスト文書です。")
            
        finally:
            os.unlink(test_file)
    
    @patch.object(GeminiTranslator, 'translate_file')
    def test_translate_files_from_classification(self, mock_translate_file):
        """分類結果からの翻訳のテスト"""
        # モックの設定
        mock_translate_file.return_value = True
        
        # 分類結果のテストデータ
        classification_data = {
            "summary": {
                "a": ["docs/new.md"],
                "b-1": ["docs/updated.md"],
                "b-2": ["docs/conflict.md"],
                "c": ["package.json"]
            }
        }
        
        # 一時ファイルに分類結果を保存
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(classification_data, f)
            classification_file = f.name
        
        try:
            # selective modeでテスト
            result = self.translator.translate_files_from_classification(
                classification_file, mode="selective"
            )
            
            # 成功したことを確認
            self.assertTrue(result)
            
            # 期待されるファイル数が翻訳されたことを確認
            # selective mode: a + b-1 = 2ファイル
            self.assertEqual(mock_translate_file.call_count, 2)
            
        finally:
            os.unlink(classification_file)


class TestGeminiTranslatorIntegration(unittest.TestCase):
    """統合テスト（実際のAPI呼び出しなし）"""
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_translation_workflow(self, mock_model_class, mock_configure):
        """翻訳ワークフロー全体のテスト"""
        # APIレスポンスをモック
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "これはJHipsterのテスト文書である。"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        translator = GeminiTranslator("test_api_key")
        
        # テスト用コンテンツ
        test_content = "This is a JHipster test document."
        
        # 翻訳実行
        result = translator.translate_chunk(test_content)
        
        # 結果確認
        self.assertEqual(result, "これはJHipsterのテスト文書である。")
        
        # APIが正しく呼ばれたことを確認
        mock_configure.assert_called_once_with(api_key="test_api_key")
        mock_model.generate_content.assert_called_once()
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_translation_workflow_with_custom_style_guide(self, mock_model_class, mock_configure):
        """カスタムスタイルガイドを含む翻訳ワークフロー全体のテスト"""
        # APIレスポンスをモック
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "これはJHipster v8.7.0のリリースです。\n\n主な変更点は以下の通りです。"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        translator = GeminiTranslator("test_api_key")
        
        # リリースノート用のテストコンテンツ
        test_content = "This is JHipster v8.7.0 release.\n\nHere are the main changes."
        file_path = "docs/releases/2024-01-01-release.md"
        
        # カスタムスタイルガイドのモック
        with patch.object(translator, 'get_custom_style_guide_for_path') as mock_custom_guide:
            mock_custom_guide.return_value = "## リリースノート専用スタイル\n- です・ます調を使用"
            
            # 翻訳実行
            result = translator.translate_chunk(test_content, file_path)
            
            # 結果確認
            self.assertEqual(result, "これはJHipster v8.7.0のリリースです。\n\n主な変更点は以下の通りです。")
            
            # カスタムスタイルガイドが取得されたことを確認
            mock_custom_guide.assert_called_once_with(file_path)
            
            # APIが正しく呼ばれたことを確認
            mock_configure.assert_called_once_with(api_key="test_api_key")
            mock_model.generate_content.assert_called_once()
            
            # プロンプトにカスタムスタイルガイドが含まれていることを確認
            call_args = mock_model.generate_content.call_args[0][0]
            self.assertIn("カスタムスタイルガイド", call_args)
            self.assertIn("リリースノート専用スタイル", call_args)


if __name__ == '__main__':
    unittest.main()