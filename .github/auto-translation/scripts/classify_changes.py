#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム
変更ファイル分類スクリプト
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def find_project_root() -> Path:
    """プロジェクトルートディレクトリを見つける"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / '.git').exists() or (current / 'package.json').exists():
            return current
        current = current.parent
    return Path.cwd()


class ChangeClassifier:
    def __init__(self, base_branch: str = "origin/main"):
        self.base_branch = base_branch
        self.project_root = find_project_root()
        self.translatable_extensions = {".md", ".mdx", ".adoc", ".html"}
        self.non_translatable_extensions = {
            ".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp",
            ".json", ".yml", ".yaml", ".toml", ".conf", 
            ".js", ".ts", ".tsx", ".css", ".scss", ".sass",
            ".py", ".lock"
        }
    
    def get_changed_files(self) -> List[Tuple[str, str]]:
        """変更されたファイルのリストを取得（ステータス付き）"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", f"{self.base_branch}..HEAD"],
                capture_output=True, text=True, check=True
            )
            
            files = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    status, filepath = parts
                    files.append((status, filepath))
            
            return files
            
        except subprocess.CalledProcessError as e:
            print(f"Error getting changed files: {e}")
            return []
    
    def has_conflict_markers(self, filepath: str) -> bool:
        """ファイルにコンフリクトマーカーが含まれているかチェック"""
        try:
            full_path = self.project_root / filepath
            if not full_path.exists():
                return False
                
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return any(marker in content for marker in ['<<<<<<<', '=======', '>>>>>>>'])
                
        except Exception as e:
            print(f"Error checking conflict markers in {filepath}: {e}")
            return False
    
    def is_translatable_file(self, filepath: str) -> bool:
        """ファイルが翻訳対象かどうか判定"""
        path = Path(filepath)
        
        # ルートディレクトリの '.' で始まるファイル・フォルダを除外
        if filepath.startswith('.'):
            return False
        
        # 拡張子チェック
        if path.suffix.lower() in self.translatable_extensions:
            return True
        
        # 特殊ケース: 拡張子なしのファイルでもマークダウンの可能性
        if not path.suffix and filepath not in ['LICENSE', 'NOTICE', 'CNAME']:
            try:
                full_path = self.project_root / filepath
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        first_line = f.readline().strip()
                        # マークダウンのヘッダーで始まるかチェック
                        if first_line.startswith('#') or first_line.startswith('---'):
                            return True
            except:
                pass
        
        return False
    
    def classify_file_change(self, status: str, filepath: str) -> str:
        """ファイル変更を分類"""
        # まず翻訳対象外ファイルをチェック
        if not self.is_translatable_file(filepath):
            return "c"  # 非文書／除外
        
        # 新規ファイル
        if status == "A":
            return "a"  # 新規文書
        
        # 変更されたファイル
        if status == "M":
            if self.has_conflict_markers(filepath):
                return "b-2"  # 衝突 (Conflict)
            else:
                return "b-1"  # 追記 (No conflict)
        
        # 削除されたファイル
        if status == "D":
            return "c"  # 除外扱い
        
        # その他のステータス（リネーム等）
        return "c"  # 除外扱い
    
    def classify_all_changes(self) -> Dict[str, List[str]]:
        """全ての変更ファイルを分類"""
        changed_files = self.get_changed_files()
        
        classification = {
            "a": [],      # 新規文書
            "b-1": [],    # 追記 (No conflict)
            "b-2": [],    # 衝突 (Conflict)
            "c": []       # 非文書／除外
        }
        
        file_details = []
        
        for status, filepath in changed_files:
            category = self.classify_file_change(status, filepath)
            classification[category].append(filepath)
            
            file_details.append({
                "path": filepath,
                "status": status,
                "category": category,
                "translatable": self.is_translatable_file(filepath),
                "has_conflicts": self.has_conflict_markers(filepath) if (self.project_root / filepath).exists() else False
            })
        
        return {
            "summary": classification,
            "details": file_details,
            "total_files": len(changed_files),
            "translatable_files": len([f for f in file_details if f["translatable"]])
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Classify changed files for translation")
    parser.add_argument(
        "--base-branch",
        default="origin/main",
        help="Base branch for comparison"
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "summary"],
        default="json",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    classifier = ChangeClassifier(args.base_branch)
    result = classifier.classify_all_changes()
    
    if args.output_format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("📋 ファイル変更分類結果:")
        print(f"   総ファイル数: {result['total_files']}")
        print(f"   翻訳対象ファイル数: {result['translatable_files']}")
        print()
        
        for category, files in result["summary"].items():
            if files:
                category_names = {
                    "a": "🆕 新規文書",
                    "b-1": "✏️ 追記 (No conflict)",
                    "b-2": "⚠️ 衝突 (Conflict)",
                    "c": "📄 非文書／除外"
                }
                print(f"{category_names.get(category, category)} ({len(files)} files):")
                for file in files[:5]:  # 最初の5ファイルのみ表示
                    print(f"   - {file}")
                if len(files) > 5:
                    print(f"   ... and {len(files) - 5} more files")
                print()


if __name__ == "__main__":
    main()