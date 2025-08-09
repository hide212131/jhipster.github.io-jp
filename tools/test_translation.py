#!/usr/bin/env python3
"""
Tests for the line-wise translator with placeholder protection.

This test module validates:
- Line count preservation (1 input line → 1 output line)
- Placeholder protection and restoration
- Code fence handling
- Table handling
- YAML frontmatter handling
"""

import unittest
import sys
import os

# Add the parent directory to the Python path to import tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.placeholder import PlaceholderManager, protect_line, restore_line
from tools.translate_linewise import LinewiseTranslator, ProcessingState


class TestPlaceholderManager(unittest.TestCase):
    """Test placeholder protection and restoration functionality."""
    
    def setUp(self):
        self.manager = PlaceholderManager()
    
    def test_inline_code_protection(self):
        """Test protection of inline code with backticks."""
        text = "Use `console.log()` for debugging"
        protected = self.manager.protect_content(text)
        restored = self.manager.restore_content(protected)
        
        self.assertNotEqual(text, protected)
        self.assertEqual(text, restored)
        self.assertIn("__PLACEHOLDER_", protected)
        self.assertEqual(self.manager.get_placeholder_count(), 1)
    
    def test_url_protection(self):
        """Test protection of URLs."""
        text = "Visit https://www.jhipster.tech/ for more info"
        protected = self.manager.protect_content(text)
        restored = self.manager.restore_content(protected)
        
        self.assertEqual(text, restored)
        self.assertIn("__PLACEHOLDER_", protected)
    
    def test_markdown_link_protection(self):
        """Test protection of markdown links."""
        text = "Check out [JHipster](https://www.jhipster.tech/) website"
        protected = self.manager.protect_content(text)
        restored = self.manager.restore_content(protected)
        
        self.assertEqual(text, restored)
        self.assertIn("__PLACEHOLDER_", protected)
    
    def test_jekyll_variables_protection(self):
        """Test protection of Jekyll variables and tags."""
        text = "URL: {{ site.url }} and {% include header.html %}"
        protected = self.manager.protect_content(text)
        restored = self.manager.restore_content(protected)
        
        self.assertEqual(text, restored)
        self.assertIn("__PLACEHOLDER_", protected)
        self.assertEqual(self.manager.get_placeholder_count(), 2)
    
    def test_mixed_content_protection(self):
        """Test protection of mixed special content."""
        text = "Use `code`, visit [site](http://example.com) and see {{ var }}"
        protected = self.manager.protect_content(text)
        restored = self.manager.restore_content(protected)
        
        self.assertEqual(text, restored)
        # Should have 3 placeholders: code, link, jekyll var
        self.assertEqual(self.manager.get_placeholder_count(), 3)
    
    def test_validation(self):
        """Test validation of restoration."""
        text = "Use `console.log()` for debugging"
        protected = self.manager.protect_content(text)
        restored = self.manager.restore_content(protected)
        
        is_valid, issues = self.manager.validate_restoration(text, restored)
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)


