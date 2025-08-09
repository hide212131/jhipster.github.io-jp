#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム
整合検証スクリプト

同期結果の整合性を機械的に検証し、逸脱時には非ゼロ終了させる検証器
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def find_project_root() -> Path:
    """プロジェクトルートディレクトリを見つける"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / '.git').exists() or (current / 'package.json').exists():
            return current
        current = current.parent
    return Path.cwd()


class AlignmentVerifier:
    """整合検証器"""
    
    def __init__(self):
        self.project_root = find_project_root()
        self.target_extensions = {".md", ".mdx", ".adoc", ".html"}
        self.errors = []
        
    def log_error(self, error_type: str, file_path: str, line_number: Optional[int] = None, message: str = ""):
        """エラーログを記録"""
        error_entry = {
            "type": error_type,
            "file": file_path,
            "line": line_number,
            "message": message
        }
        self.errors.append(error_entry)
        
        if line_number is not None:
            print(f"❌ {error_type}: {file_path}:{line_number} - {message}", file=sys.stderr)
        else:
            print(f"❌ {error_type}: {file_path} - {message}", file=sys.stderr)
    
    def verify_line_count(self, original_file: str, translated_file: str) -> bool:
        """行数一致検証（対象拡張子のみ）"""
        original_path = Path(original_file)
        translated_path = Path(translated_file)
        
        # 対象拡張子チェック
        if original_path.suffix not in self.target_extensions:
            return True  # 対象外ファイルは検証しない
            
        if not original_path.exists():
            self.log_error("FILE_MISSING", original_file, message="Original file not found")
            return False
            
        if not translated_path.exists():
            self.log_error("FILE_MISSING", translated_file, message="Translated file not found")
            return False
        
        try:
            with open(original_path, 'r', encoding='utf-8') as f:
                original_lines = len(f.readlines())
                
            with open(translated_path, 'r', encoding='utf-8') as f:
                translated_lines = len(f.readlines())
                
            if original_lines != translated_lines:
                self.log_error(
                    "LINE_COUNT_MISMATCH", 
                    translated_file,
                    message=f"Line count mismatch: original={original_lines}, translated={translated_lines}"
                )
                return False
                
        except Exception as e:
            self.log_error("FILE_READ_ERROR", original_file, message=str(e))
            return False
            
        return True
    
    def verify_structure(self, original_dir: str, translated_dir: str) -> bool:
        """構成一致検証（ファイル/ディレクトリ/種別）"""
        original_path = Path(original_dir)
        translated_path = Path(translated_dir)
        
        if not original_path.exists():
            self.log_error("DIRECTORY_MISSING", original_dir, message="Original directory not found")
            return False
            
        if not translated_path.exists():
            self.log_error("DIRECTORY_MISSING", translated_dir, message="Translated directory not found")
            return False
        
        success = True
        
        # 元ディレクトリのファイル/ディレクトリ構造を取得
        original_items = set()
        for item in original_path.rglob('*'):
            relative_path = item.relative_to(original_path)
            item_type = 'dir' if item.is_dir() else 'file'
            original_items.add((str(relative_path), item_type))
        
        # 翻訳ディレクトリのファイル/ディレクトリ構造を取得
        translated_items = set()
        for item in translated_path.rglob('*'):
            relative_path = item.relative_to(translated_path)
            item_type = 'dir' if item.is_dir() else 'file'
            translated_items.add((str(relative_path), item_type))
        
        # 不足ファイル/ディレクトリの検出
        missing_items = original_items - translated_items
        for relative_path, item_type in missing_items:
            full_path = translated_path / relative_path
            self.log_error(
                "STRUCTURE_MISSING",
                str(full_path),
                message=f"Missing {item_type}: {relative_path}"
            )
            success = False
        
        # 余分なファイル/ディレクトリの検出
        extra_items = translated_items - original_items
        for relative_path, item_type in extra_items:
            full_path = translated_path / relative_path
            self.log_error(
                "STRUCTURE_EXTRA",
                str(full_path),
                message=f"Extra {item_type}: {relative_path}"
            )
            success = False
        
        return success
    
    def verify_fence_alignment(self, original_file: str, translated_file: str) -> bool:
        """フェンス開始/終了行の位置一致検証"""
        original_path = Path(original_file)
        translated_path = Path(translated_file)
        
        # 対象拡張子チェック
        if original_path.suffix not in self.target_extensions:
            return True
            
        if not original_path.exists() or not translated_path.exists():
            return True  # ファイル存在チェックは他の検証で行う
        
        try:
            with open(original_path, 'r', encoding='utf-8') as f:
                original_content = f.readlines()
                
            with open(translated_path, 'r', encoding='utf-8') as f:
                translated_content = f.readlines()
        except Exception as e:
            self.log_error("FILE_READ_ERROR", original_file, message=str(e))
            return False
        
        # コードフェンスの開始/終了行を抽出
        fence_pattern = re.compile(r'^```')
        
        original_fences = []
        for i, line in enumerate(original_content, 1):
            if fence_pattern.match(line.strip()):
                original_fences.append(i)
        
        translated_fences = []
        for i, line in enumerate(translated_content, 1):
            if fence_pattern.match(line.strip()):
                translated_fences.append(i)
        
        if len(original_fences) != len(translated_fences):
            self.log_error(
                "FENCE_COUNT_MISMATCH",
                translated_file,
                message=f"Fence count mismatch: original={len(original_fences)}, translated={len(translated_fences)}"
            )
            return False
        
        # 各フェンスの位置をチェック
        success = True
        for i, (orig_line, trans_line) in enumerate(zip(original_fences, translated_fences)):
            if orig_line != trans_line:
                self.log_error(
                    "FENCE_POSITION_MISMATCH",
                    translated_file,
                    line_number=trans_line,
                    message=f"Fence #{i+1} position mismatch: original line {orig_line}, translated line {trans_line}"
                )
                success = False
        
        return success
    
    def verify_table_alignment(self, original_file: str, translated_file: str) -> bool:
        """表のパイプ数/アライメント一致検証"""
        original_path = Path(original_file)
        translated_path = Path(translated_file)
        
        # 対象拡張子チェック
        if original_path.suffix not in self.target_extensions:
            return True
            
        if not original_path.exists() or not translated_path.exists():
            return True  # ファイル存在チェックは他の検証で行う
        
        try:
            with open(original_path, 'r', encoding='utf-8') as f:
                original_content = f.readlines()
                
            with open(translated_path, 'r', encoding='utf-8') as f:
                translated_content = f.readlines()
        except Exception as e:
            self.log_error("FILE_READ_ERROR", original_file, message=str(e))
            return False
        
        # 表の行を検出（パイプ文字を含む行）
        table_pattern = re.compile(r'^\s*\|.*\|\s*$')
        
        original_tables = []
        for i, line in enumerate(original_content, 1):
            if table_pattern.match(line):
                pipe_count = line.count('|')
                original_tables.append((i, pipe_count))
        
        translated_tables = []
        for i, line in enumerate(translated_content, 1):
            if table_pattern.match(line):
                pipe_count = line.count('|')
                translated_tables.append((i, pipe_count))
        
        if len(original_tables) != len(translated_tables):
            self.log_error(
                "TABLE_COUNT_MISMATCH",
                translated_file,
                message=f"Table row count mismatch: original={len(original_tables)}, translated={len(translated_tables)}"
            )
            return False
        
        # 各表行のパイプ数をチェック
        success = True
        for i, ((orig_line, orig_pipes), (trans_line, trans_pipes)) in enumerate(zip(original_tables, translated_tables)):
            if orig_pipes != trans_pipes:
                self.log_error(
                    "TABLE_PIPE_MISMATCH",
                    translated_file,
                    line_number=trans_line,
                    message=f"Table row #{i+1} pipe count mismatch: original={orig_pipes}, translated={trans_pipes}"
                )
                success = False
        
        return success
    
    def verify_placeholder_integrity(self, original_file: str, translated_file: str) -> bool:
        """プレースホルダ破損検知"""
        original_path = Path(original_file)
        translated_path = Path(translated_file)
        
        # 対象拡張子チェック
        if original_path.suffix not in self.target_extensions:
            return True
            
        if not original_path.exists() or not translated_path.exists():
            return True  # ファイル存在チェックは他の検証で行う
        
        try:
            with open(original_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            with open(translated_path, 'r', encoding='utf-8') as f:
                translated_content = f.read()
        except Exception as e:
            self.log_error("FILE_READ_ERROR", original_file, message=str(e))
            return False
        
        # 一般的なプレースホルダパターンを定義（重複しないように優先順位付け）
        placeholder_patterns = [
            r'\{\{[^}]+\}\}',  # {{ placeholder }} (最優先)
            r'\$\{[^}]+\}',    # ${placeholder}
            r'%[^%]+%',        # %placeholder%
            r'<[a-zA-Z][^>]*>',  # <placeholder> (HTMLタグ風だが、文字で始まるもの)
        ]
        
        success = True
        
        # 使用済み位置を追跡して重複を避ける
        original_used_positions = set()
        translated_used_positions = set()
        
        for pattern in placeholder_patterns:
            original_matches = list(re.finditer(pattern, original_content))
            translated_matches = list(re.finditer(pattern, translated_content))
            
            # 既に他のパターンでマッチした位置を除外
            original_matches = [m for m in original_matches if not any(pos in original_used_positions for pos in range(m.start(), m.end()))]
            translated_matches = [m for m in translated_matches if not any(pos in translated_used_positions for pos in range(m.start(), m.end()))]
            
            # 使用済み位置を更新
            for match in original_matches:
                original_used_positions.update(range(match.start(), match.end()))
            for match in translated_matches:
                translated_used_positions.update(range(match.start(), match.end()))
            
            # プレースホルダの数をチェック
            if len(original_matches) != len(translated_matches):
                self.log_error(
                    "PLACEHOLDER_COUNT_MISMATCH",
                    translated_file,
                    message=f"Placeholder count mismatch for pattern '{pattern}': original={len(original_matches)}, translated={len(translated_matches)}"
                )
                success = False
                continue
            
            # 各プレースホルダの内容をチェック
            for orig_match, trans_match in zip(original_matches, translated_matches):
                if orig_match.group() != trans_match.group():
                    # 行番号を計算
                    line_number = translated_content[:trans_match.start()].count('\n') + 1
                    self.log_error(
                        "PLACEHOLDER_CONTENT_MISMATCH",
                        translated_file,
                        line_number=line_number,
                        message=f"Placeholder content mismatch: original='{orig_match.group()}', translated='{trans_match.group()}'"
                    )
                    success = False
        
        return success
    
    def verify_all(self, original_path: str, translated_path: str) -> bool:
        """全検証を実行"""
        success = True
        
        print("🔍 Starting alignment verification...")
        
        # ディレクトリかファイルかを判定
        original = Path(original_path)
        translated = Path(translated_path)
        
        if original.is_dir() and translated.is_dir():
            # ディレクトリ間の検証
            print(f"📁 Verifying directory structure: {original_path} vs {translated_path}")
            
            # 構成一致検証
            if not self.verify_structure(original_path, translated_path):
                success = False
            
            # 各ファイルの詳細検証
            for original_file in original.rglob('*'):
                if original_file.is_file():
                    relative_path = original_file.relative_to(original)
                    translated_file = translated / relative_path
                    
                    if translated_file.exists():
                        print(f"📄 Verifying file: {relative_path}")
                        
                        if not self.verify_line_count(str(original_file), str(translated_file)):
                            success = False
                        if not self.verify_fence_alignment(str(original_file), str(translated_file)):
                            success = False
                        if not self.verify_table_alignment(str(original_file), str(translated_file)):
                            success = False
                        if not self.verify_placeholder_integrity(str(original_file), str(translated_file)):
                            success = False
        
        elif original.is_file() and translated.is_file():
            # ファイル間の検証
            print(f"📄 Verifying single file: {original_path} vs {translated_path}")
            
            if not self.verify_line_count(original_path, translated_path):
                success = False
            if not self.verify_fence_alignment(original_path, translated_path):
                success = False
            if not self.verify_table_alignment(original_path, translated_path):
                success = False
            if not self.verify_placeholder_integrity(original_path, translated_path):
                success = False
        
        else:
            self.log_error("PATH_TYPE_MISMATCH", original_path, message="Original and translated paths must both be files or both be directories")
            success = False
        
        # 結果サマリー
        if success:
            print("✅ All alignment verifications passed!")
        else:
            print(f"\n❌ Alignment verification failed with {len(self.errors)} errors:")
            for error in self.errors:
                if error['line']:
                    print(f"  - {error['type']}: {error['file']}:{error['line']} - {error['message']}")
                else:
                    print(f"  - {error['type']}: {error['file']} - {error['message']}")
        
        return success


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="整合検証：行数一致/構成一致/フェンス整合/表整合")
    parser.add_argument("original", help="元ファイルまたはディレクトリのパス")
    parser.add_argument("translated", help="翻訳後ファイルまたはディレクトリのパス")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細出力")
    
    args = parser.parse_args()
    
    verifier = AlignmentVerifier()
    success = verifier.verify_all(args.original, args.translated)
    
    if not success:
        sys.exit(1)  # 非ゼロ終了
    
    sys.exit(0)


if __name__ == "__main__":
    main()