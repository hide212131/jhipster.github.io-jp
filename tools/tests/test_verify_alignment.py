#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム
整合検証テスト
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from verify_alignment import AlignmentVerifier


class TestAlignmentVerifier(unittest.TestCase):
    """整合検証器のテスト"""
    
    def setUp(self):
        self.verifier = AlignmentVerifier()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, relative_path: str, content: str) -> Path:
        """テスト用ファイルを作成"""
        file_path = self.temp_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_verify_line_count_success(self):
        """行数一致検証：正常系"""
        original_content = """# Test Document
        
Line 1
Line 2
Line 3
"""
        translated_content = """# テストドキュメント

行 1
行 2
行 3
"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_line_count(str(original_file), str(translated_file))
        self.assertTrue(result)
        self.assertEqual(len(self.verifier.errors), 0)
    
    def test_verify_line_count_mismatch(self):
        """行数一致検証：不一致"""
        original_content = """# Test Document
Line 1
Line 2
"""
        translated_content = """# テストドキュメント
行 1
行 2
追加行
"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_line_count(str(original_file), str(translated_file))
        self.assertFalse(result)
        self.assertEqual(len(self.verifier.errors), 1)
        self.assertEqual(self.verifier.errors[0]["type"], "LINE_COUNT_MISMATCH")
    
    def test_verify_line_count_non_target_extension(self):
        """行数一致検証：対象外拡張子はスキップ"""
        original_content = "line 1\nline 2"
        translated_content = "line 1\nline 2\nline 3"
        
        original_file = self.create_test_file("original.json", original_content)
        translated_file = self.create_test_file("translated.json", translated_content)
        
        result = self.verifier.verify_line_count(str(original_file), str(translated_file))
        self.assertTrue(result)  # 対象外なので検証をスキップ
        self.assertEqual(len(self.verifier.errors), 0)
    
    def test_verify_structure_success(self):
        """構成一致検証：正常系"""
        # 元ディレクトリ構造を作成
        original_dir = self.temp_path / "original"
        self.create_test_file("original/README.md", "# README")
        self.create_test_file("original/docs/guide.md", "# Guide")
        self.create_test_file("original/docs/images/logo.png", "fake image")
        (original_dir / "empty_dir").mkdir(parents=True, exist_ok=True)
        
        # 翻訳ディレクトリ構造を作成（同じ構造）
        translated_dir = self.temp_path / "translated"
        self.create_test_file("translated/README.md", "# README JA")
        self.create_test_file("translated/docs/guide.md", "# Guide JA")
        self.create_test_file("translated/docs/images/logo.png", "fake image")
        (translated_dir / "empty_dir").mkdir(parents=True, exist_ok=True)
        
        result = self.verifier.verify_structure(str(original_dir), str(translated_dir))
        self.assertTrue(result)
        self.assertEqual(len(self.verifier.errors), 0)
    
    def test_verify_structure_missing_file(self):
        """構成一致検証：ファイル不足"""
        # 元ディレクトリ構造を作成
        original_dir = self.temp_path / "original"
        self.create_test_file("original/README.md", "# README")
        self.create_test_file("original/docs/guide.md", "# Guide")
        
        # 翻訳ディレクトリ構造を作成（一部ファイルが不足）
        translated_dir = self.temp_path / "translated"
        self.create_test_file("translated/README.md", "# README JA")
        # docs/guide.md is missing
        
        result = self.verifier.verify_structure(str(original_dir), str(translated_dir))
        self.assertFalse(result)
        self.assertGreaterEqual(len(self.verifier.errors), 1)  # 少なくとも1つのエラー
        self.assertTrue(any(error["type"] == "STRUCTURE_MISSING" for error in self.verifier.errors))
    
    def test_verify_structure_extra_file(self):
        """構成一致検証：余分なファイル"""
        # 元ディレクトリ構造を作成
        original_dir = self.temp_path / "original"
        self.create_test_file("original/README.md", "# README")
        
        # 翻訳ディレクトリ構造を作成（余分なファイルあり）
        translated_dir = self.temp_path / "translated"
        self.create_test_file("translated/README.md", "# README JA")
        self.create_test_file("translated/extra.md", "# Extra")
        
        result = self.verifier.verify_structure(str(original_dir), str(translated_dir))
        self.assertFalse(result)
        self.assertEqual(len(self.verifier.errors), 1)
        self.assertEqual(self.verifier.errors[0]["type"], "STRUCTURE_EXTRA")
    
    def test_verify_fence_alignment_success(self):
        """フェンス整合検証：正常系"""
        original_content = """# Test Document

Some text here.

```python
def hello():
    print("Hello")
```

More text.

```javascript
console.log("Hello");
```
"""
        translated_content = """# テストドキュメント

テキストです。

```python
def hello():
    print("こんにちは")
```

さらにテキスト。

```javascript
console.log("こんにちは");
```
"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_fence_alignment(str(original_file), str(translated_file))
        self.assertTrue(result)
        self.assertEqual(len(self.verifier.errors), 0)
    
    def test_verify_fence_alignment_count_mismatch(self):
        """フェンス整合検証：フェンス数不一致"""
        original_content = """# Test

```python
print("hello")
```

```bash
echo "world"
```
"""
        translated_content = """# テスト