class TestLinewiseTranslator(unittest.TestCase):
    """Test line-wise translation functionality."""
    
    def setUp(self):
        self.translator = LinewiseTranslator()
    
    def test_line_count_preservation(self):
        """Test that output has same number of lines as input."""
        input_lines = [
            "---",
            "title: Test",
            "---",
            "",
            "# Header",
            "",
            "Paragraph",
            "",
            "```code",
            "content",
            "```",
            "",
            "Final line"
        ]
        
        output_lines = self.translator.translate_file_with_microbatch(input_lines)
        self.assertEqual(len(input_lines), len(output_lines))
    
    def test_yaml_frontmatter_preservation(self):
        """Test that YAML frontmatter is not translated."""
        input_lines = [
            "---",
            "layout: default",
            "title: Test Page",
            "---",
            "",
            "Content to translate"
        ]
        
        output_lines = self.translator.translate_file_with_microbatch(input_lines)
        
        # YAML frontmatter should be unchanged
        self.assertEqual(output_lines[0], "---")
        self.assertEqual(output_lines[1], "layout: default")
        self.assertEqual(output_lines[2], "title: Test Page")
        self.assertEqual(output_lines[3], "---")
        
        # Content should be translated
        self.assertIn("[TRANSLATED]", output_lines[5])
    
    def test_code_fence_preservation(self):
        """Test that code inside fences is not translated."""
        input_lines = [
            "Some text to translate",
            "",
            "```javascript",
            "console.log('hello world');",
            "var x = 42;",
            "```",
            "",
            "More text to translate"
        ]
        
        output_lines = self.translator.translate_file_with_microbatch(input_lines)
        
        # Text should be translated
        self.assertIn("[TRANSLATED]", output_lines[0])
        self.assertIn("[TRANSLATED]", output_lines[7])
        
        # Code fence and content should be unchanged
        self.assertEqual(output_lines[2], "```javascript")
        self.assertEqual(output_lines[3], "console.log('hello world');")
        self.assertEqual(output_lines[4], "var x = 42;")
        self.assertEqual(output_lines[5], "```")
    
    def test_table_preservation(self):
        """Test that markdown tables are not translated."""
        input_lines = [
            "Text before table",
            "",
            "| Column 1 | Column 2 |",
            "|----------|----------|",
            "| Data 1   | Data 2   |",
            "| Data 3   | Data 4   |",
            "",
            "Text after table"
        ]
        
        output_lines = self.translator.translate_file_with_microbatch(input_lines)
        
        # Text should be translated
        self.assertIn("[TRANSLATED]", output_lines[0])
        self.assertIn("[TRANSLATED]", output_lines[7])
        
        # Table should be unchanged
        self.assertEqual(output_lines[2], "| Column 1 | Column 2 |")
        self.assertEqual(output_lines[3], "|----------|----------|")
        self.assertEqual(output_lines[4], "| Data 1   | Data 2   |")
        self.assertEqual(output_lines[5], "| Data 3   | Data 4   |")
    
    def test_placeholder_preservation_in_translation(self):
        """Test that placeholders are properly restored after translation."""
        input_lines = [
            "Use `inline code` and visit [link](http://example.com) for info"
        ]
        
        output_lines = self.translator.translate_file_with_microbatch(input_lines)
        
        # Should contain the translation prefix
        self.assertIn("[TRANSLATED]", output_lines[0])
        # Should contain the original inline code
        self.assertIn("`inline code`", output_lines[0])
        # Should contain the original link
        self.assertIn("[link](http://example.com)", output_lines[0])
    
    def test_empty_line_preservation(self):
        """Test that empty lines are preserved."""
        input_lines = [
            "Line 1",
            "",
            "",
            "Line 4",
            ""
        ]
        
        output_lines = self.translator.translate_file_with_microbatch(input_lines)
        
        # Should have same number of lines
        self.assertEqual(len(output_lines), 5)
        # Empty lines should remain empty
        self.assertEqual(output_lines[1], "")
        self.assertEqual(output_lines[2], "")
        self.assertEqual(output_lines[4], "")
    
    def test_state_machine_reset(self):
        """Test that state machine resets properly between files."""
        # First file with code fence
        input_lines1 = [
            "```code",
            "content",
            "```"
        ]
        output_lines1 = self.translator.translate_file_with_microbatch(input_lines1)
        
        # Second file should start with normal state
        input_lines2 = [
            "Normal text to translate"
        ]
        output_lines2 = self.translator.translate_file_with_microbatch(input_lines2)
        
        # Second file should be translated (not affected by first file's state)
        self.assertIn("[TRANSLATED]", output_lines2[0])


class TestIntegration(unittest.TestCase):
    """Integration tests with real markdown content."""
    
    def test_real_markdown_file_structure(self):
        """Test with realistic markdown file structure."""
        markdown_content = """---
layout: default
title: エンティティの構築
permalink: /creating-an-entity/
---

# <i class="fa fa-bolt"></i> エンティティの構築

**重要** JavaScript/TypeScriptコードの「ライブリロード」を行いたい場合は、`npm start`または`yarn start`を実行する必要があります。

## はじめに

アプリケーションを作成したら、_エンティティ_ を作成します。例：

```bash
jhipster entity Author
jhipster entity Book
```

エンティティごとに、次の要素が必要です：

*   データベーステーブル
*   Liquibaseチェンジセット
*   JPAエンティティ

詳細については、[ドキュメント]({{ site.url }}/documentation/)を参照してください。

| オプション | 説明 |
|-----------|------|
| `--table-name` | テーブル名を指定 |
| `--skip-server` | サーバ側をスキップ |
""".strip().split('\n')
        
        translator = LinewiseTranslator()
        output_lines = translator.translate_file_with_microbatch(markdown_content)
        
        # Verify line count preservation
        self.assertEqual(len(markdown_content), len(output_lines))
        
        # Verify YAML frontmatter is preserved
        self.assertEqual(output_lines[0], "---")
        self.assertEqual(output_lines[4], "---")
        
        # Verify code blocks are preserved
        bash_line = next((i for i, line in enumerate(output_lines) if "```bash" in line), None)
        self.assertIsNotNone(bash_line)
        self.assertEqual(output_lines[bash_line + 1], "jhipster entity Author")
        
        # Verify Jekyll variables are preserved in translated content
        translated_doc_line = next((line for line in output_lines if "{{ site.url }}" in line), None)
        self.assertIsNotNone(translated_doc_line)
        
        # Verify table is preserved
        table_header = next((line for line in output_lines if "| オプション | 説明 |" in line), None)
        self.assertIsNotNone(table_header)


if __name__ == "__main__":
    unittest.main()