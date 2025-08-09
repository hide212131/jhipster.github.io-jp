#!/usr/bin/env python3
"""
行ロック翻訳器のテストケース
"""

import unittest
import sys
from pathlib import Path

# テスト対象モジュールをインポート
sys.path.append(str(Path(__file__).parent.parent))
from translate_linewise import LinewiseTranslator, CodeFenceDetector, FenceState


class TestCodeFenceDetector(unittest.TestCase):
    """コードフェンス検出器のテスト"""
    
    def setUp(self):
        """テストケースごとの初期化"""
        self.detector = CodeFenceDetector()
    
    def test_triple_backtick_fence(self):
        """三重バッククォートフェンスのテスト"""
        # フェンス開始
        state, changed = self.detector.process_line("```python")
        self.assertEqual(state, FenceState.INSIDE)
        self.assertTrue(changed)
        
        # フェンス内
        state, changed = self.detector.process_line("def hello():")
        self.assertEqual(state, FenceState.INSIDE)
        self.assertFalse(changed)
        
        # フェンス終了
        state, changed = self.detector.process_line("```")
        self.assertEqual(state, FenceState.OUTSIDE)
        self.assertTrue(changed)
    
    def test_triple_tilde_fence(self):
        """三重チルダフェンスのテスト"""
        state, changed = self.detector.process_line("~~~javascript")
        self.assertEqual(state, FenceState.INSIDE)
        self.assertTrue(changed)
        
        state, changed = self.detector.process_line("console.log('test');")
        self.assertEqual(state, FenceState.INSIDE)
        self.assertFalse(changed)
        
        state, changed = self.detector.process_line("~~~")
        self.assertEqual(state, FenceState.OUTSIDE)
        self.assertTrue(changed)
    
    def test_empty_lines_in_fence(self):
        """フェンス内の空行のテスト"""
        self.detector.process_line("```")
        
        # 空行
        state, changed = self.detector.process_line("")
        self.assertEqual(state, FenceState.INSIDE)
        self.assertFalse(changed)
        
        # スペースのみの行
        state, changed = self.detector.process_line("   ")
        self.assertEqual(state, FenceState.INSIDE)
        self.assertFalse(changed)
    
    def test_reset_functionality(self):
        """リセット機能のテスト"""
        self.detector.process_line("```")
        self.assertEqual(self.detector.state, FenceState.INSIDE)
        
        self.detector.reset()
        self.assertEqual(self.detector.state, FenceState.OUTSIDE)