```python
print("こんにちは")
```
"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_fence_alignment(str(original_file), str(translated_file))
        self.assertFalse(result)
        self.assertEqual(len(self.verifier.errors), 1)
        self.assertEqual(self.verifier.errors[0]["type"], "FENCE_COUNT_MISMATCH")
    
    def test_verify_fence_alignment_position_mismatch(self):
        """フェンス整合検証：フェンス位置不一致"""
        original_content = """# Test
Line 1
```python
print("hello")
```
"""
        translated_content = """# テスト
```python
print("こんにちは")
```
"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_fence_alignment(str(original_file), str(translated_file))
        self.assertFalse(result)
        self.assertGreaterEqual(len(self.verifier.errors), 1)  # 少なくとも1つのエラー
        self.assertTrue(any(error["type"] == "FENCE_POSITION_MISMATCH" for error in self.verifier.errors))
    
    def test_verify_table_alignment_success(self):
        """表整合検証：正常系"""
        original_content = """# Test Document

| Name | Age | City |
|------|-----|------|
| John | 25  | NYC  |
| Jane | 30  | LA   |
"""
        translated_content = """# テストドキュメント

| 名前 | 年齢 | 都市 |
|------|-----|------|
| 太郎 | 25  | 東京 |
| 花子 | 30  | 大阪 |
"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_table_alignment(str(original_file), str(translated_file))
        self.assertTrue(result)
        self.assertEqual(len(self.verifier.errors), 0)
    
    def test_verify_table_alignment_count_mismatch(self):
        """表整合検証：表行数不一致"""
        original_content = """# Test

| Name | Age |
|------|-----|
| John | 25  |
| Jane | 30  |
"""
        translated_content = """# テスト

| 名前 | 年齢 |
|------|-----|
| 太郎 | 25  |
"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_table_alignment(str(original_file), str(translated_file))
        self.assertFalse(result)
        self.assertEqual(len(self.verifier.errors), 1)
        self.assertEqual(self.verifier.errors[0]["type"], "TABLE_COUNT_MISMATCH")
    
    def test_verify_table_alignment_pipe_mismatch(self):
        """表整合検証：パイプ数不一致"""
        original_content = """# Test

| Name | Age | City |
|------|-----|------|
| John | 25  | NYC  |
"""
        translated_content = """# テスト

| 名前 | 年齢 |
|------|-----|
| 太郎 | 25  |
"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_table_alignment(str(original_file), str(translated_file))
        self.assertFalse(result)
        # 3つの表行それぞれでパイプ数が異なるため、複数のエラー
        self.assertGreater(len(self.verifier.errors), 0)
        self.assertTrue(any(error["type"] == "TABLE_PIPE_MISMATCH" for error in self.verifier.errors))
    
    def test_verify_placeholder_integrity_success(self):
        """プレースホルダ検証：正常系"""
        original_content = """# Test Document

Welcome to {{site.name}}!

Use the ${variable} placeholder.

See <reference> for details.
"""
        translated_content = """# テストドキュメント

{{site.name}}へようこそ！

${variable}プレースホルダを使用してください。

詳細については<reference>を参照してください。
"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_placeholder_integrity(str(original_file), str(translated_file))
        self.assertTrue(result)
        self.assertEqual(len(self.verifier.errors), 0)
    
    def test_verify_placeholder_integrity_count_mismatch(self):
        """プレースホルダ検証：数不一致"""
        original_content = """Welcome to {{site.name}}!

Use {{config.version}} too."""
        translated_content = """{{site.name}}へようこそ！"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_placeholder_integrity(str(original_file), str(translated_file))
        self.assertFalse(result)
        self.assertGreaterEqual(len(self.verifier.errors), 1)
        self.assertTrue(any(error["type"] == "PLACEHOLDER_COUNT_MISMATCH" for error in self.verifier.errors))
    
    def test_verify_placeholder_integrity_content_mismatch(self):
        """プレースホルダ検証：内容不一致"""
        original_content = """Welcome to {{site.name}}!"""
        translated_content = """{{site.title}}へようこそ！"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_placeholder_integrity(str(original_file), str(translated_file))
        self.assertFalse(result)
        self.assertGreaterEqual(len(self.verifier.errors), 1)
        self.assertTrue(any(error["type"] == "PLACEHOLDER_CONTENT_MISMATCH" for error in self.verifier.errors))
        # 行番号が設定されていることを確認
        content_mismatch_errors = [e for e in self.verifier.errors if e["type"] == "PLACEHOLDER_CONTENT_MISMATCH"]
        self.assertTrue(all(e["line"] is not None for e in content_mismatch_errors))
    
    def test_verify_all_success(self):
        """全検証：正常系"""
        # 完全に一致するファイルペアを作成
        original_content = """# Test Document

Welcome to {{site.name}}!

```python
def test():
    pass
```

| Name | Age |
|------|-----|
| John | 25  |
"""
        translated_content = """# テストドキュメント

{{site.name}}へようこそ！

```python
def test():
    pass
```

| 名前 | 年齢 |
|------|-----|
| 太郎 | 25  |
"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_all(str(original_file), str(translated_file))
        self.assertTrue(result)
        self.assertEqual(len(self.verifier.errors), 0)
    
    def test_verify_all_multiple_errors(self):
        """全検証：複数エラー"""
        original_content = """# Test

{{placeholder}}

```python
code
```

| A | B |
|---|---|
"""
        translated_content = """# テスト
追加行
{{different}}

```python
code
```
別の追加行

| A |
|---|
"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_all(str(original_file), str(translated_file))
        self.assertFalse(result)
        # 複数の種類のエラーが検出されることを確認
        error_types = {error["type"] for error in self.verifier.errors}
        self.assertIn("LINE_COUNT_MISMATCH", error_types)
        # フェンス位置ずれ、テーブルずれ、プレースホルダ不一致のうちいずれかが検出される
        expected_error_types = {"FENCE_POSITION_MISMATCH", "TABLE_PIPE_MISMATCH", "PLACEHOLDER_CONTENT_MISMATCH"}
        self.assertTrue(len(error_types.intersection(expected_error_types)) >= 2)  # 少なくとも2種類のエラー


if __name__ == '__main__':
    unittest.main()