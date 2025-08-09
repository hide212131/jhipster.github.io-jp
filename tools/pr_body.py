#!/usr/bin/env python3
"""
PR本文生成ツール
自動PR作成時に各ファイルの変更内容・戦略・行数差・基準SHAを表形式で記載するPR本文を生成
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Tuple


class PRBodyGenerator:
    """PR本文生成クラス"""
    
    def __init__(self, base_sha: str = None):
        self.base_sha = base_sha or self._get_base_sha()
        self.output_dir = Path(__file__).parent / ".out"
        self.output_file = self.output_dir / "pr_body.md"
        
    def _get_base_sha(self) -> str:
        """基準SHAを取得"""
        try:
            # デフォルトブランチとの比較用のSHAを取得
            result = subprocess.run(
                ["git", "merge-base", "HEAD", "origin/main"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            try:
                # main ブランチが存在しない場合はmasterを試す
                result = subprocess.run(
                    ["git", "merge-base", "HEAD", "origin/master"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError:
                # フォールバック: 直前のコミット
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD~1"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
    
    def _get_changed_files(self) -> List[str]:
        """変更されたファイルのリストを取得"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", self.base_sha, "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            return [f.strip() for f in result.stdout.split('\n') if f.strip()]
        except subprocess.CalledProcessError:
            return []
    
    def _get_file_stats(self, file_path: str) -> Tuple[int, int]:
        """ファイルの追加行数・削除行数を取得"""
        try:
            result = subprocess.run(
                ["git", "diff", "--numstat", self.base_sha, "HEAD", "--", file_path],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                parts = result.stdout.strip().split('\t')
                added = int(parts[0]) if parts[0] != '-' else 0
                deleted = int(parts[1]) if parts[1] != '-' else 0
                return added, deleted
        except (subprocess.CalledProcessError, ValueError, IndexError):
            pass
        return 0, 0
    
    def _determine_strategy(self, file_path: str, added: int, deleted: int) -> str:
        """変更戦略を判定"""
        if not os.path.exists(file_path):
            return "削除"
        
        # 基準SHAでファイルが存在していたかチェック
        try:
            subprocess.run(
                ["git", "cat-file", "-e", f"{self.base_sha}:{file_path}"],
                capture_output=True,
                check=True
            )
            file_existed = True
        except subprocess.CalledProcessError:
            file_existed = False
        
        if not file_existed:
            return "新規作成"
        elif added == 0 and deleted > 0:
            return "削除のみ"
        elif added > 0 and deleted == 0:
            return "追加のみ"
        elif added > deleted * 2:
            return "大幅追加"
        elif deleted > added * 2:
            return "大幅削除"
        else:
            return "更新"
    
    def _format_line_diff(self, added: int, deleted: int) -> str:
        """行数差をフォーマット"""
        if added > 0 and deleted > 0:
            return f"+{added}/-{deleted}"
        elif added > 0:
            return f"+{added}"
        elif deleted > 0:
            return f"-{deleted}"
        else:
            return "変更なし"
    
    def generate_pr_body(self) -> str:
        """PR本文を生成"""
        changed_files = self._get_changed_files()
        
        if not changed_files:
            return "## 変更ファイル\n\n変更されたファイルはありません。\n"
        
        # ヘッダー
        body = f"## 変更ファイル (基準SHA: `{self.base_sha[:8]}`)\n\n"
        
        # テーブルヘッダー
        body += "| ファイルパス | 戦略 | 行数差 | 基準SHA |\n"
        body += "|--------------|------|--------|----------|\n"
        
        # 各ファイルの情報を追加
        for file_path in sorted(changed_files):
            added, deleted = self._get_file_stats(file_path)
            strategy = self._determine_strategy(file_path, added, deleted)
            line_diff = self._format_line_diff(added, deleted)
            
            body += f"| `{file_path}` | {strategy} | {line_diff} | `{self.base_sha[:8]}` |\n"
        
        body += "\n"
        return body
    
    def save_pr_body(self) -> str:
        """PR本文をファイルに保存"""
        self.output_dir.mkdir(exist_ok=True)
        
        pr_body = self.generate_pr_body()
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(pr_body)
        
        return str(self.output_file)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='PR本文生成ツール')
    parser.add_argument(
        '--base-sha',
        help='比較基準となるSHA (省略時は自動検出)'
    )
    parser.add_argument(
        '--output',
        help='出力ファイルパス (省略時はtools/.out/pr_body.md)'
    )
    parser.add_argument(
        '--print',
        action='store_true',
        help='ファイル保存に加えて標準出力にも表示'
    )
    
    args = parser.parse_args()
    
    try:
        generator = PRBodyGenerator(base_sha=args.base_sha)
        
        if args.output:
            generator.output_file = Path(args.output)
            generator.output_dir = generator.output_file.parent
        
        output_path = generator.save_pr_body()
        
        if args.print:
            with open(output_path, 'r', encoding='utf-8') as f:
                print(f.read())
        
        print(f"PR本文を生成しました: {output_path}", file=sys.stderr)
        
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()