class TestLinewiseTranslator(unittest.TestCase):
    """行ロック翻訳器のテスト"""
    
    def setUp(self):
        """テストケースごとの初期化"""
        self.translator = LinewiseTranslator(api_key="fake_api_key_for_testing")
    
    def test_line_count_preservation(self):
        """行数保持のテスト"""
        test_text = """# Header

Paragraph 1

Paragraph 2 with `code`

```python
# Code block
print("hello")
```

Final paragraph"""
        
        translated_text, results = self.translator.translate_text(test_text)
        
        original_lines = test_text.split('\n')
        translated_lines = translated_text.split('\n')
        
        # 行数が一致することを確認
        self.assertEqual(len(original_lines), len(translated_lines))
        
        # 結果オブジェクトの数も一致することを確認
        self.assertEqual(len(results), len(original_lines))
    
    def test_code_fence_preservation(self):
        """コードフェンス保護のテスト"""
        test_text = """Before code

```python
def hello():
    return "Hello, World!"
```

After code"""
        
        translated_text, results = self.translator.translate_text(test_text)
        
        # コードブロック内容が保持されることを確認
        self.assertIn('def hello():', translated_text)
        self.assertIn('return "Hello, World!"', translated_text)
        
        # フェンス内として認識された行を確認
        fence_lines = [r for r in results if r.was_in_fence]
        self.assertGreater(len(fence_lines), 0)
    
    def test_placeholder_protection_integration(self):
        """プレースホルダ保護統合テスト"""
        test_text = """# Document

Check [this link](https://example.com) and `inline code`.

| Col1 | Col2 |
|------|------|
| A    | B    |"""
        
        translated_text, results = self.translator.translate_text(test_text)
        
        # 保護された要素が復元されることを確認
        self.assertIn('[this link](https://example.com)', translated_text)
        self.assertIn('`inline code`', translated_text)
        self.assertIn('| Col1 | Col2 |', translated_text)
        
        # 保護された行を確認
        protected_lines = [r for r in results if r.was_protected]
        self.assertGreater(len(protected_lines), 0)
    
    def test_micro_batch_prompt_format(self):
        """マイクロバッチプロンプト形式のテスト"""
        lines = ["Line 1", "Line 2", "Line 3"]
        prompt = self.translator.create_micro_batch_prompt(lines, "TEST001")
        
        # L0001=... 形式が含まれることを確認
        self.assertIn("L0001=Line 1", prompt)
        self.assertIn("L0002=Line 2", prompt)
        self.assertIn("L0003=Line 3", prompt)
        self.assertIn("ID: TEST001", prompt)
    
    def test_batch_response_parsing(self):
        """バッチレスポンス解析のテスト"""
        response = """L0001=[MOCK翻訳]Line 1
L0002=[MOCK翻訳]Line 2
L0003=[MOCK翻訳]Line 3"""
        
        parsed = self.translator.parse_batch_response(response, 3)
        self.assertIsNotNone(parsed)
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[0], "[MOCK翻訳]Line 1")
        self.assertEqual(parsed[1], "[MOCK翻訳]Line 2")
        self.assertEqual(parsed[2], "[MOCK翻訳]Line 3")
    
    def test_batch_response_parsing_invalid(self):
        """無効なバッチレスポンス解析のテスト"""
        # 行数不一致
        response = """L0001=[MOCK翻訳]Line 1
L0002=[MOCK翻訳]Line 2"""
        
        parsed = self.translator.parse_batch_response(response, 3)
        self.assertIsNone(parsed)
        
        # 順序不正
        response = """L0002=[MOCK翻訳]Line 2
L0001=[MOCK翻訳]Line 1
L0003=[MOCK翻訳]Line 3"""
        
        parsed = self.translator.parse_batch_response(response, 3)
        self.assertIsNotNone(parsed)  # 順序は自動修正される
    
    def test_llm_output_normalization(self):
        """LLM出力正規化のテスト"""
        # 改行を含む出力
        output_with_newlines = "This is a\nmultiline\noutput"
        normalized = self.translator.normalize_llm_output(output_with_newlines)
        self.assertEqual(normalized, "This is a multiline output")
        
        # 複数スペース
        output_with_spaces = "This  has   multiple    spaces"
        normalized = self.translator.normalize_llm_output(output_with_spaces)
        self.assertEqual(normalized, "This has multiple spaces")
    
    def test_validation_functionality(self):
        """翻訳検証機能のテスト"""
        original = """# Header
Content with `code`
| Table | Header |
|-------|--------|"""
        
        # 正常な翻訳（行数一致）
        good_translation = """# ヘッダー
`code`を含むコンテンツ
| テーブル | ヘッダー |
|---------|----------|"""
        
        is_valid, errors = self.translator.validate_translation(original, good_translation)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # 異常な翻訳（行数不一致）
        bad_translation = """# ヘッダー
コンテンツ"""
        
        is_valid, errors = self.translator.validate_translation(original, bad_translation)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_empty_and_whitespace_lines(self):
        """空行と空白行のテスト"""
        test_text = """Line 1

Line 3
   
Line 5"""
        
        translated_text, results = self.translator.translate_text(test_text)
        
        original_lines = test_text.split('\n')
        translated_lines = translated_text.split('\n')
        
        # 行数保持
        self.assertEqual(len(original_lines), len(translated_lines))
        
        # 空行の位置保持（モック翻訳を考慮）
        for i, (orig, trans) in enumerate(zip(original_lines, translated_lines)):
            if not orig.strip():  # 元が空行なら
                # モック翻訳では完全には保持されないが、元が空白のみなら考慮
                if not orig:  # 完全な空行
                    self.assertFalse(trans.strip())  # 翻訳も空行
                # 空白のみの行はモック翻訳で特殊処理されるのでスキップ
    
    def test_complex_document_structure(self):
        """複雑な文書構造のテスト"""
        test_text = """# Main Title

Introduction paragraph with [link](https://example.com).

## Code Section

Here's some code:

```python
def process_data(data):
    # Process the data
    return data.upper()
```

## Table Section

| Feature | Status | Notes |
|---------|--------|-------|
| Auth    | ✅     | Done  |
| API     | 🚧     | WIP   |

## Footnotes

See reference[^1] for details.

[^1]: This is the detailed explanation."""
        
        translated_text, results = self.translator.translate_text(test_text)
        
        # 構造保持の確認
        self.assertIn('def process_data(data):', translated_text)  # コード保持
        self.assertIn('[link](https://example.com)', translated_text)  # リンク保持
        self.assertIn('| Feature | Status | Notes |', translated_text)  # テーブル保持
        self.assertIn('[^1]:', translated_text)  # 脚注保持
        
        # 行数一致
        original_lines = test_text.split('\n')
        translated_lines = translated_text.split('\n')
        self.assertEqual(len(original_lines), len(translated_lines))
        
        # 統計確認
        fence_lines = [r for r in results if r.was_in_fence]
        protected_lines = [r for r in results if r.was_protected]
        
        self.assertGreater(len(fence_lines), 0)  # フェンス行が存在
        self.assertGreater(len(protected_lines), 0)  # 保護行が存在


if __name__ == '__main__':
    unittest.main()