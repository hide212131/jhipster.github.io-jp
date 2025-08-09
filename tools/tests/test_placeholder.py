#!/usr/bin/env python3
"""
プレースホルダ保護システムのテストケース
"""

import unittest
import sys
from pathlib import Path

# テスト対象モジュールをインポート
sys.path.append(str(Path(__file__).parent.parent))
from placeholder import PlaceholderProtector


class TestPlaceholderProtector(unittest.TestCase):
    """プレースホルダ保護機能のテスト"""
    
    def setUp(self):
        """テストケースごとの初期化"""
        self.protector = PlaceholderProtector()
    
    def test_inline_code_protection(self):
        """インラインコード保護のテスト"""
        content = "This is `inline code` and `another code`."
        protected = self.protector.protect_inline_code(content)
        restored = self.protector.restore_all(protected)
        
        # 復元されることを確認
        self.assertEqual(content, restored)
        # プレースホルダーが作成されることを確認
        self.assertGreater(self.protector.get_placeholder_count(), 0)
        # 元のコードが保護されていることを確認
        self.assertNotIn('`', protected)
    
    def test_url_protection(self):
        """URL保護のテスト"""
        content = "Visit https://example.com and http://test.org/path?query=value"
        protected = self.protector.protect_urls(content)
        restored = self.protector.restore_all(protected)
        
        self.assertEqual(content, restored)
        self.assertGreater(self.protector.get_placeholder_count(), 0)
    
    def test_markdown_link_protection(self):
        """Markdownリンク保護のテスト"""
        content = "Check [this link](https://example.com) and [another](http://test.org)."
        protected = self.protector.protect_markdown_links(content)
        restored = self.protector.restore_all(protected)
        
        self.assertEqual(content, restored)
        self.assertGreater(self.protector.get_placeholder_count(), 0)
    
    def test_html_attributes_protection(self):
        """HTML属性値保護のテスト"""
        content = '<div class="test" id="example">content</div>'
        protected = self.protector.protect_html_attributes(content)
        restored = self.protector.restore_all(protected)
        
        self.assertEqual(content, restored)
        self.assertGreater(self.protector.get_placeholder_count(), 0)
    
    def test_footnote_protection(self):
        """脚注保護のテスト"""
        content = """Text with footnote[^1].

[^1]: Footnote definition."""
        protected = self.protector.protect_footnote_ids(content)
        restored = self.protector.restore_all(protected)
        
        self.assertEqual(content, restored)
        self.assertGreater(self.protector.get_placeholder_count(), 0)
    
    def test_table_separator_protection(self):
        """表区切り保護のテスト"""
        content = """| Column 1 | Column 2 |
|----------|----------|
| Cell A   | Cell B   |"""
        
        protected = self.protector.protect_table_separators(content)
        restored = self.protector.restore_all(protected)
        
        self.assertEqual(content, restored)
        self.assertGreater(self.protector.get_placeholder_count(), 0)
    
    def test_table_alignment_protection(self):
        """表アライメント保護のテスト"""
        content = """| Left | Center | Right |
|:-----|:------:|------:|
| A    | B      | C     |"""
        
        protected = self.protector.protect_table_separators(content)
        restored = self.protector.restore_all(protected)
        
        self.assertEqual(content, restored)
        # アライメント行が保護されることを確認
        self.assertIn('PLACEHOLDER_', protected)
    
    def test_trailing_spaces_protection(self):
        """行末スペース保護のテスト"""
        content = """Line with trailing spaces  
Should be preserved."""
        
        protected = self.protector.protect_trailing_spaces(content)
        restored = self.protector.restore_all(protected)
        
        self.assertEqual(content, restored)
        self.assertGreater(self.protector.get_placeholder_count(), 0)
    
    def test_complex_content_protection(self):
        """複合コンテンツ保護のテスト"""
        content = """# Test Document

This is a test with `inline code` and [link](https://example.com).

| Column 1 | Column 2 | Column 3 |
|:---------|:--------:|--------:|
| Left     | Center   | Right   |

See footnote[^1] for details.

[^1]: This is the footnote definition.

HTML element: <div class="test" id="example">content</div>

Line with trailing spaces  
Should be preserved."""
        
        protected = self.protector.protect_all(content)
        restored = self.protector.restore_all(protected)
        
        # 基本的な復元チェック
        self.assertEqual(content, restored)
        
        # 検証機能のテスト
        is_valid, errors = self.protector.validate_restoration(content, protected, restored)
        self.assertTrue(is_valid, f"Validation failed: {errors}")
    
    def test_line_count_preservation(self):
        """行数保持のテスト"""
        content = """Line 1
Line 2 with `code`
Line 3

Line 5 after empty line
[Link](https://example.com)"""
        
        protected = self.protector.protect_all(content)
        restored = self.protector.restore_all(protected)
        
        original_lines = content.split('\n')
        restored_lines = restored.split('\n')
        
        self.assertEqual(len(original_lines), len(restored_lines))
        self.assertEqual(content, restored)
    
    def test_nested_protection(self):
        """ネストした保護要素のテスト"""
        content = "Check this `code with [link](https://example.com)` example."
        
        protected = self.protector.protect_all(content)
        restored = self.protector.restore_all(content)
        
        # 完全復元を確認
        self.assertEqual(content, restored)
    
    def test_placeholder_uniqueness(self):
        """プレースホルダー一意性のテスト"""
        content1 = "`code1`"
        content2 = "`code2`"
        
        protected1 = self.protector.protect_inline_code(content1)
        protected2 = self.protector.protect_inline_code(content2)
        
        # 異なるプレースホルダーが生成されることを確認
        self.assertNotEqual(protected1, protected2)
        
        # 両方とも正しく復元されることを確認
        restored1 = self.protector.restore_all(protected1)
        restored2 = self.protector.restore_all(protected2)
        
        self.assertEqual(content1, restored1)
        self.assertEqual(content2, restored2)
    
    def test_edge_cases(self):
        """エッジケースのテスト"""
        # 空文字列
        empty = ""
        self.assertEqual(empty, self.protector.restore_all(self.protector.protect_all(empty)))
        
        # 単一行
        single_line = "Single line with `code`"
        protected = self.protector.protect_all(single_line)
        restored = self.protector.restore_all(protected)
        self.assertEqual(single_line, restored)
        
        # 保護対象なし
        no_protection = "Just plain text with nothing special"
        protected = self.protector.protect_all(no_protection)
        self.assertEqual(no_protection, protected)  # 変化なし


if __name__ == '__main__':
    unittest.main()