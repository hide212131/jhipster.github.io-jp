#!/usr/bin/env python3
"""
プレースホルダ保護システム
翻訳時に壊れやすい要素をプレースホルダで保護し、翻訳後に復元する機能を提供
"""

import re
import uuid
from typing import Dict, List, Tuple


class PlaceholderProtector:
    """プレースホルダ保護クラス"""
    
    def __init__(self):
        self.placeholders: Dict[str, str] = {}
        self.placeholder_counter = 0
    
    def _generate_placeholder(self) -> str:
        """一意なプレースホルダーを生成"""
        self.placeholder_counter += 1
        # UUID風の形式だが短く、改行を含まない
        return f"PLACEHOLDER_{self.placeholder_counter:04d}_{uuid.uuid4().hex[:8]}"
    
    def _protect_element(self, content: str, pattern: str, flags: int = 0) -> str:
        """指定されたパターンをプレースホルダで保護"""
        def replacer(match):
            placeholder = self._generate_placeholder()
            self.placeholders[placeholder] = match.group(0)
            return placeholder
        
        return re.sub(pattern, replacer, content, flags=flags)
    
    def protect_inline_code(self, content: str) -> str:
        """インラインコード（バッククォート）を保護"""
        # 単一バッククォート
        content = self._protect_element(content, r'`[^`\n]*`')
        # 二重バッククォート（ネストした場合）
        content = self._protect_element(content, r'``[^`\n]*``')
        return content
    
    def protect_urls(self, content: str) -> str:
        """URL（http/https）を保護"""
        url_pattern = r'https?://[^\s\)\]\}]+(?:\([^\s\)]*\))*[^\s\.\,\;\!\?\)\]\}]*'
        return self._protect_element(content, url_pattern)
    
    def protect_markdown_links(self, content: str) -> str:
        """Markdownリンクのurl部分を保護"""
        # [text](url) 形式全体を保護（URL部分だけでなくリンク全体）
        content = self._protect_element(content, r'\[([^\]]*)\]\(([^\)]+)\)')
        
        # 参照リンク：[text][ref]
        content = self._protect_element(content, r'\[([^\]]*)\]\[([^\]]+)\]')
        
        return content
    
    def protect_html_attributes(self, content: str) -> str:
        """HTML属性値を保護"""
        # HTML属性値：key="value" や key='value'
        content = self._protect_element(content, r'\w+="[^"]*"')
        content = self._protect_element(content, r"\w+='[^']*'")
        return content
    
    def protect_footnote_ids(self, content: str) -> str:
        """脚注ID（[^id]）を保護"""
        # 脚注参照：[^id]
        content = self._protect_element(content, r'\[\^[^\]]+\]')
        # 脚注定義：[^id]: 
        content = self._protect_element(content, r'^\[\^[^\]]+\]:', re.MULTILINE)
        return content
    
    def protect_table_separators(self, content: str) -> str:
        """表の区切り文字とアライメントを保護"""
        lines = content.split('\n')
        protected_lines = []
        
        for line in lines:
            # 表のヘッダー区切り行を検出（|:---:|, |---:|, |:---|, |---|）
            if self._is_table_separator_line(line):
                # 行全体を保護
                placeholder = self._generate_placeholder()
                self.placeholders[placeholder] = line
                protected_lines.append(placeholder)
            else:
                # 通常の行でも表の区切り文字（|）を保護
                if '|' in line and self._looks_like_table_row(line):
                    protected_line = self._protect_table_pipes(line)
                    protected_lines.append(protected_line)
                else:
                    protected_lines.append(line)
        
        return '\n'.join(protected_lines)
    
    def _is_table_separator_line(self, line: str) -> bool:
        """表のヘッダー区切り行かどうかを判定"""
        stripped = line.strip()
        if not stripped.startswith('|') or not stripped.endswith('|'):
            return False
        
        # |で分割して、各セルが区切り文字パターンか確認
        cells = stripped[1:-1].split('|')
        for cell in cells:
            cell = cell.strip()
            if not re.match(r'^:?-+:?$', cell):
                return False
        return True
    
    def _looks_like_table_row(self, line: str) -> bool:
        """表の行っぽいかどうかを判定"""
        stripped = line.strip()
        return (stripped.startswith('|') and stripped.endswith('|') and 
                stripped.count('|') >= 2)
    
    def _protect_table_pipes(self, line: str) -> str:
        """表の行の区切り文字（|）を保護"""
        # 先頭と末尾の|は保護
        if line.strip().startswith('|'):
            line = self._protect_element(line, r'^\s*\|', re.MULTILINE)
        if line.strip().endswith('|'):
            line = self._protect_element(line, r'\|\s*$', re.MULTILINE)
        
        # 中間の|も保護（ただし、コード内の|は除外）
        # 簡易的にバッククォートで囲まれていない|を保護
        parts = line.split('`')
        protected_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:  # バッククォート外
                part = self._protect_element(part, r'\|')
            protected_parts.append(part)
        
        return '`'.join(protected_parts)
    
    def protect_trailing_spaces(self, content: str) -> str:
        """行末の2スペース（改行マーカー）を保護"""
        return self._protect_element(content, r'  $', re.MULTILINE)
    
    def protect_all(self, content: str) -> str:
        """すべての保護要素を適用"""
        # 保護の順序は重要（重複を避けるため）
        content = self.protect_inline_code(content)
        content = self.protect_markdown_links(content)  # URLより先に処理
        content = self.protect_urls(content)
        content = self.protect_html_attributes(content)
        content = self.protect_footnote_ids(content)
        content = self.protect_table_separators(content)
        content = self.protect_trailing_spaces(content)
        return content
    
    def restore_all(self, content: str) -> str:
        """すべてのプレースホルダーを元の値に復元"""
        for placeholder, original in self.placeholders.items():
            content = content.replace(placeholder, original)
        return content
    
    def clear(self):
        """プレースホルダー辞書をクリア"""
        self.placeholders.clear()
        self.placeholder_counter = 0
    
    def get_placeholder_count(self) -> int:
        """現在のプレースホルダー数を取得"""
        return len(self.placeholders)
    
    def validate_restoration(self, original: str, protected: str, restored: str) -> Tuple[bool, List[str]]:
        """復元が正しく行われたかを検証"""
        errors = []
        
        # 基本的な長さチェック
        if len(original.split('\n')) != len(restored.split('\n')):
            errors.append(f"Line count mismatch: {len(original.split('\n'))} -> {len(restored.split('\n'))}")
        
        # プレースホルダーの残存チェック
        remaining_placeholders = re.findall(r'PLACEHOLDER_\d+_[a-f0-9]{8}', restored)
        if remaining_placeholders:
            errors.append(f"Unreplaced placeholders found: {remaining_placeholders}")
        
        # 重要な要素の確認（簡易的）
        original_urls = re.findall(r'https?://[^\s\)\]]+', original)
        restored_urls = re.findall(r'https?://[^\s\)\]]+', restored)
        if len(original_urls) != len(restored_urls):
            errors.append(f"URL count mismatch: {len(original_urls)} -> {len(restored_urls)}")
        
        return len(errors) == 0, errors


def main():
    """テスト用メイン関数"""
    protector = PlaceholderProtector()
    
    test_content = """# Test Document

This is a test with `inline code` and [link](https://example.com).

| Column 1 | Column 2 | Column 3 |
|:---------|:--------:|--------:|
| Left     | Center   | Right   |

See footnote[^1] for details.

[^1]: This is the footnote definition.

HTML element: <div class="test" id="example">content</div>

Line with trailing spaces  
Should be preserved.
"""
    
    print("Original content:")
    print(repr(test_content))
    print("\n" + "="*50 + "\n")
    
    protected = protector.protect_all(test_content)
    print("Protected content:")
    print(repr(protected))
    print("\n" + "="*50 + "\n")
    
    restored = protector.restore_all(protected)
    print("Restored content:")
    print(repr(restored))
    print("\n" + "="*50 + "\n")
    
    is_valid, errors = protector.validate_restoration(test_content, protected, restored)
    print(f"Validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    
    print(f"\nPlaceholder count: {protector.get_placeholder_count()}")


if __name__ == "__main__":
    main()