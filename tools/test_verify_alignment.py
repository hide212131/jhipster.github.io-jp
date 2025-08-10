#!/usr/bin/env python3
"""Comprehensive tests for verify_alignment.py functionality."""

import pytest
import tempfile
import os
from pathlib import Path
from verify_alignment import AlignmentVerifier


class TestVerifyAlignment:
    """Test cases for alignment verification."""
    
    def setup_method(self):
        """Set up test environment."""
        self.verifier = AlignmentVerifier()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str) -> str:
        """Create a test file with given content."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def test_perfect_alignment(self):
        """Test case where original and translated files are perfectly aligned."""
        original_content = """# Getting Started

This is a sample document.

## Installation

1. Download the software
2. Run the installer
3. Follow the setup wizard

```bash
npm install
```

| Feature | Status |
|---------|--------|
| Basic   | ✓      |
| Advanced| ✗      |

> Note: This is important.

End of document.  
"""
        
        translated_content = """# はじめに

これはサンプルドキュメントです。

## インストール

1. ソフトウェアをダウンロード
2. インストーラーを実行
3. セットアップウィザードに従う

```bash
npm install
```

| 機能    | 状態   |
|---------|--------|
| 基本    | ✓      |
| 高度    | ✗      |

> 注意: これは重要です。

ドキュメントの終わり。  
"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        assert result["line_count_match"] == True
        assert result["structure_match"] == True
        assert result["code_fence_match"] == True
        assert result["table_match"] == True
        assert result["trailing_spaces_match"] == True
        assert len(result["issues"]) == 0
        
    def test_line_count_mismatch(self):
        """Test case where line counts don't match."""
        original_content = """Line 1
Line 2
Line 3"""
        
        translated_content = """ライン 1
ライン 2
ライン 3
ライン 4"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        assert result["line_count_match"] == False
        assert len(result["issues"]) > 0
        assert "Line count mismatch" in result["issues"][0]
        
    def test_heading_level_mismatch(self):
        """Test case where heading levels don't match."""
        original_content = """# Main Title
## Subtitle
### Subsubtitle"""
        
        translated_content = """# メインタイトル
# サブタイトル
### サブサブタイトル"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        assert result["structure_match"] == False
        assert any("Heading level mismatch" in issue for issue in result["issues"])
        
    def test_missing_heading_marker(self):
        """Test case where heading marker is missing."""
        original_content = """# Title
Some content
## Subtitle"""
        
        translated_content = """タイトル
コンテンツ
## サブタイトル"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        assert result["structure_match"] == False
        assert any("Missing heading marker" in issue for issue in result["issues"])
        
    def test_list_indentation_mismatch(self):
        """Test case where list indentation doesn't match."""
        original_content = """1. First item
   - Sub item
   - Another sub item
2. Second item"""
        
        translated_content = """1. 最初の項目
- サブ項目
- 別のサブ項目
2. 二番目の項目"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        assert result["structure_match"] == False
        assert any("List indentation mismatch" in issue for issue in result["issues"])
        
    def test_code_fence_mismatch(self):
        """Test case where code fences don't match."""
        original_content = """Some text

```javascript
console.log("Hello");
```

More text

```bash
echo "test"
```"""
        
        translated_content = """テキスト

```javascript
console.log("Hello");
```

さらにテキスト

```python
print("test")
```"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        assert result["code_fence_match"] == False
        assert any("Code fence content mismatch" in issue for issue in result["issues"])
        
    def test_code_fence_position_mismatch(self):
        """Test case where code fence positions don't match."""
        original_content = """Some text
```bash
echo "hello"
```
More text"""
        
        translated_content = """テキスト

```bash
echo "hello"
```
さらにテキスト"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        assert result["code_fence_match"] == False
        assert any("Code fence position mismatch" in issue for issue in result["issues"])
        
    def test_table_column_mismatch(self):
        """Test case where table column counts don't match."""
        original_content = """| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |"""
        
        translated_content = """| 列 1 | 列 2 |
|------|------|
| データ1 | データ2 |"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        assert result["table_match"] == False
        assert any("Table column count mismatch" in issue for issue in result["issues"])
        
    def test_table_alignment_row_mismatch(self):
        """Test case where table alignment rows don't match."""
        original_content = """| Column 1 | Column 2 |
|:---------|:--------:|
| Left     | Center   |"""
        
        translated_content = """| 列 1 | 列 2 |
| 左 | 中央 |
| 左       | 中央     |"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        assert result["table_match"] == False
        assert any("Table alignment row mismatch" in issue for issue in result["issues"])
        
    def test_trailing_spaces_mismatch(self):
        """Test case where trailing spaces (markdown line breaks) don't match."""
        original_content = """Line with trailing spaces  
Next line
Line without trailing spaces"""
        
        translated_content = """末尾スペースのある行
次の行  
末尾スペースのない行"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        assert result["trailing_spaces_match"] == False
        assert any("Missing trailing spaces" in issue for issue in result["issues"])
        assert any("Unexpected trailing spaces" in issue for issue in result["issues"])
        
    def test_blockquote_mismatch(self):
        """Test case where blockquote markers don't match."""
        original_content = """> This is a quote
Normal text
> Another quote"""
        
        translated_content = """これは引用
Normal text
> もう一つの引用"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        assert result["structure_match"] == False
        assert any("Blockquote mismatch" in issue for issue in result["issues"])
        
    def test_complex_failure_case(self):
        """Test case with multiple types of failures."""
        original_content = """# Title

## Subtitle

1. Item 1
2. Item 2  
   - Sub item

```javascript
console.log("test");
```

| Col1 | Col2 |
|------|------|
| A    | B    |

> Quote

End."""
        
        translated_content = """タイトル

### サブタイトル

1. 項目1
2. 項目2
   - サブ項目

```python
print("test")
```

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |

Quote

End.
Extra line."""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        # Should have multiple types of failures
        assert result["line_count_match"] == False
        assert result["structure_match"] == False
        assert result["code_fence_match"] == False
        assert result["table_match"] == False
        assert result["trailing_spaces_match"] == False
        assert len(result["issues"]) > 5  # Multiple issues
        
    def test_statistics_collection(self):
        """Test that statistics are collected correctly."""
        original_content = """# Title

Text content.

```bash
echo "test"
```

| Col1 | Col2 |
|------|------|
| A    | B    |

Line with trailing spaces  

More content."""
        
        translated_content = """# タイトル

テキストコンテンツ。

```bash
echo "test"
```

| 列1 | 列2 |
|-----|-----|
| A   | B   |

末尾スペースのある行  

さらにコンテンツ。"""
        
        original_file = self.create_test_file("original.md", original_content)
        translated_file = self.create_test_file("translated.md", translated_content)
        
        result = self.verifier.verify_file(original_file, translated_file)
        
        stats = result["statistics"]
        assert stats["original_lines"] == 15
        assert stats["translated_lines"] == 15
        assert stats["code_fences"] == 2  # Opening and closing fence
        assert stats["tables"] == 3  # Header, separator, data row
        assert stats["trailing_spaces"] == 1
        
    def test_file_not_found(self):
        """Test behavior when files don't exist."""
        result = self.verifier.verify_file("nonexistent.md", "also_nonexistent.md")
        
        assert len(result["issues"]) > 0
        assert any("Error reading files" in issue for issue in result["issues"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])