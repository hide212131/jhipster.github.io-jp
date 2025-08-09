#!/usr/bin/env python3
"""
PR本文生成器
変更ファイル一覧、戦略、行数差、基準SHAを漏れなく出力する
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def find_project_root() -> Path:
    """プロジェクトルートディレクトリを見つける"""
    current = Path(__file__).parent.parent  # tools/から上がる
    while current != current.parent:
        if (current / '.git').exists() or (current / 'package.json').exists():
            return current
        current = current.parent
    
    # フォールバック: 現在のディレクトリに.gitやpackage.jsonがあるかチェック
    cwd = Path.cwd()
    if (cwd / '.git').exists() or (cwd / 'package.json').exists():
        return cwd
    
    return cwd


class PRBodyGenerator:
    def __init__(self, base_branch: str = "origin/main", project_root: Optional[Path] = None):
        self.base_branch = base_branch
        self.project_root = project_root or find_project_root()
        self.translatable_extensions = {".md", ".mdx", ".adoc", ".html"}
        self.non_translatable_extensions = {
            ".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp",
            ".json", ".yml", ".yaml", ".toml", ".conf", 
            ".js", ".ts", ".tsx", ".css", ".scss", ".sass",
            ".py", ".lock"
        }
    
    def get_upstream_sha(self) -> Optional[str]:
        """基準となるupstream SHAを取得"""
        try:
            # upstream/mainから最新のコミットハッシュを取得
            result = subprocess.run(
                ["git", "rev-parse", "upstream/main"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()[:7]  # 短縮形
        except subprocess.CalledProcessError:
            try:
                # fallback: origin/mainを使用
                result = subprocess.run(
                    ["git", "rev-parse", f"{self.base_branch}"],
                    capture_output=True, text=True, check=True
                )
                return result.stdout.strip()[:7]
            except subprocess.CalledProcessError:
                return None
    
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
                lines = content.split('\n')
                
                # 行の先頭から始まる競合マーカーのみを検出（クォートされた文字列は除外）
                for line in lines:
                    stripped = line.strip()
                    # より確実な競合マーカー検出
                    if (stripped.startswith('<<<<<<<') or 
                        stripped.startswith('=======') or 
                        stripped.startswith('>>>>>>>')):
                        # さらに正確性を高めるため、長さもチェック
                        if (stripped.startswith('<<<<<<<') and len(stripped) >= 7) or \
                           (stripped.startswith('=======') and len(stripped) >= 7) or \
                           (stripped.startswith('>>>>>>>') and len(stripped) >= 7):
                            return True
                
                return False
                
        except Exception as e:
            print(f"Error checking conflict markers in {filepath}: {e}")
            return False
    
    def is_translatable_file(self, filepath: str) -> bool:
        """ファイルが翻訳対象かどうか判定"""
        path = Path(filepath)
        
        # ルートディレクトリの '.' で始まるファイル・フォルダを除外
        if filepath.startswith('.'):
            return False
        
        # ルート直下のファイルを除外（サブディレクトリ内のファイルのみ翻訳対象）
        if '/' not in filepath:
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
    
    def get_line_count(self, filepath: str) -> int:
        """ファイルの行数を取得"""
        try:
            full_path = self.project_root / filepath
            if not full_path.exists():
                return 0
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                return len(lines)
        except Exception:
            return 0
    
    def get_line_count_diff(self, filepath: str) -> Tuple[int, int, int]:
        """行数差を取得 (現在の行数, ベース行数, 差分)"""
        current_lines = self.get_line_count(filepath)
        
        try:
            # ベースブランチでの行数を取得
            result = subprocess.run(
                ["git", "show", f"{self.base_branch}:{filepath}"],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode == 0:
                base_lines = len(result.stdout.splitlines())
            else:
                base_lines = 0  # 新規ファイル
            
            diff = current_lines - base_lines
            return current_lines, base_lines, diff
            
        except Exception:
            return current_lines, 0, current_lines
    
    def determine_change_type(self, git_status: str, has_conflict: bool, is_translatable: bool) -> str:
        """変更種別を決定"""
        if git_status == "A":
            if is_translatable:
                return "insert"
            else:
                return "copy_only"
        elif git_status == "D":
            return "delete"
        elif git_status == "M":
            if has_conflict:
                return "replace"
            else:
                return "insert"
        else:
            return "copy_only"
    
    def determine_strategy(self, change_type: str, is_translatable: bool, has_conflict: bool) -> str:
        """戦略を決定"""
        if not is_translatable:
            return "keep"
        
        if change_type == "delete":
            return "delete"
        elif change_type == "insert":
            return "retranslate"
        elif change_type == "replace":
            if has_conflict:
                return "retranslate"
            else:
                return "retranslate"
        else:
            return "keep"
    
    def analyze_changes(self) -> List[Dict[str, any]]:
        """すべての変更を分析"""
        changed_files = self.get_changed_files()
        analysis_results = []
        
        for git_status, filepath in changed_files:
            is_translatable = self.is_translatable_file(filepath)
            has_conflict = self.has_conflict_markers(filepath)
            change_type = self.determine_change_type(git_status, has_conflict, is_translatable)
            strategy = self.determine_strategy(change_type, is_translatable, has_conflict)
            current_lines, base_lines, line_diff = self.get_line_count_diff(filepath)
            
            analysis_results.append({
                "filepath": filepath,
                "change_type": change_type,
                "strategy": strategy,
                "current_lines": current_lines,
                "base_lines": base_lines,
                "line_diff": line_diff,
                "is_translatable": is_translatable,
                "has_conflict": has_conflict,
                "git_status": git_status
            })
        
        return analysis_results
    
    def generate_pr_body_markdown(self, analysis_results: List[Dict[str, any]], upstream_sha: Optional[str]) -> str:
        """PR本文のMarkdownを生成"""
        if not analysis_results:
            return self._generate_empty_pr_body(upstream_sha)
        
        lines = []
        lines.append("# 変更ファイル一覧")
        lines.append("")
        
        if upstream_sha:
            lines.append(f"**基準upstream SHA:** `{upstream_sha}`")
            lines.append("")
        
        lines.append("| ファイル | 変更種別 | 戦略 | 行数変化 | 現在行数 | ベース行数 |")
        lines.append("|---------|---------|------|---------|---------|-----------|")
        
        for result in analysis_results:
            filepath = result["filepath"]
            change_type = result["change_type"]
            strategy = result["strategy"]
            line_diff = result["line_diff"]
            current_lines = result["current_lines"]
            base_lines = result["base_lines"]
            
            # 行数変化の表示
            if line_diff > 0:
                line_change_display = f"+{line_diff}"
            elif line_diff < 0:
                line_change_display = str(line_diff)
            else:
                line_change_display = "±0"
            
            lines.append(f"| `{filepath}` | {change_type} | {strategy} | {line_change_display} | {current_lines} | {base_lines} |")
        
        lines.append("")
        lines.append("## 凡例")
        lines.append("")
        lines.append("**変更種別:**")
        lines.append("- `insert`: 新規追加または更新（競合なし）")
        lines.append("- `replace`: 更新（競合あり）")
        lines.append("- `delete`: 削除")
        lines.append("- `copy_only`: コピーのみ（翻訳対象外）")
        lines.append("")
        lines.append("**戦略:**")
        lines.append("- `retranslate`: 再翻訳")
        lines.append("- `keep`: 維持（翻訳対象外）")
        lines.append("- `insert`: 新規挿入")
        lines.append("- `delete`: 削除")
        lines.append("")
        
        # 統計情報
        total_files = len(analysis_results)
        translatable_files = sum(1 for r in analysis_results if r["is_translatable"])
        conflict_files = sum(1 for r in analysis_results if r["has_conflict"])
        
        lines.append("## 統計")
        lines.append(f"- **総ファイル数:** {total_files}")
        lines.append(f"- **翻訳対象ファイル数:** {translatable_files}")
        lines.append(f"- **競合ファイル数:** {conflict_files}")
        
        return "\n".join(lines)
    
    def _generate_empty_pr_body(self, upstream_sha: Optional[str]) -> str:
        """変更がない場合の簡潔なPR本文を生成"""
        lines = []
        lines.append("# 変更ファイル一覧")
        lines.append("")
        
        if upstream_sha:
            lines.append(f"**基準upstream SHA:** `{upstream_sha}`")
            lines.append("")
        
        lines.append("変更されたファイルはありません。")
        lines.append("")
        
        return "\n".join(lines)
    
    def save_pr_body(self, content: str, output_path: Optional[str] = None) -> str:
        """PR本文をファイルに保存"""
        if not output_path:
            output_dir = self.project_root / "tools" / ".out"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "pr_body.md"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(output_path)
    
    def generate(self, output_path: Optional[str] = None) -> str:
        """PR本文を生成してファイルに保存"""
        upstream_sha = self.get_upstream_sha()
        analysis_results = self.analyze_changes()
        pr_body_content = self.generate_pr_body_markdown(analysis_results, upstream_sha)
        saved_path = self.save_pr_body(pr_body_content, output_path)
        
        return saved_path


def main():
    parser = argparse.ArgumentParser(description="PR本文生成器")
    parser.add_argument(
        "--base-branch",
        default="origin/main",
        help="比較対象のベースブランチ (default: origin/main)"
    )
    parser.add_argument(
        "--output",
        help="出力ファイルパス (default: tools/.out/pr_body.md)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="詳細出力"
    )
    
    args = parser.parse_args()
    
    try:
        generator = PRBodyGenerator(base_branch=args.base_branch)
        saved_path = generator.generate(output_path=args.output)
        
        print(f"✅ PR本文を生成しました: {saved_path}")
        
        if args.verbose:
            with open(saved_path, 'r', encoding='utf-8') as f:
                print("\n--- Generated Content ---")
                print(f.read())
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()