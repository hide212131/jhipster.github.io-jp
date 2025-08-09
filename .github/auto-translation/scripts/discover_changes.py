#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム
変更検出スクリプト：translation-meta の upstream_sha を基準に upstream 旧/新を取得し、行オペコードを列挙
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import tempfile
import shutil

# プロジェクトルートに line_diff モジュールを追加
sys.path.insert(0, os.path.dirname(__file__))
from line_diff import LineDiffAnalyzer, LineOperation, analyze_file_diff


def find_project_root() -> Path:
    """プロジェクトルートディレクトリを見つける"""
    current = Path(__file__).parent.parent.parent.parent
    while current != current.parent:
        if (current / '.git').exists() or (current / 'package.json').exists():
            return current
        current = current.parent
    return Path.cwd()


class TranslationMetaManager:
    """Translation metadata管理クラス"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.meta_file = project_root / ".translation-meta.json"
    
    def get_upstream_sha(self) -> Optional[str]:
        """保存されたupstream SHAを取得"""
        if not self.meta_file.exists():
            return None
        
        try:
            with open(self.meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                return meta.get('upstream_sha')
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    
    def set_upstream_sha(self, sha: str) -> None:
        """upstream SHAを保存"""
        meta = {}
        if self.meta_file.exists():
            try:
                with open(self.meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        meta['upstream_sha'] = sha
        
        with open(self.meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)


class UpstreamChangeDiscoverer:
    """Upstream変更検出器"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or find_project_root()
        self.meta_manager = TranslationMetaManager(self.project_root)
        self.upstream_repo = "https://github.com/jhipster/jhipster.github.io.git"
        self.upstream_remote = "upstream"
    
    def setup_upstream_remote(self) -> bool:
        """upstream リモートを設定"""
        try:
            # 既存のupstreamリモートをチェック
            result = subprocess.run(
                ["git", "remote", "get-url", self.upstream_remote],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            if result.returncode == 0:
                # 既に設定されている
                return True
            
            # upstreamリモートを追加
            subprocess.run(
                ["git", "remote", "add", self.upstream_remote, self.upstream_repo],
                check=True, cwd=self.project_root
            )
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error setting up upstream remote: {e}")
            return False
    
    def fetch_upstream(self) -> bool:
        """upstream から最新情報を取得"""
        try:
            if not self.setup_upstream_remote():
                return False
            
            subprocess.run(
                ["git", "fetch", self.upstream_remote],
                check=True, cwd=self.project_root
            )
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error fetching upstream: {e}")
            return False
    
    def get_current_upstream_sha(self) -> Optional[str]:
        """現在のupstream/main SHAを取得"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", f"{self.upstream_remote}/main"],
                capture_output=True, text=True, check=True, cwd=self.project_root
            )
            
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            print(f"Error getting upstream SHA: {e}")
            return None
    
    def get_file_content_at_sha(self, filepath: str, sha: str) -> Optional[str]:
        """指定されたSHAでのファイル内容を取得"""
        try:
            result = subprocess.run(
                ["git", "show", f"{sha}:{filepath}"],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                # ファイルが存在しない場合
                return None
                
        except subprocess.CalledProcessError:
            return None
    
    def get_changed_files_between_shas(self, old_sha: str, new_sha: str) -> List[Tuple[str, str]]:
        """2つのSHA間で変更されたファイルリストを取得"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", f"{old_sha}..{new_sha}"],
                capture_output=True, text=True, check=True, cwd=self.project_root
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
    
    def is_translatable_file(self, filepath: str) -> bool:
        """ファイルが翻訳対象かどうか判定"""
        path = Path(filepath)
        translatable_extensions = {".md", ".mdx", ".adoc", ".html"}
        
        # ルートディレクトリの '.' で始まるファイル・フォルダを除外
        if filepath.startswith('.'):
            return False
        
        # ルート直下のファイルを除外（サブディレクトリ内のファイルのみ翻訳対象）
        if '/' not in filepath:
            return False
        
        return path.suffix.lower() in translatable_extensions
    
    def discover_changes(self, new_sha: str = None) -> Dict[str, Any]:
        """upstream変更を検出して差分情報を生成"""
        if not self.fetch_upstream():
            raise RuntimeError("Failed to fetch upstream changes")
        
        # 現在のupstream SHAを取得
        if new_sha is None:
            new_sha = self.get_current_upstream_sha()
            if not new_sha:
                raise RuntimeError("Could not get current upstream SHA")
        
        # 前回のSHAを取得
        old_sha = self.meta_manager.get_upstream_sha()
        if not old_sha:
            # 初回の場合、現在のSHAを保存して終了
            self.meta_manager.set_upstream_sha(new_sha)
            return {
                "old_sha": None,
                "new_sha": new_sha,
                "is_initial": True,
                "changed_files": [],
                "file_diffs": {}
            }
        
        if old_sha == new_sha:
            return {
                "old_sha": old_sha,
                "new_sha": new_sha,
                "is_initial": False,
                "changed_files": [],
                "file_diffs": {},
                "no_changes": True
            }
        
        # 変更されたファイルを取得
        changed_files = self.get_changed_files_between_shas(old_sha, new_sha)
        
        # 翻訳対象ファイルのみフィルタ
        translatable_files = [
            (status, filepath) for status, filepath in changed_files
            if self.is_translatable_file(filepath)
        ]
        
        # 各ファイルの行レベル差分を分析
        file_diffs = {}
        for status, filepath in translatable_files:
            file_diff_info = self._analyze_file_diff(filepath, old_sha, new_sha, status)
            file_diffs[filepath] = file_diff_info
        
        # メタデータを更新
        self.meta_manager.set_upstream_sha(new_sha)
        
        return {
            "old_sha": old_sha,
            "new_sha": new_sha,
            "is_initial": False,
            "changed_files": translatable_files,
            "file_diffs": file_diffs,
            "summary": self._generate_summary(file_diffs)
        }
    
    def _analyze_file_diff(self, filepath: str, old_sha: str, new_sha: str, status: str) -> Dict[str, Any]:
        """単一ファイルの差分を分析"""
        old_content = ""
        new_content = ""
        
        if status != "A":  # 新規ファイルでない場合
            old_content = self.get_file_content_at_sha(filepath, old_sha) or ""
        
        if status != "D":  # 削除ファイルでない場合
            new_content = self.get_file_content_at_sha(filepath, new_sha) or ""
        
        # 行レベル差分分析
        analyzer = analyze_file_diff(old_content, new_content)
        
        return {
            "status": status,
            "old_content": old_content,
            "new_content": new_content,
            "operations": [self._serialize_operation(op) for op in analyzer.operations],
            "summary": analyzer.get_change_summary(),
            "has_significant_changes": analyzer.has_significant_changes()
        }
    
    def _serialize_operation(self, operation: LineOperation) -> Dict[str, Any]:
        """LineOperationをシリアライズ"""
        return {
            "operation": operation.operation.value,
            "old_start": operation.old_start,
            "old_end": operation.old_end,
            "new_start": operation.new_start,
            "new_end": operation.new_end,
            "old_lines": operation.old_lines,
            "new_lines": operation.new_lines,
            "similarity_ratio": operation.similarity_ratio,
            "is_minor_change": operation.is_minor_change()
        }
    
    def _generate_summary(self, file_diffs: Dict[str, Any]) -> Dict[str, Any]:
        """全体の要約を生成"""
        total_files = len(file_diffs)
        significant_changes = sum(1 for diff in file_diffs.values() if diff["has_significant_changes"])
        minor_changes = total_files - significant_changes
        
        operation_counts = {
            "equal": 0,
            "insert": 0,
            "delete": 0,
            "replace": 0,
            "minor_replace": 0
        }
        
        for diff in file_diffs.values():
            for op in diff["operations"]:
                operation_counts[op["operation"]] += 1
                if op["operation"] == "replace" and op["is_minor_change"]:
                    operation_counts["minor_replace"] += 1
        
        return {
            "total_files": total_files,
            "significant_changes": significant_changes,
            "minor_changes": minor_changes,
            "operation_counts": operation_counts
        }


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Discover upstream changes and analyze line-level diffs")
    parser.add_argument(
        "--new-sha",
        help="Target upstream SHA (defaults to upstream/main)"
    )
    parser.add_argument(
        "--output",
        help="Output file for change analysis (JSON format)"
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Output summary only"
    )
    
    args = parser.parse_args()
    
    try:
        discoverer = UpstreamChangeDiscoverer()
        changes = discoverer.discover_changes(args.new_sha)
        
        if args.summary_only:
            print("🔍 Upstream変更検出結果:")
            print(f"   旧SHA: {changes.get('old_sha', 'N/A')}")
            print(f"   新SHA: {changes['new_sha']}")
            
            if changes.get('is_initial'):
                print("   初回実行：ベースラインを設定しました")
            elif changes.get('no_changes'):
                print("   変更なし")
            else:
                summary = changes['summary']
                print(f"   対象ファイル数: {summary['total_files']}")
                print(f"   重要な変更: {summary['significant_changes']}")
                print(f"   軽微な変更: {summary['minor_changes']}")
        else:
            output_data = json.dumps(changes, indent=2, ensure_ascii=False)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output_data)
                print(f"✅ 変更分析結果を {args.output} に保存しました")
            else:
                print(output_data)
    
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()